#!/usr/bin/env python3
import os
import sys
import re
import base64
import tempfile
import requests
from dotenv import load_dotenv

# Import Notion SDK
try:
    from notion_client import Client
except ImportError:
    print("Errore: la libreria 'notion-client' non è installata. Installala con: pip install notion-client")
    sys.exit(1)

# Import Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Errore: le librerie Google API non sono installate. Installale con: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Ambito dei permessi di Google Drive (accesso completo in lettura/scrittura)
SCOPES = ['https://www.googleapis.com/auth/drive']

def setup_environment():
    """Configura l'ambiente caricando o richiedendo interattivamente i token necessari."""
    load_dotenv()
    
    notion_token = os.getenv('NOTION_TOKEN')
    notion_page_id = os.getenv('NOTION_PAGE_ID')
    drive_parent_id = os.getenv('DRIVE_PARENT_FOLDER_ID')
    
    updated = False
    
    print("=========================================================")
    print("   MIGRAZIONE NOTION -> GOOGLE DRIVE (API AUTOMATICA)   ")
    print("=========================================================\n")
    
    if not notion_token:
        notion_token = input("1. Inserisci il tuo Notion Integration Token (Secret): ").strip()
        updated = True
        
    if not notion_page_id:
        raw_id = input("2. Inserisci l'ID o l'URL della pagina Notion di partenza: ").strip()
        # Estrae l'ID da un eventuale URL di Notion
        if "/" in raw_id:
            parts = raw_id.split('/')
            last_part = parts[-1]
            if '?' in last_part:
                last_part = last_part.split('?')[0]
            if '-' in last_part:
                last_part = last_part.split('-')[-1]
            notion_page_id = last_part
        else:
            notion_page_id = raw_id
        updated = True
        
    if drive_parent_id is None:
        drive_parent_id = input("3. Inserisci l'ID della cartella di destinazione su Google Drive (premi Invio per la Root): ").strip()
        updated = True
        
    if updated:
        with open('.env', 'w') as f:
            f.write(f"NOTION_TOKEN={notion_token}\n")
            f.write(f"NOTION_PAGE_ID={notion_page_id}\n")
            f.write(f"DRIVE_PARENT_FOLDER_ID={drive_parent_id}\n")
        print("\n[INFO] Configurazione salvata in .env per i prossimi utilizzi!\n")
        
    return notion_token, notion_page_id, drive_parent_id

def get_google_drive_service():
    """Autentica l'utente tramite OAuth 2.0 e restituisce il servizio Google Drive API."""
    creds = None
    # Il file token.json memorizza i token di accesso e aggiornamento dell'utente
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # Se non ci sono credenziali valide disponibili, consente all'utente di accedere
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                print("\n[ERRORE] File 'credentials.json' non trovato in questa cartella!")
                print("Si prega di seguire la guida in GUIDA_CONFIGURAZIONE.md per crearlo e scaricarlo.")
                sys.exit(1)
                
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Salva le credenziali per il prossimo ciclo
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def download_image_as_base64(url):
    """Scarica un'immagine e la converte in una stringa Base64 per l'incorporamento inline nell'HTML."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.3"
        }
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', 'image/png')
            encoded = base64.b64encode(response.content).decode('utf-8')
            return f"data:{content_type};base64,{encoded}"
        else:
            print(f"  [Avviso] Errore nel download dell'immagine (Status {response.status_code})")
    except Exception as e:
        print(f"  [Avviso] Errore di connessione per l'immagine: {e}")
    return None

def rich_text_to_html(rich_text_array):
    """Converte un array Rich Text di Notion in HTML sicuro con stili di formattazione."""
    if not rich_text_array:
        return ""
    
    html = ""
    for segment in rich_text_array:
        text = segment.get('plain_text', '')
        # Escape HTML di base per evitare rotture di tag
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        ann = segment.get('annotations', {})
        if ann.get('code'):
            text = f'<code style="background-color: #f1f3f5; padding: 2px 4px; border-radius: 3px; font-family: monospace; font-size: 0.9em;">{text}</code>'
        if ann.get('bold'):
            text = f'<strong>{text}</strong>'
        if ann.get('italic'):
            text = f'<em>{text}</em>'
        if ann.get('strikethrough'):
            text = f'<del>{text}</del>'
        if ann.get('underline'):
            text = f'<u>{text}</u>'
            
        color = ann.get('color', 'default')
        if color != 'default' and not color.endswith('_background'):
            text = f'<span style="color: {color};">{text}</span>'
        elif color.endswith('_background'):
            bg_color = color.replace('_background', '')
            text = f'<span style="background-color: {bg_color}; padding: 1px 3px; border-radius: 2px;">{text}</span>'
            
        href = segment.get('href')
        if href:
            text = f'<a href="{href}" style="color: #0066cc; text-decoration: underline;">{text}</a>'
            
        html += text
    return html

def get_all_blocks(notion, block_id):
    """Recupera tutti i blocchi figli di un blocco Notion, gestendo la paginazione."""
    blocks = []
    cursor = None
    while True:
        try:
            response = notion.blocks.children.list(block_id=block_id, start_cursor=cursor)
            blocks.extend(response.get('results', []))
            if not response.get('has_more'):
                break
            cursor = response.get('next_cursor')
        except Exception as e:
            print(f"Errore nel recupero dei blocchi per {block_id}: {e}")
            break
    return blocks

def convert_blocks_to_html(notion, blocks):
    """Genera frammenti di codice HTML analizzando una lista di blocchi di Notion."""
    html = ""
    in_list = None # Traccia l'apertura e chiusura delle liste ul / ol
    
    for block in blocks:
        block_type = block.get('type')
        
        # Gestione transizioni liste
        if block_type == 'bulleted_list_item':
            if in_list != 'ul':
                if in_list: html += f"</{in_list}>\n"
                html += "<ul>\n"
                in_list = 'ul'
        elif block_type == 'numbered_list_item':
            if in_list != 'ol':
                if in_list: html += f"</{in_list}>\n"
                html += "<ol>\n"
                in_list = 'ol'
        else:
            if in_list:
                html += f"</{in_list}>\n"
                in_list = None
                
        # Conversione dei singoli tipi di blocchi
        if block_type == 'paragraph':
            text = rich_text_to_html(block['paragraph'].get('rich_text', []))
            # Ignoriamo i paragrafi completamente vuoti o aggiungiamo interlinea
            if text:
                html += f"<p>{text}</p>\n"
            else:
                html += "<p>&nbsp;</p>\n"
            if block.get('has_children'):
                nested = get_all_blocks(notion, block['id'])
                html += convert_blocks_to_html(notion, nested)
                
        elif block_type == 'heading_1':
            text = rich_text_to_html(block['heading_1'].get('rich_text', []))
            html += f"<h1 style='color: #111; margin-top: 24px; margin-bottom: 8px;'>{text}</h1>\n"
            
        elif block_type == 'heading_2':
            text = rich_text_to_html(block['heading_2'].get('rich_text', []))
            html += f"<h2 style='color: #222; margin-top: 20px; margin-bottom: 6px;'>{text}</h2>\n"
            
        elif block_type == 'heading_3':
            text = rich_text_to_html(block['heading_3'].get('rich_text', []))
            html += f"<h3 style='color: #333; margin-top: 16px; margin-bottom: 4px;'>{text}</h3>\n"
            
        elif block_type == 'bulleted_list_item':
            text = rich_text_to_html(block['bulleted_list_item'].get('rich_text', []))
            html += f"<li>{text}"
            if block.get('has_children'):
                nested = get_all_blocks(notion, block['id'])
                html += "\n" + convert_blocks_to_html(notion, nested)
            html += "</li>\n"
            
        elif block_type == 'numbered_list_item':
            text = rich_text_to_html(block['numbered_list_item'].get('rich_text', []))
            html += f"<li>{text}"
            if block.get('has_children'):
                nested = get_all_blocks(notion, block['id'])
                html += "\n" + convert_blocks_to_html(notion, nested)
            html += "</li>\n"
            
        elif block_type == 'to_do':
            text = rich_text_to_html(block['to_do'].get('rich_text', []))
            checked = block['to_do'].get('checked', False)
            checkbox = "☑" if checked else "☐"
            html += f"<p><span style='font-family: monospace; font-size: 1.2em; margin-right: 6px;'>{checkbox}</span>{text}</p>\n"
            if block.get('has_children'):
                nested = get_all_blocks(notion, block['id'])
                html += convert_blocks_to_html(notion, nested)
                
        elif block_type == 'toggle':
            text = rich_text_to_html(block['toggle'].get('rich_text', []))
            html += f"<details style='border: 1px solid #ddd; padding: 8px; border-radius: 4px; margin: 8px 0;'><summary style='font-weight: bold; cursor: pointer;'>{text}</summary>\n"
            if block.get('has_children'):
                nested = get_all_blocks(notion, block['id'])
                html += "<div style='padding-left: 15px; margin-top: 8px;'>" + convert_blocks_to_html(notion, nested) + "</div>\n"
            html += "</details>\n"
            
        elif block_type == 'quote':
            text = rich_text_to_html(block['quote'].get('rich_text', []))
            html += f"<blockquote style='border-left: 4px solid #0066cc; padding-left: 15px; margin: 12px 0; color: #555; font-style: italic;'>{text}</blockquote>\n"
            if block.get('has_children'):
                nested = get_all_blocks(notion, block['id'])
                html += convert_blocks_to_html(notion, nested)
                
        elif block_type == 'callout':
            text = rich_text_to_html(block['callout'].get('rich_text', []))
            icon_obj = block['callout'].get('icon', {})
            emoji = icon_obj.get('emoji', '💡') if icon_obj.get('type') == 'emoji' else '💡'
            html += f'<div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 12px; margin: 12px 0; border-radius: 4px; display: flex; align-items: flex-start;">'
            html += f'  <div style="font-size: 1.2em; margin-right: 12px; line-height: 1.2;">{emoji}</div>'
            html += f'  <div style="flex: 1; line-height: 1.5;">{text}</div>'
            html += '</div>\n'
            if block.get('has_children'):
                nested = get_all_blocks(notion, block['id'])
                html += convert_blocks_to_html(notion, nested)
                
        elif block_type == 'divider':
            html += "<hr style='border: none; border-top: 1px solid #dee2e6; margin: 20px 0;' />\n"
            
        elif block_type == 'code':
            rich_texts = block['code'].get('rich_text', [])
            code_text = "".join([t.get('plain_text', '') for t in rich_texts])
            code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            lang = block['code'].get('language', 'plain text')
            html += f'<pre style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; border: 1px solid #e9ecef; overflow-x: auto; font-family: monospace; font-size: 0.9em;"><code class="language-{lang}">{code_text}</code></pre>\n'
            
        elif block_type == 'image':
            img_info = block['image']
            img_type = img_info.get('type')
            url = None
            if img_type == 'file':
                url = img_info['file'].get('url')
            elif img_type == 'external':
                url = img_info['external'].get('url')
                
            if url:
                b64 = download_image_as_base64(url)
                if b64:
                    html += f'<p style="text-align: center;"><img src="{b64}" style="max-width: 100%; max-height: 500px; display: block; margin: 16px auto;" /></p>\n'
                else:
                    html += f'<p style="text-align: center; color: #888;">[Immagine: <a href="{url}" target="_blank">Apri link esterno</a>]</p>\n'
                    
        elif block_type == 'table':
            table_rows = get_all_blocks(notion, block['id'])
            html += '<table style="border-collapse: collapse; width: 100%; border: 1px solid #dee2e6; margin: 16px 0; font-size: 0.95em;">\n'
            for row in table_rows:
                if row['type'] == 'table_row':
                    html += '  <tr>\n'
                    for cell in row['table_row'].get('cells', []):
                        cell_html = rich_text_to_html(cell)
                        html += f'    <td style="border: 1px solid #dee2e6; padding: 8px; vertical-align: top;">{cell_html}</td>\n'
                    html += '  </tr>\n'
            html += '</table>\n'
            
    if in_list:
        html += f"</{in_list}>\n"
        
    return html

def wrap_in_html_shell(title, body_content):
    """Incolla il corpo HTML convertito all'interno di uno scheletro HTML ben formattato."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 40px auto;
            max-width: 800px;
            padding: 0 20px;
        }}
        h1 {{ border-bottom: 2px solid #eaecef; padding-bottom: 8px; font-size: 2em; }}
        h2 {{ border-bottom: 1px solid #eaecef; padding-bottom: 6px; font-size: 1.5em; margin-top: 30px; }}
        h3 {{ font-size: 1.25em; margin-top: 24px; }}
        blockquote {{
            border-left: 4px solid #dfe2e5;
            padding-left: 16px;
            color: #6a737d;
            margin: 16px 0;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow: auto;
            font-size: 85%;
        }}
        code {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        table, th, td {{
            border: 1px solid #dfe2e5;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f6f8fa;
            font-weight: bold;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    {body_content}
</body>
</html>
"""

def get_page_title(page):
    """Estrae in modo sicuro il titolo da una risorsa pagina di Notion."""
    properties = page.get('properties', {})
    for prop_name, prop_val in properties.items():
        if prop_val.get('type') == 'title':
            title_list = prop_val.get('title', [])
            if title_list:
                return "".join([t.get('plain_text', '') for t in title_list])
    return "Pagina senza titolo"

def get_database_title(database):
    """Estrae in modo sicuro il titolo da una risorsa database di Notion."""
    title_list = database.get('title', [])
    if title_list:
        return "".join([t.get('plain_text', '') for t in title_list])
    return "Database senza titolo"

def create_drive_folder(drive_service, name, parent_id=None):
    """Crea una nuova cartella su Google Drive."""
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
        
    try:
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    except Exception as e:
        print(f"[ERRORE] Creazione cartella '{name}' fallita: {e}")
        return None

def upload_html_as_google_doc(drive_service, filepath, doc_name, parent_id=None):
    """Carica un file HTML temporaneo su Google Drive e lo converte in Google Doc."""
    file_metadata = {
        'name': doc_name,
        'mimeType': 'application/vnd.google-apps.document' # Converte l'HTML in Google Doc
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
        
    try:
        media = MediaFileUpload(filepath, mimetype='text/html', resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')
    except Exception as e:
        print(f"[ERRORE] Caricamento del documento '{doc_name}' fallito: {e}")
        return None

def get_database_pages(notion, database_id):
    """Recupera tutte le pagine contenute all'interno di un database Notion."""
    pages = []
    cursor = None
    while True:
        try:
            response = notion.databases.query(database_id=database_id, start_cursor=cursor)
            pages.extend(response.get('results', []))
            if not response.get('has_more'):
                break
            cursor = response.get('next_cursor')
        except Exception as e:
            print(f"[ERRORE] Query del database {database_id} fallita: {e}")
            break
    return pages

def check_has_subpages(blocks):
    """Controlla se tra i blocchi ce ne sono di tipo child_page o child_database."""
    for block in blocks:
        if block.get('type') in ('child_page', 'child_database'):
            return True
    return False

def export_page_recursive(notion, drive, page_id, parent_drive_id=None):
    """Funzione ricorsiva principale per esportare una pagina Notion e le sue sottopagine."""
    try:
        # Recupera dettagli della pagina
        page = notion.pages.retrieve(page_id=page_id)
        title = get_page_title(page)
        print(f"\n[*] Elaborazione pagina: {title} (ID: {page_id})")
        
        # Recupera tutti i blocchi della pagina
        blocks = get_all_blocks(notion, page_id)
        
        # Controlla se contiene sottopagine o database nidificati
        has_subelements = check_has_subpages(blocks)
        
        # Determina la destinazione dell'upload per il documento principale
        current_parent_id = parent_drive_id
        
        # Se ha sottopagine, creiamo una cartella con il nome della pagina su Google Drive
        if has_subelements:
            print(f"  --> La pagina contiene sottopagine. Creazione cartella su Google Drive...")
            folder_id = create_drive_folder(drive, title, parent_drive_id)
            if not folder_id:
                return
            current_parent_id = folder_id
            
            # Il documento della pagina stessa verrà caricato all'interno di questa cartella
            doc_name = title
        else:
            # È una pagina foglia, la carichiamo direttamente nella cartella corrente come Google Doc
            doc_name = title

        # Genera il file HTML per i blocchi di contenuto (esclusi child_page e child_database)
        content_blocks = [b for b in blocks if b.get('type') not in ('child_page', 'child_database')]
        
        print(f"  --> Conversione blocchi in HTML...")
        body_html = convert_blocks_to_html(notion, content_blocks)
        full_html = wrap_in_html_shell(title, body_html)
        
        # Scrittura su file HTML locale temporaneo
        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_filepath = temp_file.name
            temp_file.write(full_html)
            
        print(f"  --> Caricamento e conversione in Google Doc...")
        doc_id = upload_html_as_google_doc(drive, temp_filepath, doc_name, current_parent_id)
        if doc_id:
            print(f"  [SUCCESSO] Documento '{doc_name}' caricato con ID: {doc_id}")
        
        # Rimozione immediata del file locale temporaneo come richiesto dall'utente
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            print("  --> File temporaneo locale rimosso.")
            
        # Ora gestisce ricorsivamente i sotto-elementi
        for block in blocks:
            b_type = block.get('type')
            if b_type == 'child_page':
                subpage_id = block['id']
                # Chiamata ricorsiva con la nuova cartella come destinazione
                export_page_recursive(notion, drive, subpage_id, current_parent_id)
                
            elif b_type == 'child_database':
                db_id = block['id']
                export_database_recursive(notion, drive, db_id, current_parent_id)
                
    except Exception as e:
        print(f"[ERRORE] Elaborazione della pagina {page_id} non riuscita: {e}")

def export_database_recursive(notion, drive, database_id, parent_drive_id=None):
    """Esporta un database Notion creando una cartella su Google Drive e inserendo tutte le sue pagine."""
    try:
        # Recupera dettagli del database
        db = notion.databases.retrieve(database_id=database_id)
        db_title = get_database_title(db)
        print(f"\n[*] Elaborazione database: {db_title} (ID: {database_id})")
        
        # Crea una cartella per il database
        print(f"  --> Creazione cartella database su Google Drive...")
        db_folder_id = create_drive_folder(drive, db_title, parent_drive_id)
        if not db_folder_id:
            return
            
        # Recupera tutte le pagine nel database
        pages = get_database_pages(notion, database_id)
        print(f"  --> Trovate {len(pages)} pagine nel database. Inizio migrazione...")
        
        for p in pages:
            export_page_recursive(notion, drive, p['id'], db_folder_id)
            
    except Exception as e:
        print(f"[ERRORE] Elaborazione del database {database_id} non riuscita: {e}")

def main():
    # Caricamento e configurazione credenziali
    notion_token, notion_page_id, drive_parent_id = setup_environment()
    
    # Inizializzazione client Notion
    print("[*] Inizializzazione Notion API...")
    notion = Client(auth=notion_token)
    
    # Inizializzazione servizio Google Drive
    print("[*] Connessione a Google Drive API...")
    drive = get_google_drive_service()
    
    print("\n[INFO] Avvio migrazione ricorsiva. Per favore attendi...\n")
    # Avvia l'esportazione
    export_page_recursive(notion, drive, notion_page_id, drive_parent_id or None)
    
    print("\n=========================================================")
    print("      MIGRAZIONE COMPLETATA CON SUCCESSO! 🎉")
    print("=========================================================")

if __name__ == "__main__":
    main()
