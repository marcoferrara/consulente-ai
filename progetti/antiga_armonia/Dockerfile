FROM python:3.9-slim

# Evita che Python scriva i file .pyc e abilita il logging non bufferizzato
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installa le dipendenze di sistema minime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installa le dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Espone la porta predefinita (Cloud Run inietterà la variabile d'ambiente $PORT)
EXPOSE 8080

# Comando di avvio che supporta l'espansione della variabile $PORT in modo dinamico
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
