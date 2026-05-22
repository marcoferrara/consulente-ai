import os
import zipfile
import sys

def main():
    zip_filename = "antiga_armonia_deploy.zip"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Cartelle e file da escludere
    exclude_dirs = {
        'venv', '.git', 'uploads', 'test_data_dir', '__pycache__', 
        '.gemini', '.system_generated'
    }
    exclude_files = {
        '.env', zip_filename, '.DS_Store', 'crea_pacchetto.py'
    }
    
    print("=" * 60)
    print("  CREATORE DI PACCHETTI DI DEPLOY — ANTIGA ARMONIA")
    print("=" * 60)
    print(f"Directory di lavoro: {base_dir}")
    print("Esclusione cartelle: " + ", ".join(sorted(exclude_dirs)))
    print("Esclusione file:     " + ", ".join(sorted(exclude_files)))
    print("-" * 60)
    
    count = 0
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(base_dir):
                # Esclude le directory sul posto modificando la lista dirs
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
                
                for file in files:
                    if file in exclude_files or file.startswith('.'):
                        continue
                    
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    
                    # Filtro di sicurezza aggiuntivo per i percorsi relativi
                    if any(part in rel_path.split(os.sep) for part in exclude_dirs):
                        continue
                        
                    zipf.write(full_path, rel_path)
                    print(f" -> Aggiunto: {rel_path}")
                    count += 1
                    
        zip_size = os.path.getsize(zip_filename) / (1024 * 1024) # MB
        print("-" * 60)
        print("COMPLETATO CON SUCCESSO! ✓")
        print(f"Creato archivio:       {zip_filename}")
        print(f"File inseriti:         {count}")
        print(f"Dimensione archivio:   {zip_size:.2f} MB")
        print("-" * 60)
        print("Istruzioni:")
        print("1. Condividi il file 'antiga_armonia_deploy.zip' con il cliente o caricalo sul server.")
        print("2. Scompatta lo zip nella directory di esecuzione sul server.")
        print("3. Configura il file .env e avvia il server (vedi guida_deploy.md).")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERRORE DURANTE LA CREAZIONE DEL PACCHETTO: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
