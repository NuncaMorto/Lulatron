import logging
import requests
from pathlib import Path
import config

logger = logging.getLogger("FacebookService")
logger.setLevel(logging.INFO)


class FacebookService:
    """
    Serviço de publicação no Facebook (Páginas / Reels) usando a Meta Graph API Oficial.
    Método 100% seguro contra bloqueios, pois utiliza tokens oficiais concedidos pela Meta.
    """

    def __init__(self):
        self.page_id = config.FB_PAGE_ID
        self.access_token = config.FB_PAGE_ACCESS_TOKEN
        self.api_version = "v19.0"

    def reload_credentials(self, page_id: str, access_token: str):
        self.page_id = page_id
        self.access_token = access_token

    def check_health(self) -> dict:
        if not self.page_id or not self.access_token:
            return {"status": "unconfigured", "message": "FB_PAGE_ID ou FB_PAGE_ACCESS_TOKEN ausente"}
        
        try:
            url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}"
            params = {"access_token": self.access_token, "fields": "name,id,fan_count"}
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()

            if "error" in data:
                return {"status": "error", "message": data["error"].get("message", "Erro Meta API")}
            
            return {
                "status": "connected",
                "name": data.get("name", "Página Facebook"),
                "id": data.get("id"),
                "fan_count": data.get("fan_count", 0)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def publish_video(self, video_path: str, caption: str = "") -> dict:
        """
        Publica um vídeo na Página do Facebook (visível no Feed e Reels da Página).
        """
        file_path = Path(video_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

        if not self.page_id or not self.access_token:
            raise ValueError("Credenciais do Facebook não configuradas no .env (FB_PAGE_ID e FB_PAGE_ACCESS_TOKEN)")

        logger.info(f"Iniciando upload de vídeo para Facebook Page {self.page_id}...")

        url = f"https://graph-video.facebook.com/{self.api_version}/{self.page_id}/videos"
        data = {
            "description": caption,
            "access_token": self.access_token
        }

        with open(file_path, "rb") as video_file:
            files = {"source": video_file}
            response = requests.post(url, data=data, files=files, timeout=180)

        result = response.json()

        if "error" in result:
            err_msg = result["error"].get("message", "Erro ao publicar no Facebook")
            logger.error(f"Erro Facebook Graph API: {err_msg}")
            raise RuntimeError(f"Erro Facebook API: {err_msg}")

        video_id = result.get("id")
        logger.info(f"Vídeo publicado com sucesso no Facebook! ID: {video_id}")
        return {
            "success": True,
            "platform": "facebook",
            "video_id": video_id,
            "page_id": self.page_id
        }


facebook_service = FacebookService()
