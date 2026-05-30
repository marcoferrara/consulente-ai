# 🏺 AIjò Dice Gacha — Game Design Document (GDD) Light

Benvenuto nel documento di visione di **AIjò Dice Gacha**, un mobile game a turni di dadi con progressione su tabellone lineare ed epici combattimenti automatici in tempo reale, interamente ambientato nei miti, nelle leggende e nelle tradizioni ancestrali della **Sardegna**.

---

## 🎭 1. Ambientazione, Eroi & Costumi (The Heritage)

Il gioco è immerso nel folclore sardo: i livelli si snodano attraverso scenari suggestivi come la Barbagia selvaggia, le rovine dei nuraghi millenari, le spiagge dorate del Sinis, i pozzi sacri e le mistiche *Domus de Janas*.

### 🛡️ Le Classi degli Eroi (La Squadra Ufficiale):
Ogni giocatore schiera in battaglia una **squadra di 5 Eroi attivi**, ognuno caratterizzato da costumi tradizionali rivisitati in chiave fantasy-core:

1. **Shardana (Guerrieri - Danno Fisico)**: 
   * *Estetica*: Elmo cornuto tipico dei bronzetti, scudo tondo dorato, spada e corazza di bronzo martellato.
   * *Abilità Speciale*: *Furia del Bronzo* — Un fendente devastante a bersaglio singolo.
2. **Janas (Fate/Maghe - Danno Magico & Cura)**: 
   * *Estetica*: Abiti in velluto rosso e broccato dorato con ricami floreali, scialli tradizionali e grandi amuleti in filigrana d'oro.
   * *Abilità Speciale*: *Soffio di Domus* — Cura l'intera squadra o scaglia saette di pura luce stellare.
3. **Giganti di Mont'e Prama (Difensori/Tank - Protezione)**: 
   * *Estetica*: Monumentali giganti di pietra arenaria con scudo rettangolare tenuto sulla testa e occhi a doppio cerchio concentrico.
   * *Abilità Speciale*: *Scudo Concentrico* — Genera una barriera difensiva per tutta la squadra.
4. **Accabadora (Assassini - Danno Rapido & Critico)**: 
   * *Estetica*: Maschera e velo nero profondo di panno tipico dell'Accabadora, impugnano un martello di legno d'olivo e un pugnale d'ossidiana lucida.
   * *Abilità Speciale*: *Colpo di Grazia* — Danno critico elevatissimo ai nemici con meno del 30% di salute.

### 👿 I Nemici e Boss di Livello:
* **Mamuthones Oscuri**: Figure mascherate di nero con pesanti campanacci (scatole) sulla schiena che caricano gli eroi con attacchi stordenti.
* **Orchi di Monte Arci**: Creature di fango e pietra vulcanica che usano clave di basalto.
* **Boss di Fine Livello (es. S'Orco o Sa Mamma 'e su Sole)**: Grandi divinità folcloristiche giganti con abilità ad area.

---

## 🗺️ 2. La Tavola: Il Percorso Lineare a Serpente

I livelli non si giocano su circuiti chiusi (stile Monopoly), ma su un **tracciato lineare a serpente** che scorre verticalmente sullo schermo dello smartphone:

* **Progressione della Dimensione (Caselle)**:
  * **Livello 1 (Tutorial/Presentazione)**: Composto da **15 caselle** per introdurre in modo rapido e amichevole il gameplay.
  * **Livelli successivi**: La dimensione del tabellone aumenta di 2-3 caselle per ogni livello.
  * **Dal Livello 15 in poi**: Raggiunge il bilanciamento ideale fisso a un massimo di **50 caselle** per livello, garantendo partite dinamiche ma strategiche.
  
* **I Tipi di Casella**:
  1. **🪙 Casella Moneta (Coins)**: Raccogli oro sardo per l'upgrade degli eroi.
  2. **💎 Casella Gemma (Gems)**: Raccogli gemme preziose per le evocazioni Gacha.
  3. **🩹 Casella Tempio (Tempio Sacro / Bonus Stat)**: Ripristina i punti vita della squadra o aumenta temporaneamente l'attacco.
  4. **🕸️ Casella Trappola (Malus)**: Danno da trappola (frane di roccia nuragica, spine) che riduce i punti vita correnti della squadra.
  5. **⚔️ Casella Nemico Comune (Common Enemy)**: Avvia un combattimento istantaneo in tempo reale contro servitori (es. Mamuthones comuni).
  6. **💀 Casella Nemico Elite (Elite Enemy)**: Incontro impegnativo a metà percorso con ricompense ricche.
  7. **🏁 Casella Boss Finale (Final Boss)**: Posizionata sempre sull'ultima casella del percorso lineare, sblocca il livello successivo al suo superamento.

---

## ⚔️ 3. Combat System: Tempo Reale Attivo

Quando la pedina atterra su una casella Nemico, Elite o Boss, il gioco passa alla modalità **Combat System in Tempo Reale**:

* **Flusso del Combattimento**:
  * Gli eroi e i nemici si affrontano automaticamente scambiandosi attacchi di base ad intervalli fissi (es. ogni 1.0 secondi).
  * La squadra combatte come un'unica entità i cui valori di attacco, difesa e punti vita totali dipendono dai 5 Eroi schierati.
  
* **Abilità Speciali con Tempo di Evocazione (Casting & Cooldown)**:
  * Ogni classe di eroe ha una barra di ricarica dell'abilità speciale (*tempo di evocazione*).
  * Ad esempio, una *Jana* impiega **4.0 secondi** per incanalare l'abilità magica, dopodiché la rilascia curando la squadra o infliggendo un grosso danno, avviando poi un *cooldown* di ricarica.
  * L'Accabadora ha colpi rapidi ma necessita di ricarica per il colpo critico passante.
  * Il combattimento termina in tempo reale alla sconfitta di tutti i nemici (Vittoria) o all'esaurimento dei Punti Vita della squadra di Eroi (Sconfitta).

---

## 🔮 4. La Matrice Gacha degli Eroi (C, R, S, SR)

Nel villaggio nuragico, spendendo le gemme raccolte durante i livelli, è possibile accedere alla **Grotta delle Evocazioni** per ottenere nuovi guerrieri o sbloccare potenziamenti di quelli esistenti:

| Grado Rarity | Colore / Simbolo | Percentuale di Drop | Descrizione e Profilo |
| :--- | :--- | :--- | :--- |
| **C - Comune** | ⚪ Grigio Ardesia | **70%** | Eroi base del villaggio (es. Pastori, Cacciatori Shardana). |
| **R - Raro** | 🔵 Blu Mediterraneo | **20%** | Combattenti esperti con armature di bronzo stabili. |
| **S - Speciale** | 🟣 Viola Janas | **8%** | Incantatori Janas potenti e Shardana con elmo cornuto regale. |
| **SR - Super Raro** | 🟡 Oro AIjò | **2%** | I mitici Giganti di Mont'e Prama o Guerrieri Shardana d'élite con scudo e arco. |

---

> [!NOTE]
> **Bilanciamento & Progressione:** Nel corso dello sviluppo dei vari Sprint, integreremo il database SQLite per memorizzare l'inventario degli Eroi evocati e il livello di fusione degli eroi doppi per aumentarne le statistiche del 15% a fusione.
