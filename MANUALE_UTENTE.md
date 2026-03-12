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

### Categorie articoli

Puoi organizzare il catalogo raggruppando gli articoli in categorie. Le categorie vengono create e assegnate dall'agente direttamente dalla chat.

**Creare una categoria:**
- *"crea la categoria Alimenti Secchi"*
- *"aggiungi la categoria Crocchette Gatto"*

**Assegnare una categoria a un articolo:**
- *"assegna la categoria Alimenti Secchi all'articolo ART001"*
- *"metti l'articolo MONGE CAT nella categoria Crocchette Gatto"*

**Vedere le categorie esistenti:**
- *"mostrami le categorie"*
- *"quali categorie abbiamo?"*

Una volta assegnata, la categoria appare nel dettaglio dell'articolo e nei risultati di ricerca.

---

### Scorta minima e alert di riordino

Puoi impostare una soglia di scorta minima per ogni articolo. Quando la giacenza scende sotto quella soglia, il sistema segnala che è il momento di riordinare.

**Impostare la scorta minima:**
- *"imposta la scorta minima di ART001 a 10 pezzi"*
- *"la scorta minima del Monge Adult Pollo deve essere 20"*

**Verificare gli articoli da riordinare:**
- *"quali articoli sono sotto scorta minima?"*
- *"dimmi cosa devo riordinare"*
- *"articoli da riordinare"*

ERPClaw risponde con l'elenco degli articoli la cui giacenza attuale è inferiore alla soglia impostata, indicando giacenza attuale e scorta minima per ciascuno.

**Consiglio:** usa questo controllo periodicamente (ad esempio ogni settimana) per non rimanere mai a corto di prodotti importanti.

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

### Ordini fornitori

Puoi creare ordini di acquisto verso i fornitori, aggiungere gli articoli e seguire il percorso fino al ricevimento della merce.

Gli ordini fornitori seguono questo percorso: **Bozza → Inviato → Ricevuto**

**Esempi di richieste:**
- *"crea un ordine fornitore per FOR01"*
- *"aggiungi 10 pezzi di ART001 all'ordine ORF-0001"*
- *"aggiungi 5 pezzi di ART002 all'ordine ORF-0001 a 4,50 euro"*
- *"mostrami l'ordine fornitore ORF-0001"*
- *"lista ordini fornitori in bozza"*
- *"segna l'ordine ORF-0001 come inviato"*
- *"l'ordine ORF-0001 è arrivato, segnalo come ricevuto"*

Quando aggiungi una riga senza specificare il prezzo, ERPClaw usa automaticamente il **prezzo di acquisto** impostato sull'articolo. Se l'articolo non ha un prezzo di acquisto, dovrai specificarlo esplicitamente.

Quando l'ordine passa in stato **Ricevuto**, ricordati di caricare la merce nelle ubicazioni di magazzino con i tool logistici.

---

### Prezzi articoli

Ogni articolo ha ora due prezzi distinti:

- **Prezzo di vendita** — il prezzo che applichi ai clienti
- **Prezzo di acquisto** — il prezzo che paghi al fornitore (opzionale)

**Esempi di richieste:**
- *"crea l'articolo ART001 Crocchette Premium, prezzo vendita 25 euro, prezzo acquisto 15 euro"*
- *"aggiorna il prezzo di acquisto di ART001 a 14 euro"*
- *"mostrami la lista articoli"* — la tabella mostra entrambi i prezzi

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

> **Nota per l'amministratore:** per azzerare e rigenerare il database (ad esempio in fase di test o setup iniziale) è disponibile il file `reset_db.bat`. Chiede conferma prima di procedere e cancella tutti i dati.

---

## Portale ordini clienti (Shop)

I tuoi clienti possono ordinare direttamente da browser, senza Telegram, accedendo al portale shop integrato.

### Come accedere

- **Registrazione:** `http://localhost:8000/shop/register`
- **Accesso:** `http://localhost:8000/shop/login`

Il portale è incluso nello stesso pannello web — non serve avviare nulla di separato.

### Cosa possono fare i clienti

1. **Registrarsi** con ragione sociale, email e password — vengono creati automaticamente nel database clienti.
2. **Cercare articoli** in tempo reale per codice o descrizione (ricerca live mentre si digita).
3. **Aggiungere al carrello** con la quantità desiderata — il carrello mostra il totale aggiornato.
4. **Confermare l'ordine** con un click — l'ordine viene creato nel sistema con numero `WEB-DATA-NNNN`.
5. **Consultare i propri ordini** con il dettaglio delle righe e lo stato attuale.

### Per l'amministratore

Gli ordini inseriti dal portale shop appaiono normalmente nella lista ordini (sia nell'admin web che nelle richieste al bot Telegram). Si riconoscono dal prefisso `WEB-` nel numero d'ordine.

I clienti registrati via shop appaiono nell'anagrafica clienti con codice `WEB-<prefisso email>`.

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
