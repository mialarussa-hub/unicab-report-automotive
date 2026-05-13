"""Scraping test endpoint — async scraping with per-source progress tracking."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token
from app.database import get_db, async_session
from app.models.source import Source
from app.models.user import User
from app.models.scraping import ScrapingSession, ScrapingResult

router = APIRouter()
logger = logging.getLogger(__name__)

SCRAPERS_URL = "http://scrapers:8001"

# Registry of running scrape tasks, keyed by session_id. Populated in /run,
# cleaned up on task completion or cancellation.
_active_tasks: dict[str, asyncio.Task] = {}


class ScrapeTestRequest(BaseModel):
    brand: str
    model: str = ""
    phase: str = "all"  # all, L1, L2, L2YT, L3
    alimentazione: str | None = None  # canonical enum or None
    cilindrata: float | None = None   # liters (e.g. 1.0, 1.5) or None


# Phase → source_type mapping (mirror of frontend LEVELS)
# youtube_editorial = canale YouTube ufficiale di una testata (Quattroruote,
# AlVolante, Motor1...) → contenuto editoriale (trascrizioni Whisper) = L2.
# youtube generico = ricerca cross-canale → user-generated (commenti) = L3.
PHASE_SOURCE_TYPES = {
    "L1": {"official"},
    "L2": {"news", "perplexity", "youtube_editorial"},
    # L2YT = variante L2 con solo i canali YouTube editoriali (sottoinsieme di
    # L2, flusso parallelo permanente — decisione Ale 2026-05-13).
    "L2YT": {"youtube_editorial"},
    "L3": {"forum", "youtube", "social"},
}

# Cascade thresholds — minimum matches per phase before degrading the filter
PHASE_MIN_MATCHES = {"L1": 1, "L2": 2, "L2YT": 1, "L3": 10}

ALIMENTAZIONE_CANONICA = {
    "benzina", "diesel", "gpl", "metano", "elettrico",
    "ibrido_full", "ibrido_mild", "ibrido_plugin",
}


def _source_type_to_phase(source_type: str | None) -> str:
    if not source_type:
        return "L3"
    for p, types in PHASE_SOURCE_TYPES.items():
        if source_type in types:
            return p
    return "L3"


def _motori_match(motore_info, want_alim, want_cil):
    """Return True if motore_info matches the (alim, cilindrata) filter."""
    if not want_alim and want_cil is None:
        return True
    if not motore_info:
        return False
    # Caso "articolo generale sul modello": l'AI ha analizzato la pagina ma non
    # ha individuato versioni specifiche (versioni=[]). L'articolo parla del
    # modello in generale (es. confronto, news brand, premio, lancio globale)
    # e resta pertinente a qualunque filtro motore — si applica solo agli
    # articoli che dichiarano esplicitamente versioni mismatch col filtro.
    if isinstance(motore_info, dict):
        versioni = motore_info.get("versioni")
        if isinstance(versioni, list) and not versioni:
            return True
    candidates = []
    if isinstance(motore_info, dict):
        versioni = motore_info.get("versioni")
        if isinstance(versioni, list) and versioni:
            candidates = versioni
        else:
            candidates = [motore_info]
    for m in candidates:
        if not isinstance(m, dict):
            continue
        m_alim = m.get("alimentazione")
        m_cil = m.get("cilindrata")
        try:
            m_cil = float(m_cil) if m_cil is not None else None
        except (TypeError, ValueError):
            m_cil = None
        if want_alim and m_alim != want_alim:
            continue
        # Cilindrata: applichiamo il filtro hard solo quando l'AI l'ha estratta.
        # Se m_cil è None (estrazione mancante) non penalizziamo l'item: la sola
        # alimentazione conferma la pertinenza. Senza questa tolleranza, articoli
        # tipo "Fiat Grande Panda benzina" (cil=null estratta da prosa libera)
        # venivano marcati non pertinenti contro filtro (benzina, 1.2).
        if want_cil is not None and m_cil is not None and abs(m_cil - want_cil) > 0.05:
            continue
        return True
    return False


def _item_matches(r, want_alim, want_cil):
    """An L1/L2/L3-thread-level item matches if its motore_info has a matching versione.

    Special case for L1 (source_type='official'): the driver analysis runs at
    MODEL level, not at version level — the alim/cil filter there is semantically
    off-scope. We consider L1 official items always matching so the cascade does
    not hide pages the driver analysis has already consumed.
    """
    if not want_alim and want_cil is None:
        return True
    if r.source_type == "official":
        return True
    return _motori_match(r.motore_info, want_alim, want_cil)


def _comment_matches(c: dict, want_alim, want_cil) -> bool:
    """A single comment matches if its motore_menzionato matches (or no filter)."""
    if not want_alim and want_cil is None:
        return True
    mm = c.get("motore_menzionato")
    return _motori_match(mm, want_alim, want_cil)


class SourceCompleteRequest(BaseModel):
    session_id: str
    source_result: dict


async def get_user_from_cookie(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via cookie (frontend pages use httponly cookies)."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def get_admin_from_cookie(
    user: User = Depends(get_user_from_cookie),
) -> User:
    """Enforce admin role on top of cookie auth. Used to lock internal endpoints
    (scraping, sources management, timesheet) away from client-role users like
    the UNICAB team (Paolo) who should only see reports.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def _compute_effective_filter(db: AsyncSession, session: ScrapingSession) -> dict:
    """Apply filter cascade per-phase on session results.

    Cascade order: (alim + cilindrata) → (alim only) → (no filter)
    For each phase, picks the most specific filter meeting PHASE_MIN_MATCHES threshold.
    Returns dict {per_phase: {L1: {...}, L2: {...}, L3: {...}}, requested: {...}}.
    """
    req_alim = session.filter_alimentazione
    req_cil = float(session.filter_cilindrata) if session.filter_cilindrata is not None else None
    requested = {"alimentazione": req_alim, "cilindrata": req_cil}

    effective_per_phase: dict[str, dict] = {}
    if not req_alim and req_cil is None:
        return {"requested": requested, "per_phase": {}}

    # Load all results grouped by phase
    res = await db.execute(
        select(ScrapingResult).where(ScrapingResult.session_id == session.id)
    )
    results = res.scalars().all()

    phase_items: dict[str, list] = {"L1": [], "L2": [], "L3": []}
    for r in results:
        phase_items[_source_type_to_phase(r.source_type)].append(r)

    # Candidate filter levels in cascade order (most → least specific)
    candidates = []
    if req_alim and req_cil is not None:
        candidates.append(("alim_cil", req_alim, req_cil))
    if req_alim:
        candidates.append(("alim_only", req_alim, None))
    candidates.append(("none", None, None))

    for phase, items in phase_items.items():
        if not items:
            effective_per_phase[phase] = {
                "alimentazione": None, "cilindrata": None,
                "matches": 0, "degraded": False, "reason": "no_items",
            }
            continue

        threshold = PHASE_MIN_MATCHES.get(phase, 1)

        chosen = None
        for level, a, c in candidates:
            # For L3, count matching comments; for L1/L2, count matching items
            if phase == "L3":
                count = 0
                for r in items:
                    for cmt in (r.ai_comments or []):
                        if _comment_matches(cmt, a, c):
                            count += 1
            else:
                count = sum(1 for r in items if _item_matches(r, a, c))

            if count >= threshold or level == "none":
                degraded = level != candidates[0][0]
                chosen = {
                    "alimentazione": a,
                    "cilindrata": c,
                    "matches": count,
                    "degraded": degraded,
                    "reason": level,
                }
                break

        effective_per_phase[phase] = chosen

    return {"requested": requested, "per_phase": effective_per_phase}


@router.post("/run")
async def run_scraping_test(
    request: ScrapeTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    """Launch scraping asynchronously — returns immediately with session_id.

    The frontend polls GET /sessions/{id} to track progress in real time.
    """
    # Validate phase
    phase = request.phase if request.phase in ("all", "L1", "L2", "L2YT", "L3") else "all"

    # Validate motore filter
    alim = request.alimentazione if request.alimentazione in ALIMENTAZIONE_CANONICA else None
    cil = request.cilindrata
    if cil is not None:
        try:
            cil = round(float(cil), 1)
            if cil < 0.5 or cil > 8.5:
                cil = None
        except (TypeError, ValueError):
            cil = None

    # Fetch active sources from DB, filtered by phase
    query = select(Source).where(Source.is_active == True)
    if phase != "all":
        allowed_types = PHASE_SOURCE_TYPES[phase]
        query = query.where(Source.source_type.in_(allowed_types))
    result = await db.execute(query)
    sources = result.scalars().all()

    sources_list = [
        {"name": s.name, "url": s.url, "source_type": s.source_type}
        for s in sources
    ]

    if not sources_list:
        raise HTTPException(
            status_code=400,
            detail=f"Nessuna fonte attiva per la fase '{phase}'",
        )

    # Create session
    session = ScrapingSession(
        brand=request.brand,
        model=request.model or None,
        status="running",
        total_sources=len(sources_list),
        phase_filter=phase,
        filter_alimentazione=alim,
        filter_cilindrata=cil,
        created_by=current_user.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Launch scraping in background — returns immediately
    session_id_str = str(session.id)
    task = asyncio.create_task(
        _run_scraping_background(
            session_id_str, request.brand, request.model, sources_list,
            alim, float(cil) if cil is not None else None,
        )
    )
    _active_tasks[session_id_str] = task
    task.add_done_callback(lambda _: _active_tasks.pop(session_id_str, None))

    return {
        "session_id": str(session.id),
        "status": "running",
        "total_sources": len(sources_list),
        "sources_names": [s["name"] for s in sources_list],
        "phase_filter": phase,
        "filter_alimentazione": alim,
        "filter_cilindrata": float(cil) if cil is not None else None,
    }


async def _run_scraping_background(
    session_id: str, brand: str, model: str, sources_list: list[dict],
    alimentazione: str | None = None, cilindrata: float | None = None,
):
    """Background task: call scrapers service, finalize session on completion."""
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(
                f"{SCRAPERS_URL}/scrape/test",
                json={
                    "brand": brand,
                    "model": model,
                    "alimentazione": alimentazione,
                    "cilindrata": cilindrata,
                    "sources": sources_list,
                    "session_id": session_id,
                    "callback_url": "http://api:8000/scraping-test/source-complete",
                },
            )
            data = resp.json()

        # Finalize session — update totals from any sources not already saved via callback
        async with async_session() as db:
            result = await db.execute(
                select(ScrapingSession).where(ScrapingSession.id == uuid.UUID(session_id))
            )
            session = result.scalar_one_or_none()
            if not session:
                return

            # Check which sources were already saved via callback
            existing = await db.execute(
                select(ScrapingResult.source_name)
                .where(ScrapingResult.session_id == uuid.UUID(session_id))
            )
            saved_sources = {r[0] for r in existing.fetchall()}

            total_results = 0
            total_comments = 0

            for source_data in data.get("sources", []):
                source_name = source_data.get("source", "")

                # Skip if already saved via callback
                if source_name in saved_sources:
                    # Count existing results
                    for item in source_data.get("items", []):
                        total_results += 1
                        total_comments += item.get("ai_comment_count", 0) or (
                            len(item.get("ai_comments") or [])
                        )
                    continue

                # Save results not yet saved
                for item in source_data.get("items", []):
                    ai_comments = item.get("ai_comments")
                    comment_count = item.get("ai_comment_count", 0)
                    if not comment_count and ai_comments:
                        comment_count = len(ai_comments)

                    # motore_info: for L1 take from official_info.motore_info, else from summary pipeline
                    motore_info = item.get("motore_info")
                    official_info = item.get("ai_official_info")
                    if motore_info is None and isinstance(official_info, dict):
                        motore_info = official_info.get("motore_info")

                    scraping_result = ScrapingResult(
                        session_id=uuid.UUID(session_id),
                        source_name=source_name,
                        source_type=source_data.get("source_type", ""),
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        summary=item.get("summary"),
                        content=item.get("content", "")[:10000],
                        ai_comments=ai_comments,
                        comment_count=comment_count,
                        view_count=item.get("view_count"),
                        like_count=item.get("like_count"),
                        channel=item.get("channel"),
                        official_info=official_info,
                        motore_info=motore_info,
                    )
                    db.add(scraping_result)
                    total_results += 1
                    total_comments += comment_count

            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            session.total_results = total_results
            session.total_comments = total_comments
            session.total_credits = data.get("total_credits", 0)
            session.duration_ms = data.get("total_duration_ms", 0)

            # L2 minireport (sintesi narrativa media/giornalisti) — opzionale,
            # presente solo se la sessione ha incluso fonti L2 con almeno un item.
            l2_synth = data.get("l2_synthesis")
            if isinstance(l2_synth, dict):
                session.l2_synthesis = l2_synth

            # L3 minireport (sintesi voce utenti) — opzionale, presente solo se
            # ci sono almeno 10 commenti aggregati su fonti L3 (forum/yt user/
            # reddit/social) + cross-import dei commenti dei video editoriali L2.
            l3_synth = data.get("l3_synthesis")
            if isinstance(l3_synth, dict):
                session.l3_synthesis = l3_synth

            # Per-source diagnostic summary (rebuilt at finalize regardless of
            # callback success — the callback is best-effort for real-time UI).
            session.source_runs = [
                {
                    "source": sd.get("source", ""),
                    "source_type": sd.get("source_type", ""),
                    "status": sd.get("status", "ok"),
                    "result_count": len(sd.get("items", []) or []),
                    "credits_used": int(sd.get("credits_used") or 0),
                    "duration_ms": int(sd.get("duration_ms") or 0),
                    "error": sd.get("error"),
                }
                for sd in (data.get("sources") or [])
            ]

            # Cascade filter per-phase
            session.filter_effective = await _compute_effective_filter(db, session)

            await db.commit()
            logger.info(f"Session {session_id} completed: {total_results} results")

    except asyncio.CancelledError:
        logger.warning(f"Session {session_id} scraping task cancelled")
        # Status already set to 'cancelled' by the /cancel endpoint; nothing else to do
        raise
    except Exception as e:
        logger.error(f"Background scraping error for session {session_id}: {e}")
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(ScrapingSession).where(ScrapingSession.id == uuid.UUID(session_id))
                )
                session = result.scalar_one_or_none()
                # Don't overwrite 'cancelled' status
                if session and session.status == "running":
                    session.status = "failed"
                    session.completed_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception:
            pass


@router.post("/sessions/{session_id}/cancel")
async def cancel_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    """Cancel a running scrape: mark session 'cancelled' + cancel the async task.

    Any in-flight external API calls (Firecrawl, Perplexity, Claude) already
    dispatched before cancel will complete server-side, but their results will
    NOT be persisted: the source-complete callback checks session status and
    skips saves for non-running sessions.
    """
    result = await db.execute(
        select(ScrapingSession).where(
            ScrapingSession.id == uuid.UUID(session_id),
            ScrapingSession.created_by == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "running":
        return {"ok": True, "already_terminal": True, "status": session.status}

    # Mark cancelled in DB first (so the callback-skip logic takes effect immediately)
    session.status = "cancelled"
    session.completed_at = datetime.now(timezone.utc)
    await db.commit()

    # Cancel the asyncio task in-flight (if any)
    task = _active_tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()

    logger.warning(f"Session {session_id} cancelled by user {current_user.email}")
    return {"ok": True, "cancelled": True}


@router.post("/source-complete")
async def source_complete(
    request: SourceCompleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Callback from scrapers service — saves one source's results incrementally.

    Called by the scrapers container each time a source finishes scraping.
    This allows the frontend to see results as they arrive via polling.
    """
    session_id = request.session_id
    source_data = request.source_result

    # Verify session exists
    result = await db.execute(
        select(ScrapingSession).where(ScrapingSession.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Skip save if session was cancelled or already terminated — avoids writing
    # results into a session the user explicitly stopped.
    if session.status != "running":
        logger.info(f"Skipping callback for session {session_id}: status={session.status}")
        return {"ok": True, "skipped": True, "reason": f"session status: {session.status}"}

    source_name = source_data.get("source", "")
    source_type = source_data.get("source_type", "")
    items = source_data.get("items", [])

    # Append per-source diagnostic summary (visible in UI even when items is empty).
    # Done before result inserts so partial/error sources are tracked too.
    run_summary = {
        "source": source_name,
        "source_type": source_type,
        "status": source_data.get("status", "ok"),
        "result_count": len(items),
        "credits_used": int(source_data.get("credits_used") or 0),
        "duration_ms": int(source_data.get("duration_ms") or 0),
        "error": source_data.get("error"),
    }
    runs = list(session.source_runs or [])
    runs.append(run_summary)
    session.source_runs = runs

    saved_count = 0
    saved_comments = 0

    for item in items:
        ai_comments = item.get("ai_comments")
        comment_count = item.get("ai_comment_count", 0)
        if not comment_count and ai_comments:
            comment_count = len(ai_comments)

        motore_info = item.get("motore_info")
        official_info = item.get("ai_official_info")
        if motore_info is None and isinstance(official_info, dict):
            motore_info = official_info.get("motore_info")

        scraping_result = ScrapingResult(
            session_id=uuid.UUID(session_id),
            source_name=source_name,
            source_type=source_type,
            url=item.get("url", ""),
            title=item.get("title", ""),
            summary=item.get("summary"),
            content=item.get("content", "")[:10000],
            ai_comments=ai_comments,
            comment_count=comment_count,
            view_count=item.get("view_count"),
            like_count=item.get("like_count"),
            channel=item.get("channel"),
            official_info=official_info,
            motore_info=motore_info,
        )
        db.add(scraping_result)
        saved_count += 1
        saved_comments += comment_count

    # Update session running totals
    session.total_results = (session.total_results or 0) + saved_count
    session.total_comments = (session.total_comments or 0) + saved_comments

    await db.commit()
    logger.info(f"[{source_name}] Saved {saved_count} results for session {session_id}")

    return {"ok": True, "saved": saved_count}


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    """List all scraping sessions for the current user."""
    result = await db.execute(
        select(ScrapingSession)
        .where(ScrapingSession.created_by == current_user.id)
        .order_by(desc(ScrapingSession.started_at))
        .limit(50)
    )
    sessions = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "brand": s.brand,
            "model": s.model,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "status": s.status,
            "total_sources": s.total_sources,
            "total_results": s.total_results,
            "total_comments": s.total_comments,
            "total_credits": s.total_credits,
            "duration_ms": s.duration_ms,
            "phase_filter": s.phase_filter,
            "filter_alimentazione": s.filter_alimentazione,
            "filter_cilindrata": float(s.filter_cilindrata) if s.filter_cilindrata is not None else None,
            "filter_effective": s.filter_effective,
            "is_featured": bool(s.is_featured),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_from_cookie),
):
    """Get session details with all results, formatted like scraper response.

    Access rules:
    - Admin can view any session they created.
    - Client users (is_admin=False) can only view sessions flagged is_featured=True.
      This lets Paolo & co. open the detail from the 'Anteprime' dashboard tab
      without gaining access to the full admin test-scraping archive.
    """
    result = await db.execute(
        select(ScrapingSession)
        .options(selectinload(ScrapingSession.results))
        .where(ScrapingSession.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.is_admin:
        if session.created_by != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        if not session.is_featured:
            raise HTTPException(status_code=403, detail="Session not available for preview")

    # Resolve effective filter per phase (for tagging match flags)
    effective = session.filter_effective or {}
    per_phase = (effective.get("per_phase") or {}) if isinstance(effective, dict) else {}

    # Group results by source
    sources_map: dict[str, dict] = {}
    for r in session.results:
        key = r.source_name
        if key not in sources_map:
            sources_map[key] = {
                "source": r.source_name,
                "source_type": r.source_type,
                "status": "ok",
                "result_count": 0,
                "credits_used": 0,
                "items": [],
                "duration_ms": 0,
            }
        sources_map[key]["result_count"] += 1

        phase = _source_type_to_phase(r.source_type)
        ph = per_phase.get(phase) or {}
        eff_alim = ph.get("alimentazione")
        eff_cil = ph.get("cilindrata")

        # Tag per-comment match flag
        tagged_comments = None
        if r.ai_comments:
            tagged_comments = []
            for cmt in r.ai_comments:
                c = dict(cmt) if isinstance(cmt, dict) else {"text": str(cmt)}
                c["matches_filter"] = _comment_matches(c, eff_alim, eff_cil)
                tagged_comments.append(c)

        item_matches = _item_matches(r, eff_alim, eff_cil)
        # For L3, an item is considered matching if any of its comments match
        if phase == "L3" and tagged_comments:
            item_matches = item_matches or any(c.get("matches_filter") for c in tagged_comments)

        # Detect Perplexity lightweight citation: L1 item with NO Claude extraction
        # AND a very short content (the Perplexity citation snippet, ~200-400 chars).
        # Firecrawl-scraped pages also have no official_info (driver analysis is
        # attached only to the consolidated item), but their content is 5k-10k chars
        # of actual brand copy — those must NOT be rendered as tiny citation cards.
        content_len = len(r.content or "")
        is_citation = (
            r.source_type == "official"
            and r.official_info is None
            and content_len < 500
        )

        item = {
            "url": r.url,
            "title": r.title,
            "summary": r.summary,
            "content": r.content,
            "ai_comments": tagged_comments,
            "ai_comment_count": r.comment_count,
            "content_length": len(r.content) if r.content else 0,
            "scraped": not is_citation,
            "motore_info": r.motore_info,
            "matches_filter": item_matches,
            "perplexity_citation": is_citation,
        }
        if r.view_count is not None:
            item["view_count"] = r.view_count
            item["like_count"] = r.like_count
            item["channel"] = r.channel
        if r.official_info is not None:
            item["ai_official_info"] = r.official_info

        sources_map[key]["items"].append(item)

    # Merge per-source diagnostic runs: sources interrogate ma senza risultati
    # (status=partial/error) non hanno entry in sources_map. Le aggiungiamo qui
    # per renderle visibili in UI con il loro stato, motivo e crediti spesi.
    for run in (session.source_runs or []):
        if not isinstance(run, dict):
            continue
        key = run.get("source") or ""
        if not key:
            continue
        if key in sources_map:
            # Arricchiamo la entry esistente con metadati che la lista results non ha.
            entry = sources_map[key]
            entry["status"] = run.get("status") or entry.get("status") or "ok"
            entry["credits_used"] = int(run.get("credits_used") or entry.get("credits_used") or 0)
            entry["duration_ms"] = int(run.get("duration_ms") or entry.get("duration_ms") or 0)
            if run.get("error"):
                entry["error"] = run["error"]
        else:
            # Fonte interrogata ma senza items: la mostriamo comunque con stato.
            sources_map[key] = {
                "source": key,
                "source_type": run.get("source_type") or "news",
                "status": run.get("status") or "partial",
                "result_count": int(run.get("result_count") or 0),
                "credits_used": int(run.get("credits_used") or 0),
                "duration_ms": int(run.get("duration_ms") or 0),
                "error": run.get("error"),
                "items": [],
            }

    return {
        "session_id": str(session.id),
        "brand": session.brand,
        "model": session.model,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "status": session.status,
        "phase_filter": session.phase_filter,
        "filter_alimentazione": session.filter_alimentazione,
        "filter_cilindrata": float(session.filter_cilindrata) if session.filter_cilindrata is not None else None,
        "filter_effective": session.filter_effective,
        "is_featured": bool(session.is_featured),
        "sources": list(sources_map.values()),
        "l2_synthesis": session.l2_synthesis,
        "l3_synthesis": session.l3_synthesis,
        "total_credits": session.total_credits,
        "total_duration_ms": session.duration_ms,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    """Delete a scraping session and all its results."""
    result = await db.execute(
        select(ScrapingSession).where(
            ScrapingSession.id == uuid.UUID(session_id),
            ScrapingSession.created_by == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return {"ok": True}


@router.patch("/sessions/{session_id}/flag")
async def toggle_session_flag(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    """Toggle the 'featured for dashboard preview' flag on a session. Admin only.

    Featured sessions show up in the /frontend/anteprime tab visible to all
    authenticated users (including client-role like Paolo).
    """
    result = await db.execute(
        select(ScrapingSession).where(
            ScrapingSession.id == uuid.UUID(session_id),
            ScrapingSession.created_by == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_featured = not session.is_featured
    await db.commit()
    return {"ok": True, "is_featured": session.is_featured}


@router.get("/featured")
async def list_featured_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_from_cookie),
):
    """List all sessions flagged as 'featured' — accessible to admin AND client.

    Read-only: client users (e.g. Paolo) view the same summaries admins see on
    /scraping-test but limited to the sessions the admin has explicitly flagged.
    """
    result = await db.execute(
        select(ScrapingSession)
        .where(ScrapingSession.is_featured == True)  # noqa: E712
        .order_by(desc(ScrapingSession.started_at))
    )
    sessions = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "brand": s.brand,
            "model": s.model,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "status": s.status,
            "total_sources": s.total_sources,
            "total_results": s.total_results,
            "total_comments": s.total_comments,
            "duration_ms": s.duration_ms,
            "phase_filter": s.phase_filter,
            "filter_alimentazione": s.filter_alimentazione,
            "filter_cilindrata": float(s.filter_cilindrata) if s.filter_cilindrata is not None else None,
            "is_featured": True,
        }
        for s in sessions
    ]
