import json
import logging
import os
import re
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import imageio_ffmpeg
import requests
import yt_dlp
from curl_cffi import requests as cffi_requests

import config
from instagram_bot import instagram_service

logger = logging.getLogger("MediaExtractor")
logger.setLevel(logging.INFO)

EXTRACTED_DIR = Path(config.UPLOAD_FOLDER) / "extracted"
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = EXTRACTED_DIR / "extracted_history.json"


def format_bytes(size: int) -> str:
    """Formata bytes em KB, MB ou GB."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


class MediaExtractor:
    """
    Extrator de mídias de alta precisão para Twitter (X) e Instagram.
    Suporta vídeos (Reels/Clips) e imagens estáticas em alta qualidade.
    """

    def __init__(self):
        self.extracted_dir = EXTRACTED_DIR
        self.history_file = HISTORY_FILE
        self._ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def _load_history(self) -> list:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self, history: list):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico de extrações: {e}")

    def get_history(self) -> list:
        """Retorna histórico de mídias extraídas (mais recentes primeiro)."""
        history = self._load_history()
        # Valida se os arquivos ainda existem fisicamente
        valid_items = []
        for item in history:
            file_path = self.extracted_dir / item.get("filename", "")
            if file_path.exists():
                valid_items.append(item)
        if len(valid_items) != len(history):
            self._save_history(valid_items)
        return valid_items

    def delete_item(self, filename: str) -> bool:
        """Exclui uma mídia extraída do disco e do histórico com proteção contra path traversal."""
        safe_name = Path(filename).name
        if not safe_name:
            return False

        file_path = self.extracted_dir / safe_name
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
            except Exception:
                pass
        # Remove versão convertida em vídeo se existir
        video_version = self.extracted_dir / f"video_{Path(safe_name).stem}.mp4"
        if video_version.exists() and video_version.is_file():
            try:
                video_version.unlink()
            except Exception:
                pass

        history = self._load_history()
        history = [h for h in history if h.get("filename") != safe_name]
        self._save_history(history)
        return True

    def detect_platform(self, url: str) -> str:
        """Detecta se a URL pertence ao Twitter/X ou Instagram."""
        clean_url = url.lower().strip()
        if any(d in clean_url for d in ["twitter.com", "x.com", "t.co"]):
            return "twitter"
        if any(d in clean_url for d in ["instagram.com", "instagr.am"]):
            return "instagram"
        return "unknown"

    def extract(self, url: str) -> dict:
        """
        Ponto de entrada unificado para extração de Twitter e Instagram.
        """
        url = url.strip()
        if not url:
            raise ValueError("URL não fornecida.")

        platform = self.detect_platform(url)

        if platform == "twitter":
            res = self._extract_twitter(url)
        elif platform == "instagram":
            res = self._extract_instagram(url)
        else:
            # Tenta com yt-dlp genérico
            res = self._extract_generic_ytdlp(url)

        # Registra no histórico
        history = self._load_history()
        # Remove duplicata pelo filename se houver
        history = [h for h in history if h.get("filename") != res.get("filename")]
        history.insert(0, res)
        # Limita histórico aos últimos 50 itens
        history = history[:50]
        self._save_history(history)

        return res

    # =========================================================================
    # EXTRAÇÃO TWITTER / X
    # =========================================================================

    def _extract_twitter(self, url: str) -> dict:
        logger.info(f"Iniciando extração do Twitter/X: {url}")

        # Extrai o ID do tweet da URL
        tweet_id_match = re.search(r"(?:status|statuses)/(\d+)", url)
        if not tweet_id_match:
            raise ValueError("Link do Twitter/X inválido. Não foi possível identificar o ID do post.")

        tweet_id = tweet_id_match.group(1)

        # 1. Tentar via API fxtwitter (alta velocidade e metadados completos)
        try:
            api_url = f"https://api.fxtwitter.com/status/{tweet_id}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(api_url, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                tweet = data.get("tweet", {})
                media_data = tweet.get("media", {})

                videos = media_data.get("videos", [])
                photos = media_data.get("photos", [])

                caption = tweet.get("text", "")
                author = f"@{tweet.get('author', {}).get('screen_name', '')} ({tweet.get('author', {}).get('name', '')})"
                author_avatar = tweet.get("author", {}).get("avatar_url", "")

                # Se houver vídeo
                if videos:
                    # Pega o primeiro vídeo (geralmente melhor formato)
                    v = videos[0]
                    video_url = v.get("url")
                    thumb_url = v.get("thumbnail_url", "")
                    duration_s = v.get("duration", 0)

                    filename = f"twitter_{tweet_id}_{uuid.uuid4().hex[:6]}.mp4"
                    dest_path = self.extracted_dir / filename

                    self._download_stream(video_url, dest_path)
                    filesize = dest_path.stat().st_size

                    return {
                        "id": tweet_id,
                        "platform": "twitter",
                        "media_type": "video",
                        "original_url": url,
                        "filename": filename,
                        "file_url": f"/api/extractor/file/{filename}",
                        "download_url": f"/api/extractor/download/{filename}",
                        "title": f"Vídeo do Twitter ({tweet_id})",
                        "caption": caption,
                        "author": author,
                        "author_avatar": author_avatar,
                        "thumbnail_url": thumb_url or f"/api/extractor/file/{filename}",
                        "filesize": filesize,
                        "filesize_formatted": format_bytes(filesize),
                        "duration": f"{int(duration_s)}s" if duration_s else None,
                        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }

                # Se houver foto/imagem
                elif photos:
                    p = photos[0]
                    photo_url = p.get("url")
                    ext = "jpg"
                    if ".png" in photo_url.lower():
                        ext = "png"
                    elif ".webp" in photo_url.lower():
                        ext = "webp"

                    filename = f"twitter_{tweet_id}_{uuid.uuid4().hex[:6]}.{ext}"
                    dest_path = self.extracted_dir / filename

                    self._download_stream(photo_url, dest_path)
                    filesize = dest_path.stat().st_size

                    return {
                        "id": tweet_id,
                        "platform": "twitter",
                        "media_type": "image",
                        "original_url": url,
                        "filename": filename,
                        "file_url": f"/api/extractor/file/{filename}",
                        "download_url": f"/api/extractor/download/{filename}",
                        "title": f"Imagem do Twitter ({tweet_id})",
                        "caption": caption,
                        "author": author,
                        "author_avatar": author_avatar,
                        "thumbnail_url": f"/api/extractor/file/{filename}",
                        "filesize": filesize,
                        "filesize_formatted": format_bytes(filesize),
                        "duration": None,
                        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }

                else:
                    raise ValueError("Este post do Twitter/X não contém mídias de vídeo ou imagem para extração.")
        except Exception as e:
            logger.warning(f"Falha na API fxtwitter: {e}. Tentando fallback via yt-dlp...")

        # 2. Fallback via yt-dlp
        return self._extract_generic_ytdlp(url, platform_name="twitter", default_id=tweet_id)

    # =========================================================================
    # EXTRAÇÃO INSTAGRAM
    # =========================================================================

    def _extract_instagram(self, url: str) -> dict:
        logger.info(f"Iniciando extração do Instagram: {url}")

        # Extrai código do post ou reel (ex: DCrWnSgOGsU)
        code_match = re.search(r"/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", url)
        if not code_match:
            raise ValueError("Link do Instagram inválido. Certifique-se de que é um link de Reel ou Post.")

        shortcode = code_match.group(1)

        # 1. Estratégia Principal: Instagrapi Client Autenticado
        try:
            cl = instagram_service.get_client()
            pk = cl.media_pk_from_code(shortcode)

            # Tenta media_info e media_info_v1
            media = None
            try:
                media = cl.media_info(pk)
            except Exception:
                media = cl.media_info_v1(pk)

            if media:
                caption = media.caption_text or ""
                author = f"@{media.user.username} ({media.user.full_name or ''})".strip()
                author_avatar = str(media.user.profile_pic_url or "")
                thumb_url = str(media.thumbnail_url or "")

                # Se for vídeo (Reel / Vídeo Feed)
                if media.media_type == 2 or getattr(media, "video_url", None):
                    video_url = str(media.video_url)
                    filename = f"instagram_{shortcode}_{uuid.uuid4().hex[:6]}.mp4"
                    dest_path = self.extracted_dir / filename

                    self._download_stream(video_url, dest_path)
                    filesize = dest_path.stat().st_size
                    duration_s = getattr(media, "video_duration", None)

                    return {
                        "id": shortcode,
                        "platform": "instagram",
                        "media_type": "video",
                        "original_url": url,
                        "filename": filename,
                        "file_url": f"/api/extractor/file/{filename}",
                        "download_url": f"/api/extractor/download/{filename}",
                        "title": f"Reel/Vídeo Instagram ({shortcode})",
                        "caption": caption,
                        "author": author,
                        "author_avatar": author_avatar,
                        "thumbnail_url": thumb_url or f"/api/extractor/file/{filename}",
                        "filesize": filesize,
                        "filesize_formatted": format_bytes(filesize),
                        "duration": f"{int(duration_s)}s" if duration_s else None,
                        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }

                # Se for foto / imagem (media_type == 1)
                elif media.media_type == 1 or thumb_url:
                    img_url = thumb_url
                    filename = f"instagram_{shortcode}_{uuid.uuid4().hex[:6]}.jpg"
                    dest_path = self.extracted_dir / filename

                    self._download_stream(img_url, dest_path)
                    filesize = dest_path.stat().st_size

                    return {
                        "id": shortcode,
                        "platform": "instagram",
                        "media_type": "image",
                        "original_url": url,
                        "filename": filename,
                        "file_url": f"/api/extractor/file/{filename}",
                        "download_url": f"/api/extractor/download/{filename}",
                        "title": f"Foto/Post Instagram ({shortcode})",
                        "caption": caption,
                        "author": author,
                        "author_avatar": author_avatar,
                        "thumbnail_url": f"/api/extractor/file/{filename}",
                        "filesize": filesize,
                        "filesize_formatted": format_bytes(filesize),
                        "duration": None,
                        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
        except Exception as e:
            logger.warning(f"Instagrapi não conseguiu extrair diretamente ({e}). Tentando fallback via yt-dlp...")

        # 2. Fallback via yt-dlp
        return self._extract_generic_ytdlp(url, platform_name="instagram", default_id=shortcode)

    # =========================================================================
    # FALLBACK GENÉRICO COM YT-DLP
    # =========================================================================

    def _extract_generic_ytdlp(self, url: str, platform_name: str = "generic", default_id: str = None) -> dict:
        unique_id = default_id or uuid.uuid4().hex[:8]
        out_tmpl = str(self.extracted_dir / f"{platform_name}_{unique_id}_%(id)s.%(ext)s")

        ydl_opts = {
            "outtmpl": out_tmpl,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise RuntimeError("Nenhuma informação de mídia retornada pelo extrator.")

                # Se houver entries (playlist), pega a primeira
                if "entries" in info:
                    info = info["entries"][0]

                downloaded_file = Path(ydl.prepare_filename(info))
                # Se mergeou para mp4
                if not downloaded_file.exists():
                    mp4_candidate = downloaded_file.with_suffix(".mp4")
                    if mp4_candidate.exists():
                        downloaded_file = mp4_candidate

                if not downloaded_file.exists():
                    # Procura na pasta por arquivos criados nos últimos segundos
                    recent_files = sorted(
                        self.extracted_dir.glob(f"{platform_name}_{unique_id}*"),
                        key=os.path.getmtime,
                        reverse=True
                    )
                    if recent_files:
                        downloaded_file = recent_files[0]
                    else:
                        raise FileNotFoundError("O arquivo extraído não foi localizado no disco.")

                ext = downloaded_file.suffix.lower()
                is_video = ext in [".mp4", ".mov", ".mkv", ".webm"]
                media_type = "video" if is_video else "image"
                filesize = downloaded_file.stat().st_size
                duration_s = info.get("duration")

                return {
                    "id": unique_id,
                    "platform": platform_name,
                    "media_type": media_type,
                    "original_url": url,
                    "filename": downloaded_file.name,
                    "file_url": f"/api/extractor/file/{downloaded_file.name}",
                    "download_url": f"/api/extractor/download/{downloaded_file.name}",
                    "title": info.get("title") or f"Mídia extraída ({platform_name})",
                    "caption": info.get("description") or info.get("title") or "",
                    "author": info.get("uploader") or info.get("channel") or platform_name.capitalize(),
                    "author_avatar": None,
                    "thumbnail_url": info.get("thumbnail") or f"/api/extractor/file/{downloaded_file.name}",
                    "filesize": filesize,
                    "filesize_formatted": format_bytes(filesize),
                    "duration": f"{int(duration_s)}s" if duration_s else None,
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"Erro no extrator yt-dlp: {e}")
            raise RuntimeError(f"Não foi possível extrair a mídia do link fornecido: {e}")

    # =========================================================================
    # CONVERSÃO DE IMAGEM ESTÁTICA EM VÍDEO VERTICAL 9:16 (1080x1920)
    # =========================================================================

    def convert_image_to_video(self, image_filename: str, duration: int = 5) -> dict:
        """
        Converte uma imagem estática (extraída do Twitter/Instagram) em um vídeo
        vertical 1080x1920 .mp4 de 5 segundos pronto para Reels, TikTok, Kwai e Stories.
        """
        safe_name = Path(image_filename).name
        img_path = self.extracted_dir / safe_name
        if not img_path.exists():
            # Tenta na pasta raiz de uploads
            img_path = Path(config.UPLOAD_FOLDER) / safe_name
            if not img_path.exists():
                raise FileNotFoundError(f"Imagem não encontrada: {safe_name}")

        out_filename = f"video_{img_path.stem}.mp4"
        out_path = self.extracted_dir / out_filename

        # Se já foi gerado antes, retorna direto
        if out_path.exists():
            filesize = out_path.stat().st_size
            return {
                "filename": out_filename,
                "file_url": f"/api/extractor/file/{out_filename}",
                "download_url": f"/api/extractor/download/{out_filename}",
                "filesize_formatted": format_bytes(filesize),
                "duration": f"{duration}s"
            }

        cmd = [
            self._ffmpeg_exe,
            "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black",
            str(out_path)
        ]

        logger.info(f"Convertendo imagem para vídeo 9:16 vertical via FFmpeg: {out_filename}")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            logger.error(f"Erro ao converter imagem em vídeo: {proc.stderr.decode('utf-8', errors='ignore')}")
            raise RuntimeError("Falha na renderização de vídeo da imagem.")

        filesize = out_path.stat().st_size
        return {
            "filename": out_filename,
            "file_url": f"/api/extractor/file/{out_filename}",
            "download_url": f"/api/extractor/download/{out_filename}",
            "filesize_formatted": format_bytes(filesize),
            "duration": f"{duration}s"
        }

    # =========================================================================
    # HELPER DE DOWNLOAD STREAM
    # =========================================================================

    def _download_stream(self, url: str, target_path: Path):
        """Baixa arquivo via HTTP stream em chunks com tratamento de headers."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)


media_extractor = MediaExtractor()
