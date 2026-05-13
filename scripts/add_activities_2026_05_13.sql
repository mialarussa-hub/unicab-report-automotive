-- Voci timesheet per il lavoro del 2026-05-13.
-- INSERT eseguito via psql diretto in prod, questo file resta come
-- traccia storica del testo definitivo in DB.
-- ID generati al momento dell'INSERT (vedi commit successivo per riempire).

INSERT INTO activities (activity_date, description, hours, category, created_by) VALUES
  (
    '2026-05-13',
    'Introdotto un flusso alternativo di raccolta media e giornalisti che attinge ai soli canali YouTube editoriali (Quattroruote, AlVolante, Motor1 Italia, DriveK), in parallelo al flusso standard. La sintesi del report si adatta automaticamente alle fonti analizzate. Selezionabile dall''interfaccia con etichetta dedicata. Rilascio in produzione e verifica.',
    2.5,
    'development',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  ),
  (
    '2026-05-13',
    'Arricchita la scheda di comunicazione ufficiale: quando il brand parla di prestazioni e piacere di guida, la card relativa mostra ora i numeri-chiave estratti dal sito ufficiale (cavalli, coppia, accelerazione, velocità massima, peso, autonomia di ricarica, rapporto peso/potenza) come riprova alle citazioni. Rilascio in produzione e verifica.',
    1.5,
    'development',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  ),
  (
    '2026-05-13',
    'Risolta un''anomalia emersa dal confronto fra due raccolte sullo stesso modello: la sintesi del report scartava parte del pacchetto quando ampio, restituendo punti di debolezza incompleti. Aumentata la soglia di elaborazione e introdotta tracciatura della dimensione del pacchetto. Rilascio in produzione e verifica.',
    1.0,
    'development',
    '46696f65-ee1f-47bd-96cd-b914ef9b2996'
  )
RETURNING id, activity_date, hours, category, LEFT(description, 60) AS preview;
