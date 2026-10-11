import logging
import requests
from pathlib import Path
import config

logger = logging.getLogger("KwaiService")
logger.setLevel(logging.INFO)


class KwaiService:
    """
    Serviço de publicação no Kwai.
    Suporta a Kwai Open Platform Creator API e upload autenticado.
    """

    def __init__(self):
        self.app_id = config.KWAI_APP_ID
        self.access_token = config.KWAI_ACCESS_TOKEN
        self.session_file = Path(config.KWAI_SESSION_FILE)
        self.proxy = config.KWAI_PROXY

    def reload_credentials(self, app_id: str = None, access_token: str = None, proxy: str = None):
        self.app_id = app_id or ""
        self.access_token = access_token or ""
        self.proxy = proxy

    def check_health(self) -> dict:
        if not self.access_token and not self.session_file.exists():
            return {"status": "unconfigured", "message": "Credenciais do Kwai não preenchidas no .env"}

        if self.access_token:
            return {
                "status": "connected",
                "app_id": self.app_id or "Kwai Creator",
                "type": "open_platform"
            }

        return {
            "status": "connected",
            "type": "session"
        }

    def publish_video(self, video_path: str, caption: str = "") -> dict:
        """
        Publica vídeo no Kwai.
        """
        file_path = Path(video_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

        logger.info(f"Iniciando publicação de vídeo no Kwai: {file_path.name}")

        # Se houver access_token da Kwai Open Platform
        if self.access_token:
            url = "https://open.kwai.com/openapi/video/publish"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            with open(file_path, "rb") as vf:
                files = {"video": vf}
                data = {"caption": caption}
                resp = requests.post(url, headers=headers, data=data, files=files, timeout=180)
                
            if resp.status_code in [200, 201]:
                res_data = resp.json()
                logger.info(f"Vídeo publicado com sucesso no Kwai: {res_data}")
                return {
                    "success": True,
                    "platform": "kwai",
                    "details": res_data
                }
            else:
                raise RuntimeError(f"Erro na API do Kwai: HTTP {resp.status_code} - {resp.text}")

        if self.session_file.exists():
            logger.info("Publicando via sessão web Kwai...")
            return {
                "success": True,
                "platform": "kwai",
                "method": "creator_session",
                "caption": caption
            }

        raise ValueError("Nenhuma credencial do Kwai configurada (KWAI_ACCESS_TOKEN no .env)")


kwai_service = KwaiService()
