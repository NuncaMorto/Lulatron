import os
import json
import logging
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

import config
from social_publisher import social_publisher

logger = logging.getLogger("SchedulerService")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [Scheduler] %(message)s"))
    logger.addHandler(ch)

HISTORY_FILE = config.BASE_DIR / "posts_history.json"


def record_history_entry(entry: dict):
    """Registra histórico de execuções em arquivo JSON local."""
    try:
        history = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        history.insert(0, entry)
        history = history[:150]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erro ao registrar histórico: {e}")


def execute_scheduled_post(job_id: str, video_path: str, caption: str, platforms):
    """
    Função chamada pelo APScheduler em background.
    Executa a postagem multi-plataforma (Instagram, TikTok, Facebook, Kwai) sem travar o servidor.
    """
    if isinstance(platforms, str):
        platforms = [platforms]

    logger.info(f"==> Executando tarefa agendada: {job_id} para {platforms}")
    start_time = datetime.now().isoformat()
    try:
        result = social_publisher.publish_all(
            platforms=platforms,
            video_path=video_path,
            caption=caption
        )
        status = result.get("overall_status", "success")
        logger.info(f"Tarefa {job_id} finalizada com status [{status}]")
        record_history_entry({
            "job_id": job_id,
            "timestamp": start_time,
            "status": "success" if status in ["success", "partial"] else "failed",
            "overall_status": status,
            "platforms": platforms,
            "destination": ", ".join(platforms),
            "video_path": video_path,
            "caption": caption,
            "details": result
        })
        return result
    except Exception as e:
        logger.error(f"Falha crítica na tarefa agendada {job_id}: {e}", exc_info=True)
        record_history_entry({
            "job_id": job_id,
            "timestamp": start_time,
            "status": "failed",
            "platforms": platforms,
            "destination": ", ".join(platforms),
            "video_path": video_path,
            "caption": caption,
            "error": str(e)
        })


class SchedulerManager:
    """
    Gerenciador do APScheduler com persistência em SQLite.
    Garante que os agendamentos resistam a reboots e reinicializações na VPS.
    """

    def __init__(self):
        jobstores = {
            "default": SQLAlchemyJobStore(url=config.DATABASE_URL)
        }
        executors = {
            "default": ThreadPoolExecutor(max_workers=4)
        }
        job_defaults = {
            "coalesce": False,
            "max_instances": 1,
            "misfire_grace_time": 600
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler inicializado com sucesso.")

    def schedule_once(self, job_id: str, run_date: datetime, video_path: str, caption: str, platforms):
        job = self.scheduler.add_job(
            execute_scheduled_post,
            trigger="date",
            run_date=run_date,
            id=job_id,
            name=f"Post [{', '.join(platforms)}] [{job_id}]",
            args=[job_id, video_path, caption, platforms],
            replace_existing=True
        )
        logger.info(f"Postagem única agendada [{job_id}] para {run_date}")
        return job

    def schedule_recurring_daily(self, job_id: str, hour: int, minute: int, video_path: str, caption: str, platforms):
        job = self.scheduler.add_job(
            execute_scheduled_post,
            trigger="cron",
            hour=hour,
            minute=minute,
            id=job_id,
            name=f"Recorrente [{', '.join(platforms)}] {hour:02d}:{minute:02d} [{job_id}]",
            args=[job_id, video_path, caption, platforms],
            replace_existing=True
        )
        logger.info(f"Postagem diária agendada [{job_id}] às {hour:02d}:{minute:02d}")
        return job

    def list_jobs(self) -> list:
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time.strftime("%d/%m/%Y %H:%M:%S") if job.next_run_time else "N/A"
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": next_run,
                "trigger": str(job.trigger)
            })
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.remove_job(job_id)
            logger.info(f"Agendamento [{job_id}] cancelado com sucesso.")
            return True
        return False

    def get_history(self) -> list:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []


# Instância global do agendador
scheduler_manager = SchedulerManager()
