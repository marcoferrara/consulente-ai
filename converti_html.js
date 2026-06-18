/**
 * Converte tutti i file HTML nella cartella 'Consulente AI' in Google Docs
 * e sposta i file HTML originali nel Cestino.
 * 
 * Istruzioni per l'uso:
 * 1. Vai su https://script.google.com/
 * 2. Clicca su "Nuovo progetto" in alto a sinistra.
 * 3. Cancella il codice presente e incolla questo script.
 * 4. Salva il progetto (icona del floppy disk o Cmd+S / Ctrl+S).
 * 5. Clicca su "Esegui" in alto.
 * 6. Autorizza lo script quando richiesto (clicca su "Avanzate" -> "Vai a Progetto senza nome (non sicura)").
 */
function convertiHtmlInDocs() {
  var nomeCartella = "Consulente AI";
  var cartelle = DriveApp.getFoldersByName(nomeCartella);
  
  if (!cartelle.hasNext()) {
    Logger.log("Cartella non trovata: " + nomeCartella);
    return;
  }
  
  var cartella = cartelle.next();
  var fileLista = cartella.getFiles();
  var contatore = 0;
  
  while (fileLista.hasNext()) {
    var file = fileLista.next();
    var nome = file.getName();
    var mimeType = file.getMimeType();
    
    // Controlla se il file è HTML (per estensione o per MimeType)
    if (mimeType === "text/html" || nome.toLowerCase().endsWith(".html")) {
      Logger.log("Inizio conversione di: " + nome);
      
      // Rimuove l'estensione .html dal nome del nuovo documento
      var nomeDoc = nome.replace(/\.html$/i, "");
      
      // Endpoint multipart per l'upload tramite le API di Google Drive
      var url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart";
      
      var metadati = {
        name: nomeDoc,
        mimeType: "application/vnd.google-apps-document",
        parents: [cartella.getId()]
      };
      
      var boundary = "multipart_boundary_conversion";
      var delimiter = "\r\n--" + boundary + "\r\n";
      var chiusuraDelim = "\r\n--" + boundary + "--";
      
      var corpoRichiesta = delimiter +
                           "Content-Type: application/json; charset=UTF-8\r\n\r\n" +
                           JSON.stringify(metadati) +
                           delimiter +
                           "Content-Type: text/html\r\n\r\n" +
                           file.getBlob().getDataAsString() +
                           chiusuraDelim;
                           
      var opzioni = {
        method: "post",
        contentType: "multipart/related; boundary=" + boundary,
        headers: {
          Authorization: "Bearer " + ScriptApp.getOAuthToken()
        },
        payload: corpoRichiesta,
        muteHttpExceptions: true
      };
      
      var risposta = UrlFetchApp.fetch(url, opzioni);
      
      if (risposta.getResponseCode() === 200) {
        Logger.log("Convertito con successo: " + nome + " in Google Doc");
        file.setTrashed(true); // Sposta il file HTML originale nel Cestino
        contatore++;
      } else {
        Logger.log("Errore nella conversione di " + nome + ": " + risposta.getContentText());
      }
    }
  }
  
  Logger.log("Completato! Convertiti " + contatore + " file.");
}
