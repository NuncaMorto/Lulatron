import logging
from instagram_bot import instagram_service
from platforms.facebook_service import facebook_service
from platforms.tiktok_service import tiktok_service
from platforms.kwai_service import kwai_service

logger = logging.getLogger("SocialPublisher")
logger.setLevel(logging.INFO)


class SocialPublisher:
    """
    Orquestrador unificado de publicações multi-plataforma:
    Instagram (Feed/Reels, Stories), Facebook (Page/Reels), TikTok e Kwai.
    """

    def check_all_health(self) -> dict:
        """
        Retorna o status de conexão de todas as 4 redes sociais.
        """
        return {
            "instagram": instagram_service.check_health(),
            "facebook": facebook_service.check_health(),
            "tiktok": tiktok_service.check_health(),
            "kwai": kwai_service.check_health()
        }

    def publish_single_platform(self, target: str, video_path: str, caption: str) -> dict:
        target = target.lower().strip()
        
        if target in ["instagram_reels", "instagram_feed", "feed", "reels"]:
            return instagram_service.post_video_feed_or_reels(video_path, caption)
        elif target in ["instagram_story", "story", "stories"]:
            return instagram_service.post_video_story(video_path, caption)
        elif target == "facebook":
            return facebook_service.publish_video(video_path, caption)
        elif target == "tiktok":
            return tiktok_service.publish_video(video_path, caption)
        elif target == "kwai":
            return kwai_service.publish_video(video_path, caption)
        else:
            raise ValueError(f"Plataforma desconhecida: {target}")

    def publish_all(self, platforms: list[str], video_path: str, caption: str) -> dict:
        """
        Executa a postagem nas plataformas selecionadas de forma resiliente.
        Se uma plataforma falhar, as outras continuam normalmente.
        """
        results = {}
        errors = {}

        if not platforms:
            platforms = ["instagram_reels"]

        for platform in platforms:
            try:
                logger.info(f"==> Disparando post para [{platform}]...")
                res = self.publish_single_platform(platform, video_path, caption)
                results[platform] = res
            except Exception as e:
                logger.error(f"Erro ao publicar em [{platform}]: {e}")
                errors[platform] = str(e)

        overall_success = len(results) > 0 and len(errors) == 0
        partial_success = len(results) > 0 and len(errors) > 0

        return {
            "success": overall_success or partial_success,
            "overall_status": "success" if overall_success else ("partial" if partial_success else "failed"),
            "successful_platforms": results,
            "failed_platforms": errors
        }


social_publisher = SocialPublisher()
