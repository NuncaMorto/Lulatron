import os
import logging
import subprocess
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    BadPassword,
    TwoFactorRequired,
    ChallengeRequired,
    PleaseWaitFewMinutes,
)

import config

logger = logging.getLogger("InstagramBot")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [Bot] %(message)s"))
    logger.addHandler(ch)

# Garante que o FFmpeg embutido do imageio-ffmpeg seja reconhecido pelo MoviePy e instagrapi
try:
    import imageio_ffmpeg
    ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_binary
    logger.info(f"FFmpeg detectado e configurado: {ffmpeg_binary}")
except ImportError:
    logger.warning("imageio-ffmpeg não instalado. Recomenda-se instalar para processamento de vídeos.")


class InstagramService:
    """
    Serviço centralizado para autenticação e publicação no Instagram com instagrapi.
    Implementa gerenciamento inteligente de sessão persistida em arquivo JSON
    e extração automática de miniaturas (thumbnails) para Reels e Stories.
    """

    def __init__(self):
        self.cl = Client()
        self.username = config.IG_USERNAME
        self.password = config.IG_PASSWORD
        self.session_file = Path(config.SESSION_FILE)

        # Configurações de timeout razoáveis para uploads de vídeo
        self.cl.request_timeout = 90

        if config.IG_PROXY:
            logger.info("Configurando proxy para a sessão do Instagram...")
            self.cl.set_proxy(config.IG_PROXY)

    def extract_thumbnail(self, video_path: Path) -> Path | None:
        """
        Gera automaticamente uma imagem de capa (thumbnail .jpg) a partir do vídeo.
        Evita a dependência estrita do MoviePy 2.2.1 no instagrapi.
        """
        thumb_path = video_path.with_suffix(".thumb.jpg")
        if thumb_path.exists() and thumb_path.stat().st_size > 0:
            return thumb_path

        # Método 1: Extração rápida via FFmpeg binário do imageio-ffmpeg
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [
                ffmpeg_exe,
                "-y",
                "-ss", "00:00:00.500",
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(thumb_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if thumb_path.exists() and thumb_path.stat().st_size > 0:
                logger.info(f"Thumbnail gerada com sucesso via FFmpeg: {thumb_path.name}")
                return thumb_path
        except Exception as e:
            logger.debug(f"Falha ao extrair thumbnail com imageio-ffmpeg: {e}")

        # Método 2: MoviePy se instalado
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
            clip = VideoFileClip(str(video_path))
            clip.save_frame(str(thumb_path), t=0.5)
            clip.close()
            if thumb_path.exists():
                logger.info(f"Thumbnail gerada com sucesso via MoviePy: {thumb_path.name}")
                return thumb_path
        except Exception as e:
            logger.debug(f"Falha ao extrair thumbnail com MoviePy: {e}")

        return None

    def get_client(self) -> Client:
        """
        Retorna o cliente autenticado.
        Tenta reaproveitar a sessão salva em session.json.
        Apenas realiza novo login se a sessão for inexistente ou inválida.
        """
        if not self.username or not self.password:
            raise ValueError("Credenciais do Instagram não configuradas no arquivo .env!")

        # 1. Tentar reaproveitar sessão existente
        if self.session_file.exists():
            try:
                logger.info(f"Carregando sessão existente de {self.session_file}...")
                self.cl.load_settings(self.session_file)
                # Testa se a sessão ainda é válida fazendo uma requisição leve
                self.cl.get_timeline_feed()
                logger.info("Sessão válida reaproveitada com sucesso! Login adicional evitado.")
                return self.cl
            except (LoginRequired, Exception) as e:
                logger.warning(f"Sessão salva expirada ou inválida: {e}. Iniciando novo login.")

        # 2. Executar novo login e salvar sessão
        try:
            logger.info(f"Autenticando usuário @{self.username} no Instagram...")
            
            # Se houver TOTP seed configurado para 2FA automático
            verification_code = None
            if config.IG_TOTP_SEED:
                try:
                    import pyotp
                    totp = pyotp.TOTP(config.IG_TOTP_SEED)
                    verification_code = totp.now()
                    logger.info("Código 2FA gerado automaticamente via TOTP Seed.")
                except ImportError:
                    logger.warning("pyotp não instalado. 2FA automático não disponível.")

            self.cl.login(self.username, self.password, verification_code=verification_code)
            
            # Salva as configurações de sessão para evitar novos logins
            self.cl.dump_settings(self.session_file)
            logger.info(f"Login efetuado com sucesso! Sessão salva em {self.session_file}")
            return self.cl

        except BadPassword:
            logger.error("Falha de autenticação: Senha incorreta.")
            raise
        except TwoFactorRequired:
            logger.error("Autenticação em Dois Fatores (2FA) necessária na conta.")
            raise
        except ChallengeRequired:
            logger.error("Instagram solicitou desafio/verificação de segurança (Challenge Required).")
            raise
        except PleaseWaitFewMinutes:
            logger.error("Bloqueio temporário (Please wait a few minutes). Aguarde antes de tentar novamente.")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado durante o login: {e}")
            raise

    def reload_credentials(self, username: str, password: str, proxy: str = None, totp_seed: str = None):
        """Atualiza as credenciais em memória imediatamente."""
        self.username = username
        self.password = password
        if proxy:
            self.cl.set_proxy(proxy)

    def test_and_save_session(self, username: str, password: str, proxy: str = None, totp_seed: str = None, verification_code: str = None) -> dict:
        """
        Executa login de teste com as novas credenciais e salva o session.json.
        """
        self.username = username
        self.password = password
        self.cl = Client()
        self.cl.request_timeout = 90
        if proxy:
            self.cl.set_proxy(proxy)

        if not verification_code and totp_seed:
            try:
                import pyotp
                totp = pyotp.TOTP(totp_seed)
                verification_code = totp.now()
            except ImportError:
                pass

        try:
            self.cl.login(username, password, verification_code=verification_code)
            self.cl.dump_settings(self.session_file)
            user_info = self.cl.user_info_by_username(username)
            return {
                "status": "connected",
                "username": user_info.username,
                "full_name": user_info.full_name,
                "follower_count": user_info.follower_count,
                "media_count": user_info.media_count,
            }
        except TwoFactorRequired:
            return {"status": "2fa_required", "message": "Autenticação em Dois Fatores (2FA) ativada nesta conta."}
        except ChallengeRequired:
            return {"status": "challenge_required", "message": "Instagram solicitou desafio de segurança (Challenge Required)."}
        except BadPassword:
            return {"status": "error", "message": "Usuário ou senha incorretos."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def disconnect(self):
        """Desconecta a conta e apaga a sessão salva."""
        if self.session_file.exists():
            try:
                self.session_file.unlink()
            except Exception:
                pass
        self.username = ""
        self.password = ""
        self.cl = Client()

    def check_health(self) -> dict:
        """
        Verifica o estado de conexão da conta com o Instagram.
        """
        if not self.username or not self.password:
            return {"status": "unconfigured", "message": "Conta do Instagram não configurada."}

        try:
            client = self.get_client()
            user_info = client.user_info_by_username(self.username)
            return {
                "status": "connected",
                "username": user_info.username,
                "full_name": user_info.full_name,
                "follower_count": user_info.follower_count,
                "media_count": user_info.media_count,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "username": self.username
            }

    def post_video_feed_or_reels(self, video_path: str, caption: str = "") -> dict:
        """
        Publica um vídeo no Feed / Reels do Instagram.
        Gera ou passa a thumbnail para evitar falha no instagrapi.
        """
        file_path = Path(video_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")

        logger.info(f"Iniciando publicação no Feed/Reels: {file_path.name}")
        client = self.get_client()

        # Extrai thumbnail antecipadamente para contornar falha de dependências
        thumbnail = self.extract_thumbnail(file_path)

        kwargs = {
            "path": file_path,
            "caption": caption
        }
        if thumbnail:
            kwargs["thumbnail"] = thumbnail

        media = client.clip_upload(**kwargs)

        logger.info(f"Vídeo publicado com sucesso no Feed/Reels! ID: {media.pk}")
        return {
            "success": True,
            "media_id": media.pk,
            "media_type": "reels",
            "caption": caption,
            "code": getattr(media, "code", "")
        }

    def post_video_story(self, video_path: str, caption: str = "") -> dict:
        """
        Publica um vídeo nos Stories do Instagram.
        """
        file_path = Path(video_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")

        logger.info(f"Iniciando publicação nos Stories: {file_path.name}")
        client = self.get_client()

        thumbnail = self.extract_thumbnail(file_path)

        kwargs = {
            "path": file_path,
            "caption": caption if caption else None
        }
        if thumbnail:
            kwargs["thumbnail"] = thumbnail

        media = client.video_upload_to_story(**kwargs)

        logger.info(f"Vídeo publicado com sucesso nos Stories! ID: {media.pk}")
        return {
            "success": True,
            "media_id": media.pk,
            "media_type": "story",
            "caption": caption
        }

    def publish(self, destination: str, video_path: str, caption: str = "") -> dict:
        """
        Roteia a publicação com base no destino escolhido ('feed' / 'reels' ou 'story').
        """
        dest = destination.lower().strip()
        if dest in ["feed", "reels"]:
            return self.post_video_feed_or_reels(video_path, caption)
        elif dest in ["story", "stories"]:
            return self.post_video_story(video_path, caption)
        else:
            raise ValueError(f"Destino desconhecido: '{destination}'. Use 'feed', 'reels' ou 'story'.")


# Instância global do serviço
instagram_service = InstagramService()
