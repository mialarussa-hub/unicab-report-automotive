-- Voci timesheet per il lavoro del 2026-05-12.
-- INSERT eseguito via psql diretto in prod, questo file resta come
-- traccia storica del testo definitivo in DB.
-- Le 2 voci sono già in produzione:
--   id 6c102a7b-3c51-476e-9fbb-2c13df42ae4a (development, 4.5h)
--   id 325c6bc1-d655-4465-9f61-06fcb94f87a8 (documentation, 0.5h)

INSERT INTO activities (activity_date, description, hours, category, created_by) VALUES
  (
    '2026-05-12',
    'Completamento del Livello 3 commenti utente: implementato il modello di sintesi voce utenti che aggrega i commenti raccolti su forum, video YouTube e community online, con riuso dei commenti dei video editoriali del Livello 2 e deduplica per evitare doppi conteggi. Aggiunto un filtro semantico sul modello target per evitare contaminazioni da altre versioni omonime. Nuova card in interfaccia, rilascio in produzione e verifica con un modello di test.',
    4.5,
    'development',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  ),
  (
    '2026-05-12',
    'Aggiornamento del manuale operativo di rilascio in produzione con i passaggi necessari per i container con codice incluso nell''immagine e per il riallineamento del reverse proxy dopo la ricreazione dei container.',
    0.5,
    'documentation',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  )
RETURNING id, activity_date, hours, category, LEFT(description, 60) AS preview;
