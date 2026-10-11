import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Diretórios operacionais
UPLOAD_FOLDER = BASE_DIR / "uploads"
SESSION_FOLDER = BASE_DIR / "sessions"
SESSION_FILE = SESSION_FOLDER / "session.json"
TIKTOK_SESSION_FILE = SESSION_FOLDER / "tiktok_session.json"
KWAI_SESSION_FILE = SESSION_FOLDER / "kwai_session.json"
DATABASE_URL = f"sqlite:///{BASE_DIR / 'jobs.sqlite'}"

# Garante que os diretórios necessários existem
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
SESSION_FOLDER.mkdir(parents=True, exist_ok=True)

# Segurança da Dashboard
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")

# Chave secreta de sessão: se não definida ou for o placeholder, gera uma chave criptográfica efêmera
_env_secret = os.getenv("SECRET_KEY", "").strip()
_placeholder = "generate-a-strong-secret-key-for-session-protection"
if not _env_secret or _env_secret == _placeholder or _env_secret == "gere_uma_chave_longa_e_aleatoria_com_openssl_rand_hex_32":
    SECRET_KEY = secrets.token_hex(32)
else:
    SECRET_KEY = _env_secret

# Instagram
IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_PASSWORD = os.getenv("IG_PASSWORD", "")
IG_PROXY = os.getenv("IG_PROXY", None)
IG_TOTP_SEED = os.getenv("IG_TOTP_SEED", None)

# Facebook (Meta Graph API)
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")

# TikTok (Content Posting API ou Session)
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID", "")
TIKTOK_PROXY = os.getenv("TIKTOK_PROXY", None)

# Kwai (Open API ou Session)
KWAI_APP_ID = os.getenv("KWAI_APP_ID", "")
KWAI_ACCESS_TOKEN = os.getenv("KWAI_ACCESS_TOKEN", "")
KWAI_PROXY = os.getenv("KWAI_PROXY", None)

# Configurações do Servidor Web (Padrão 127.0.0.1 para evitar exposição indevida na rede local)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))

# Limites de Upload (150MB para vídeos)
MAX_CONTENT_LENGTH = 150 * 1024 * 1024
ALLOWED_EXTENSIONS = {"mp4", "mov", "mkv", "webm", "jpg", "jpeg", "png"}
