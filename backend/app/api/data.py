from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def list_data(current_user: User = Depends(get_current_user)):
    """Endpoint placeholder per dati immatricolazioni."""
    return {"message": "Data endpoint — to be implemented with UNICAB data ingestion"}
