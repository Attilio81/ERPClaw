# ERPClaw — Manuale Utente

> Gestisci la tua azienda scrivendo in modo naturale su Telegram, come una chat con un collega.

---

## Cos'è ERPClaw?

ERPClaw è un gestionale aziendale (ERP) che si usa tramite **Telegram**. Non ci sono menu complicati né moduli da compilare: scrivi quello che ti serve, e il sistema risponde.

Puoi anche **mandare messaggi vocali**: ERPClaw li trascrive e risponde come se avessi scritto.

---

## Come iniziare

1. Apri la chat con il bot **ERPClaw** su Telegram.
2. Scrivi `/start` per avviare la sessione.
3. Il bot risponde: *"Ciao! Sono ERPClaw, il tuo gestionale aziendale. Come posso aiutarti?"*

Da quel momento puoi scrivere liberamente in italiano, anche con errori di battitura — il sistema capisce lo stesso.

---

## Cosa puoi fare

### Magazzino e articoli

Controlla le giacenze, aggiungi nuovi articoli e tieni traccia di dove si trovano fisicamente nel magazzino.

**Esempi di richieste:**
- *"abbiamo articoli in magazzino?"*
- *"quanti pezzi abbiamo del cibo per gatti Monge?"*
- *"aggiungi un articolo: codice ART001, Crocchette Premium, prezzo 25 euro"*
- *"dove si trova l'articolo ART001 in magazzino?"*
- *"cosa c'è nel ripiano A-03-2?"*
- *"ci sono articoli senza ubicazione?"*

---

### Ubicazioni di magazzino

ERPClaw gestisce una struttura fisica a quattro livelli: **Magazzino → Zona → Scaffale → Ripiano**.

Puoi creare la struttura del tuo magazzino e caricare gli articoli nelle ubicazioni corrette.

**Esempi di richieste:**
- *"crea il magazzino MAG1 chiamato Principale"*
- *"crea la zona A nel magazzino MAG1"*
- *"crea lo scaffale A-03 nella zona A"*
- *"crea il ripiano A-03-2 nello scaffale A-03"*
- *"mostrami la struttura del magazzino"*
- *"carica 50 pezzi di ART001 nel ripiano A-03-2"*
- *"sposta 10 pezzi di ART001 dal ripiano A-03-2 al ripiano B-01-1"*
- *"mostrami gli ultimi movimenti di magazzino"*

Quando un ordine viene marcato come **spedito**, puoi chiedere lo scarico automatico dalle ubicazioni:
- *"scarica l'ordine ORD-0042 dal magazzino"*

ERPClaw preleva le quantità partendo dalle ubicazioni con più stock (strategia LIFO) e aggiorna automaticamente le giacenze.

---

### Fornitori

Cerca nuovi fornitori sul web, salvali nel sistema e gestisci i loro cataloghi.

**Esempi dalla chat reale:**

> 🐻 *"mi cerchi il fornitore monge? ha dei cataloghi?"*

ERPClaw cerca online, trova le informazioni su Monge & C. S.p.A. (sede, fatturato, sito web) e segnala che il catalogo PDF è disponibile. Poi chiede:

> E *"Vuoi salvare questo fornitore nel database ERP?"*

> 🐻 *"Si salvami questo nuovo fornitore"*

> E *"Fornitore salvato con successo nel database."* — con riepilogo dei dati inseriti.

**Altre richieste possibili:**
- *"mostrami la lista dei fornitori"*
- *"cerca fornitori di alimenti per cani"*

---

### Cataloghi fornitori

Puoi chiedere a ERPClaw di scaricare i cataloghi PDF dei fornitori e importare automaticamente gli articoli.

**Esempio dalla chat reale:**

> 🐻 *"Si scarica il catalogo e inserisci i primi 10 articoli"*

ERPClaw scarica il catalogo di Monge, identifica 10 articoli con i loro codici ufficiali, e nota che i prezzi non sono nel documento. Propone soluzioni alternative:

> E *"Vuoi che proceda con l'inserimento con prezzi temporanei, oppure aspettiamo il listino ufficiale?"*

> 🐻 *"Riesci a recuperare i prezzi di articoli simili sul web?"*

ERPClaw cerca i prezzi su e-commerce italiani (Trovaprezzi, Idealo, ecc.) e presenta una tabella con i prezzi trovati e la fonte. Poi offre opzioni:

> E *"Vuoi inserire con questi prezzi, aggiungere un margine del 20%, o arrotondare?"*

> 🐻 *"procedi con opzione 2"*

ERPClaw calcola i prezzi con il +20% e inserisce tutti e 10 gli articoli nel catalogo, mostrando un riepilogo finale con prezzi originali, margine applicato e prezzo finale.

---

### Clienti

Crea e gestisci la tua anagrafica clienti, compresi gli indirizzi (sede legale, spedizione, fatturazione).

**Esempi di richieste:**
- *"aggiungi cliente: codice C001, Mario Rossi Srl"*
- *"aggiungi l'indirizzo di spedizione del cliente C001: Via Roma 1, 20100 Milano MI"*
- *"mostrami gli indirizzi del cliente C001"*
- *"mostrami la lista clienti"*
- *"cerca il cliente Bianchi"*

---

### Ordini

Crea ordini di vendita, aggiorna il loro stato e tieni traccia dello storico.

Gli ordini seguono questo percorso: **Bozza → Confermato → Spedito → Chiuso**

Quando un ordine viene marcato come **spedito**, il sistema può scaricare automaticamente le quantità dalle ubicazioni di magazzino e mostrare l'indirizzo di spedizione del cliente.

**Esempi di richieste:**
- *"crea un ordine per il cliente Rossi: 2 pezzi di MONGE CAT ADULT POLLO 10KG"*
- *"conferma l'ordine numero 5"*
- *"segna l'ordine ORD-0042 come spedito"*
- *"scarica l'ordine ORD-0042 dal magazzino"*
- *"mostrami gli ordini aperti"*
- *"quali ordini ho in bozza?"*

---

## Consigli pratici

**Scrivi in modo naturale** — non devi usare comandi speciali. ERPClaw capisce il linguaggio di tutti i giorni.

**Puoi usare la voce** — se sei in giro o hai le mani occupate, manda un messaggio vocale. Il sistema lo trascrive automaticamente.

**ERPClaw ti guida** — se mancano informazioni per completare un'operazione, il bot ti chiede quello che serve, passo per passo.

**Puoi correggere o cambiare idea** — nella stessa conversazione puoi scrivere *"aspetta, cambia il prezzo a 30 euro"* oppure *"annulla, non inserire quell'articolo"*.

**Il bot ricorda il contesto** — all'interno della sessione, ERPClaw sa di cosa avete parlato. Puoi fare riferimento a cose dette prima senza ripetere tutto.

---

## Pannello web (per chi lo usa)

Esiste anche un pannello di amministrazione accessibile da browser all'indirizzo **http://localhost:8000/admin** per chi preferisce una vista tabellare dei dati (articoli, clienti, ordini, fornitori). Si può usare in parallelo con Telegram, senza interferenze.

---

## Domande frequenti

**Posso fare errori di battitura?**
Sì, ERPClaw li tollera bene. Nella chat di esempio, messaggi come *"muovo fornitore"* (invece di "nuovo") o *"recupwrare"* (invece di "recuperare") sono stati compresi correttamente.

**Cosa succede se il sistema non capisce?**
ERPClaw chiede chiarimenti o propone alternative. Non eseguirà mai un'operazione se non è sicuro di cosa vuoi fare.

**I dati sono al sicuro?**
Tutti i dati sono salvati localmente nel database aziendale. Nulla viene condiviso con servizi esterni, eccetto le ricerche web esplicite sui fornitori (solo quando le richiedi tu).

**Posso usarlo da smartphone?**
Sì, Telegram funziona su tutti i dispositivi. ERPClaw è pensato per essere usato comodamente anche dal telefono.
