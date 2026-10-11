FROM python:3.11-slim

# Evita geração de .pyc e bufferiza stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala FFmpeg e dependências de compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p uploads sessions

# Expõe a porta do servidor
EXPOSE 5000

# Executa com Gunicorn (2 workers, timeout de 180s para uploads pesados de vídeo)
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "180", "wsgi:app"]
