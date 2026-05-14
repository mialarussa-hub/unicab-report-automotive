-- Voce timesheet per il lavoro del 2026-05-14.
-- INSERT eseguito via psql diretto in prod, questo file resta come
-- traccia storica del testo definitivo in DB.
-- La voce è già in produzione:
--   id 7032d330-79be-4610-884e-5ed89c820305 (documentation, 2.0h — sessione PM mattina)

INSERT INTO activities (activity_date, description, hours, category, created_by) VALUES
  (
    '2026-05-14',
    'Project management & documentazione: ricognizione stato progetto, scope modulo campagne adv, materiali per call cliente',
    2.0,
    'documentation',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  )
RETURNING id, activity_date, hours, category, LEFT(description, 60) AS preview;
