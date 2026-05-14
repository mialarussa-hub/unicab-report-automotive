-- Voci timesheet per il lavoro del 2026-05-14.
-- INSERT eseguiti via psql diretto in prod, questo file resta come
-- traccia storica del testo definitivo in DB.
-- Le 2 voci sono già in produzione:
--   id 7032d330-79be-4610-884e-5ed89c820305 (documentation, 2.0h — sessione PM mattina)
--   id 3bd4d0a7-c803-4ec1-9d86-ba0724677ae2 (meeting, 0.75h — call cliente)

INSERT INTO activities (activity_date, description, hours, category, created_by) VALUES
  (
    '2026-05-14',
    'Project management & documentazione: ricognizione stato progetto, scope modulo campagne adv, materiali per call cliente',
    2.0,
    'documentation',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  ),
  (
    '2026-05-14',
    'Call operativa con il cliente: allineamento sugli avanzamenti recenti (commenti utenti L3, canali YouTube editoriali L2, scheda prestazioni in L1) e condivisione delle decisioni di scope sui prossimi livelli (focus su YouTube e Google Ads, criteri quantitativi nel report commenti, ambito ridotto della raccolta campagne advertising).',
    0.75,
    'meeting',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  )
RETURNING id, activity_date, hours, category, LEFT(description, 60) AS preview;
