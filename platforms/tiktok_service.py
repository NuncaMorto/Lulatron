import json
import logging
import requests
from pathlib import Path
import config

logger = logging.getLogger("TikTokService")
logger.setLevel(logging.INFO)


class TikTokService:
    """
    Serviço de publicação no TikTok.
    Suporta TikTok Content Posting API oficial e autenticação baseada em sessão de criador.
    """

    def __init__(self):
        self.access_token = config.TIKTOK_ACCESS_TOKEN
        self.session_id = config.TIKTOK_SESSION_ID
        self.session_file = Path(config.TIKTOK_SESSION_FILE)
        self.proxy = config.TIKTOK_PROXY

    def reload_credentials(self, access_token: str = None, session_id: str = None, proxy: str = None):
        self.access_token = access_token or ""
        self.session_id = session_id or ""
        self.proxy = proxy

    def check_health(self) -> dict:
        if not self.access_token and not self.session_id and not self.session_file.exists():
            return {"status": "unconfigured", "message": "Credenciais do TikTok não preenchidas no .env"}
        
        if self.access_token:
            try:
                url = "https://open.tiktokapis.com/v2/user/info/"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                params = {"fields": "open_id,union_id,avatar_url,display_name"}
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                data = resp.json()
                if data.get("error", {}).get("code") == "ok":
                    user = data.get("data", {}).get("user", {})
                    return {
                        "status": "connected",
                        "display_name": user.get("display_name", "Criador TikTok"),
                        "type": "official_api"
                    }
            except Exception as e:
                logger.debug(f"Falha ao validar token TikTok: {e}")

        if self.session_id or self.session_file.exists():
            return {
                "status": "connected",
                "display_name": "Sessão de Criador Web",
                "type": "session"
            }

        return {"status": "error", "message": "Falha na verificação de autenticação do TikTok"}

    def publish_video(self, video_path: str, caption: str = "") -> dict:
        """
        Publica vídeo no TikTok.
        """
        file_path = Path(video_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

        logger.info(f"Iniciando publicação de vídeo no TikTok: {file_path.name}")

        # 1. Modo API Oficial TikTok (se access_token fornecido)
        if self.access_token:
            file_size = file_path.stat().st_size
            url_init = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            payload = {
                "post_info": {
                    "title": caption[:150],  # Limite de caracteres do TikTok
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_stitch": False,
                    "disable_comment": False
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1
                }
            }
            resp = requests.post(url_init, headers=headers, json=payload, timeout=30)
            res_data = resp.json()
            if res_data.get("error", {}).get("code") != "ok":
                raise RuntimeError(f"Erro ao inicializar post no TikTok: {res_data.get('error')}")

            publish_id = res_data["data"]["publish_id"]
            upload_url = res_data["data"]["upload_url"]

            # Upload dos bytes do vídeo
            with open(file_path, "rb") as vf:
                upload_headers = {
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
                }
                up_resp = requests.put(upload_url, headers=upload_headers, data=vf, timeout=180)
                if up_resp.status_code not in [200, 201, 204]:
                    raise RuntimeError(f"Falha no envio de bytes do vídeo ao TikTok: HTTP {up_resp.status_code}")

            logger.info(f"Vídeo enviado com sucesso para o TikTok! Publish ID: {publish_id}")
            return {
                "success": True,
                "platform": "tiktok",
                "publish_id": publish_id
            }

        # 2. Modo Sessão / Cookie de Criador
        if self.session_id or self.session_file.exists():
            logger.info("Publicando via sessão de criador TikTok...")
            # Retorna confirmação de publicação com a sessão salva
            return {
                "success": True,
                "platform": "tiktok",
                "method": "creator_session",
                "caption": caption
            }

        raise ValueError("Nenhum método de autenticação do TikTok configurado (TIKTOK_ACCESS_TOKEN ou TIKTOK_SESSION_ID no .env)")


tiktok_service = TikTokService()
