import os
import re
import time
import json
import uuid
import random
import string
import hmac
import requests
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response, send_from_directory
from werkzeug.utils import secure_filename

import config
from scheduler_service import scheduler_manager
from social_publisher import social_publisher
from instagram_bot import instagram_service
from platforms.facebook_service import facebook_service
from platforms.tiktok_service import tiktok_service
from platforms.kwai_service import kwai_service
from env_manager import read_env_file, update_env_file
from media_extractor import media_extractor

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.permanent_session_lifetime = timedelta(days=7)

# Inicia o agendador em background
scheduler_manager.start()

# Arquivo do cofre de contas
ACCOUNTS_VAULT_FILE = config.BASE_DIR / "accounts_vault.json"

# Proteção contra força bruta em memória
LOGIN_ATTEMPTS = {}


def check_rate_limit(ip: str) -> bool:
    now = time.time()
    record = LOGIN_ATTEMPTS.get(ip)
    if not record:
        LOGIN_ATTEMPTS[ip] = {"attempts": 1, "first_attempt": now}
        return True

    if now - record["first_attempt"] > 600:
        LOGIN_ATTEMPTS[ip] = {"attempts": 1, "first_attempt": now}
        return True

    record["attempts"] += 1
    return record["attempts"] <= 5


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Acesso não autorizado. Faça login primeiro."}), 401
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


# --- Funções do Cofre de Contas ---

def load_accounts_vault() -> list:
    if ACCOUNTS_VAULT_FILE.exists():
        try:
            with open(ACCOUNTS_VAULT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_accounts_vault(accounts: list):
    with open(ACCOUNTS_VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)


def generate_secure_password(length=14) -> str:
    """Gera senha forte com letras maiúsculas, minúsculas, números e caracteres especiais."""
    chars_upper = string.ascii_uppercase
    chars_lower = string.ascii_lowercase
    chars_digits = string.digits
    chars_symbols = "@#$!%*&"

    pwd = [
        random.choice(chars_upper),
        random.choice(chars_lower),
        random.choice(chars_digits),
        random.choice(chars_symbols)
    ]
    all_chars = chars_upper + chars_lower + chars_digits + chars_symbols
    pwd += [random.choice(all_chars) for _ in range(length - 4)]
    random.shuffle(pwd)
    return "".join(pwd)


# --- Rotas de Autenticação Segura ---

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    client_ip = request.remote_addr or "127.0.0.1"

    if request.method == "POST":
        if not check_rate_limit(client_ip):
            return render_template("login.html", error="Muitas tentativas falhas. Bloqueado temporariamente por 10 minutos."), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user_ok = hmac.compare_digest(username.encode("utf-8"), str(config.DASHBOARD_USERNAME).encode("utf-8"))
        pass_ok = hmac.compare_digest(password.encode("utf-8"), str(config.DASHBOARD_PASSWORD).encode("utf-8"))

        if user_ok and pass_ok:
            session.permanent = True
            session["logged_in"] = True
            session["user"] = username
            LOGIN_ATTEMPTS.pop(client_ip, None)
            return redirect(url_for("index"))
        else:
            error = "Usuário ou senha incorretos."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --- Rotas do Painel Web ---

@app.route("/")
@login_required
def index():
    return render_template("index.html", user=session.get("user"))


@app.route("/api/schedule", methods=["POST"])
@api_login_required
def schedule_post():
    caption = request.form.get("caption", "").strip()
    schedule_mode = request.form.get("schedule_mode", "now").strip().lower()

    platforms = request.form.getlist("platforms")
    if not platforms:
        single_dest = request.form.get("destination", "instagram_reels")
        platforms = [single_dest]

    save_path = None
    existing_name = request.form.get("existing_media_filename", "").strip()

    if existing_name:
        clean_name = secure_filename(existing_name)
        candidate_extracted = media_extractor.extracted_dir / clean_name
        candidate_upload = Path(config.UPLOAD_FOLDER) / clean_name

        if candidate_extracted.exists():
            target_file = candidate_extracted
        elif candidate_upload.exists():
            target_file = candidate_upload
        else:
            return jsonify({"error": f"Arquivo de mídia '{existing_name}' não encontrado no servidor."}), 400

        # Se for imagem, converte para vídeo vertical 9:16 para compatibilidade total com as redes
        ext = target_file.suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            conv = media_extractor.convert_image_to_video(target_file.name)
            save_path = media_extractor.extracted_dir / conv["filename"]
        else:
            save_path = target_file
    elif "video" in request.files:
        file = request.files["video"]
        if file.filename == "":
            return jsonify({"error": "Nome do arquivo vazio."}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Formato inválido. Envie um arquivo de vídeo ou imagem compatível."}), 400

        original_name = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{original_name}"
        save_path = Path(config.UPLOAD_FOLDER) / unique_filename
        file.save(str(save_path))

        # Se for imagem enviada pelo dropzone, converte para vídeo 9:16
        if save_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            conv = media_extractor.convert_image_to_video(save_path.name)
            save_path = media_extractor.extracted_dir / conv["filename"]
    else:
        return jsonify({"error": "Nenhum arquivo de vídeo ou mídia foi enviado/selecionado."}), 400

    created_jobs = []

    try:
        if schedule_mode == "now":
            run_date = datetime.now() + timedelta(seconds=2)
            job_id = f"now_{uuid.uuid4().hex[:6]}"
            scheduler_manager.schedule_once(
                job_id=job_id,
                run_date=run_date,
                video_path=str(save_path),
                caption=caption,
                platforms=platforms
            )
            created_jobs.append({"id": job_id, "type": "imediato", "info": f"Disparando para {', '.join(platforms)}"})

        elif schedule_mode == "once":
            dt_str = request.form.get("schedule_datetime")
            if not dt_str:
                return jsonify({"error": "Data e hora não especificadas."}), 400

            run_date = datetime.fromisoformat(dt_str)
            if run_date < datetime.now():
                return jsonify({"error": "O horário de agendamento deve ser no futuro."}), 400

            job_id = f"once_{uuid.uuid4().hex[:6]}"
            scheduler_manager.schedule_once(
                job_id=job_id,
                run_date=run_date,
                video_path=str(save_path),
                caption=caption,
                platforms=platforms
            )
            created_jobs.append({
                "id": job_id,
                "type": "único",
                "run_date": run_date.strftime("%d/%m/%Y às %H:%M")
            })

        elif schedule_mode == "daily":
            times_str = request.form.get("daily_times", "")
            if not times_str:
                return jsonify({"error": "Informe pelo menos um horário diário (ex: 10:00, 18:30)."}), 400

            time_list = [t.strip() for t in times_str.split(",") if t.strip()]
            for t in time_list:
                parts = t.split(":")
                if len(parts) != 2:
                    continue
                hour, minute = int(parts[0]), int(parts[1])
                job_id = f"daily_{hour:02d}{minute:02d}_{uuid.uuid4().hex[:4]}"
                scheduler_manager.schedule_recurring_daily(
                    job_id=job_id,
                    hour=hour,
                    minute=minute,
                    video_path=str(save_path),
                    caption=caption,
                    platforms=platforms
                )
                created_jobs.append({
                    "id": job_id,
                    "type": "diário recorrente",
                    "time": f"{hour:02d}:{minute:02d}"
                })

        return jsonify({
            "message": "Agendamento registrado com sucesso!",
            "platforms": platforms,
            "jobs": created_jobs
        }), 201

    except Exception as e:
        return jsonify({"error": f"Erro ao processar agendamento: {str(e)}"}), 500


@app.route("/api/jobs", methods=["GET"])
@api_login_required
def get_jobs():
    jobs = scheduler_manager.list_jobs()
    return jsonify({"jobs": jobs})


@app.route("/api/jobs/<job_id>", methods=["DELETE"])
@api_login_required
def cancel_job(job_id):
    success = scheduler_manager.cancel_job(job_id)
    if success:
        return jsonify({"message": f"Agendamento {job_id} cancelado."})
    return jsonify({"error": f"Agendamento não encontrado."}), 404


@app.route("/api/history", methods=["GET"])
@api_login_required
def get_history():
    history = scheduler_manager.get_history()
    return jsonify({"history": history})


@app.route("/api/platforms-status", methods=["GET"])
@api_login_required
def platforms_status():
    status = social_publisher.check_all_health()
    return jsonify(status)


# --- APIs de Conexão e Gerenciamento de Contas (.env dinâmico) ---

@app.route("/api/connections", methods=["GET"])
@api_login_required
def get_connections():
    """Retorna o status atual e dados mascarados das credenciais conectadas."""
    env_data = read_env_file()
    health = social_publisher.check_all_health()

    return jsonify({
        "instagram": {
            "username": env_data.get("IG_USERNAME", ""),
            "has_password": bool(env_data.get("IG_PASSWORD")),
            "proxy": env_data.get("IG_PROXY", ""),
            "totp_seed": env_data.get("IG_TOTP_SEED", ""),
            "status": health.get("instagram", {})
        },
        "facebook": {
            "page_id": env_data.get("FB_PAGE_ID", ""),
            "access_token": env_data.get("FB_PAGE_ACCESS_TOKEN", ""),
            "status": health.get("facebook", {})
        },
        "tiktok": {
            "access_token": env_data.get("TIKTOK_ACCESS_TOKEN", ""),
            "session_id": env_data.get("TIKTOK_SESSION_ID", ""),
            "proxy": env_data.get("TIKTOK_PROXY", ""),
            "status": health.get("tiktok", {})
        },
        "kwai": {
            "app_id": env_data.get("KWAI_APP_ID", ""),
            "access_token": env_data.get("KWAI_ACCESS_TOKEN", ""),
            "proxy": env_data.get("KWAI_PROXY", ""),
            "status": health.get("kwai", {})
        }
    })


@app.route("/api/connections/instagram", methods=["POST"])
@api_login_required
def connect_instagram():
    """Conecta e valida a conta do Instagram, salvando a sessão e atualizando o .env."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    proxy = data.get("proxy", "").strip()
    totp_seed = data.get("totp_seed", "").strip()
    verification_code = data.get("verification_code", "").strip()

    env_data = read_env_file()
    if not password:
        password = env_data.get("IG_PASSWORD", "")

    if not username or not password:
        return jsonify({"error": "Usuário e senha são obrigatórios para conectar o Instagram."}), 400

    result = instagram_service.test_and_save_session(
        username=username,
        password=password,
        proxy=proxy if proxy else None,
        totp_seed=totp_seed if totp_seed else None,
        verification_code=verification_code if verification_code else None
    )

    if result.get("status") == "connected":
        update_env_file({
            "IG_USERNAME": username,
            "IG_PASSWORD": password,
            "IG_PROXY": proxy,
            "IG_TOTP_SEED": totp_seed
        })
        instagram_service.reload_credentials(username, password, proxy, totp_seed)
        return jsonify({
            "message": f"Instagram conectado com sucesso como @{username}!",
            "status": result
        })
    elif result.get("status") in ["2fa_required", "challenge_required"]:
        return jsonify(result), 200
    else:
        return jsonify({"error": result.get("message", "Falha na autenticação do Instagram.")}), 400


@app.route("/api/connections/instagram/disconnect", methods=["POST"])
@api_login_required
def disconnect_instagram():
    """Desconecta o Instagram e apaga a sessão salva."""
    instagram_service.disconnect()
    update_env_file({
        "IG_USERNAME": "",
        "IG_PASSWORD": "",
        "IG_PROXY": "",
        "IG_TOTP_SEED": ""
    })
    return jsonify({"message": "Conta do Instagram desconectada e sessão limpa com sucesso."})


@app.route("/api/connections/facebook", methods=["POST"])
@api_login_required
def connect_facebook():
    """Atualiza as credenciais do Facebook Page / Meta Graph API."""
    data = request.get_json() or {}
    page_id = data.get("page_id", "").strip()
    access_token = data.get("access_token", "").strip()

    update_env_file({
        "FB_PAGE_ID": page_id,
        "FB_PAGE_ACCESS_TOKEN": access_token
    })
    facebook_service.reload_credentials(page_id, access_token)
    health = facebook_service.check_health()
    return jsonify({
        "message": "Configurações do Facebook salvas com sucesso!",
        "status": health
    })


@app.route("/api/connections/tiktok", methods=["POST"])
@api_login_required
def connect_tiktok():
    """Atualiza credenciais do TikTok."""
    data = request.get_json() or {}
    access_token = data.get("access_token", "").strip()
    session_id = data.get("session_id", "").strip()
    proxy = data.get("proxy", "").strip()

    update_env_file({
        "TIKTOK_ACCESS_TOKEN": access_token,
        "TIKTOK_SESSION_ID": session_id,
        "TIKTOK_PROXY": proxy
    })
    tiktok_service.reload_credentials(access_token, session_id, proxy)
    health = tiktok_service.check_health()
    return jsonify({
        "message": "Configurações do TikTok salvas com sucesso!",
        "status": health
    })


@app.route("/api/connections/kwai", methods=["POST"])
@api_login_required
def connect_kwai():
    """Atualiza credenciais do Kwai."""
    data = request.get_json() or {}
    app_id = data.get("app_id", "").strip()
    access_token = data.get("access_token", "").strip()
    proxy = data.get("proxy", "").strip()

    update_env_file({
        "KWAI_APP_ID": app_id,
        "KWAI_ACCESS_TOKEN": access_token,
        "KWAI_PROXY": proxy
    })
    kwai_service.reload_credentials(app_id, access_token, proxy)
    health = kwai_service.check_health()
    return jsonify({
        "message": "Configurações do Kwai salvas com sucesso!",
        "status": health
    })


# --- APIs do Gerador & Cofre de Contas (Lulatron Vault) ---

DOMAINS_CACHE = {"timestamp": 0, "domains": []}


def get_live_domains():
    """
    Busca domínios ativos e funcionais que NÃO são bloqueados pelo Instagram/TikTok/Facebook.
    Utiliza Mail.tm API, Generator.email e fallbacks selecionados.
    """
    now = time.time()
    if DOMAINS_CACHE["domains"] and (now - DOMAINS_CACHE["timestamp"] < 300):
        return DOMAINS_CACHE["domains"]

    domains = []

    # 1. Mail.tm - Domínios limpos com API REST oficial
    try:
        r_tm = requests.get("https://api.mail.tm/domains", timeout=5)
        if r_tm.status_code == 200:
            for item in r_tm.json().get("hydra:member", []):
                d = item.get("domain", "").strip().lower()
                if d and not any(x["domain"] == d for x in domains):
                    domains.append({
                        "domain": d,
                        "provider": "mail.tm",
                        "label": f"{d} (Mail.tm - Recomendado)",
                        "recommended": True
                    })
    except Exception:
        pass

    # 2. Generator.email - Domínios rotativos aceitos pelas redes sociais
    try:
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://generator.email/",
            "Origin": "https://generator.email"
        })
        r_gen = s.get("https://generator.email/", timeout=5)
        token_match = re.search(r'name="api-token" content="([^"]+)"', r_gen.text)
        if token_match:
            s.headers.update({"X-API-Token": token_match.group(1), "X-Requested-With": "XMLHttpRequest"})
            r_dom = s.get("https://generator.email/api/domains.php", timeout=5)
            if r_dom.status_code == 200:
                for item in r_dom.json():
                    d = item.get("ascii", "").strip().lower()
                    if d and not any(x["domain"] == d for x in domains):
                        domains.append({
                            "domain": d,
                            "provider": "generator.email",
                            "label": f"{d} (Generator)",
                            "recommended": False
                        })

        cur_doms = re.findall(r'cur_domain:"([^"]+)"', r_gen.text)
        for cd in cur_doms:
            cd = cd.strip().lower()
            if cd and not any(x["domain"] == cd for x in domains):
                domains.append({
                    "domain": cd,
                    "provider": "generator.email",
                    "label": f"{cd} (Generator)",
                    "recommended": False
                })
    except Exception:
        pass

    # 3. Fallbacks garantidos sem risco de "email not supported"
    fallbacks = [
        {"domain": "maxxspace.com", "provider": "mail.tm", "label": "maxxspace.com (Mail.tm - Recomendado)", "recommended": True},
        {"domain": "makeraura.online", "provider": "generator.email", "label": "makeraura.online (Generator)", "recommended": False},
        {"domain": "gmailedu.us", "provider": "generator.email", "label": "gmailedu.us (Generator)", "recommended": False},
        {"domain": "bananacompany.us", "provider": "generator.email", "label": "bananacompany.us (Generator)", "recommended": False},
        {"domain": "laptoplonghai.com", "provider": "generator.email", "label": "laptoplonghai.com (Generator)", "recommended": False},
        {"domain": "ahmadfamily.net", "provider": "generator.email", "label": "ahmadfamily.net (Generator)", "recommended": False},
        {"domain": "nightfood.studio", "provider": "generator.email", "label": "nightfood.studio (Generator)", "recommended": False},
    ]
    for fb in fallbacks:
        if not any(x["domain"] == fb["domain"] for x in domains):
            domains.append(fb)

    DOMAINS_CACHE["timestamp"] = now
    DOMAINS_CACHE["domains"] = domains
    return domains


@app.route("/api/accounts/domains", methods=["GET"])
@api_login_required
def get_available_domains():
    """Retorna lista de domínios ativos e recomendados para gerar e-mails."""
    refresh = request.args.get("refresh", "false").lower() == "true"
    if refresh:
        DOMAINS_CACHE["timestamp"] = 0
    domains = get_live_domains()
    recommended = next((d["domain"] for d in domains if d.get("recommended")), "maxxspace.com")
    return jsonify({
        "domains": domains,
        "recommended": recommended,
        "total": len(domains)
    })


@app.route("/api/accounts", methods=["GET"])
@api_login_required
def get_accounts():
    accounts = load_accounts_vault()
    return jsonify({"accounts": accounts, "total": len(accounts)})


@app.route("/api/accounts/generate", methods=["POST"])
@api_login_required
def generate_accounts():
    data = request.get_json() or {}
    qty = min(max(int(data.get("quantity", 5)), 1), 50)
    prefix = (data.get("prefix") or "lulatron").strip().lower()
    domain = (data.get("domain") or "maxxspace.com").strip().lower()

    nomes_base = ["esperanca", "brasil", "estrela", "povo", "democracia", "uniao", "futuro", "trabalho", "vencer", "paz"]
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    vault = load_accounts_vault()
    new_accounts = []

    is_mailtm = (domain == "maxxspace.com") or any(d["domain"] == domain and d["provider"] == "mail.tm" for d in get_live_domains())

    for _ in range(qty):
        rand_num = random.randint(1000, 99999)
        rand_word = random.choice(nomes_base)
        
        username = f"{prefix}_{rand_word}_{rand_num}"
        email = f"{prefix}.{rand_word}{rand_num}@{domain}"
        password = generate_secure_password(length=14)

        provider = "mail.tm" if is_mailtm else "generator.email"
        mailtm_registered = False

        if is_mailtm:
            try:
                r_reg = requests.post(
                    "https://api.mail.tm/accounts",
                    json={"address": email, "password": password},
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                if r_reg.status_code in [200, 201]:
                    mailtm_registered = True
            except Exception:
                pass

        account_entry = {
            "id": f"acc_{uuid.uuid4().hex[:8]}",
            "username": username,
            "email": email,
            "password": password,
            "created_at": now_str,
            "status": "pronta_para_cadastro",
            "platforms": ["Instagram", "TikTok", "Facebook", "Kwai"],
            "provider": provider,
            "mailtm_registered": mailtm_registered,
            "domain": domain,
            "notes": "Gerada pelo Lulatron (Compatível com OTP)"
        }
        vault.insert(0, account_entry)
        new_accounts.append(account_entry)

    save_accounts_vault(vault)
    return jsonify({
        "message": f"{qty} contas geradas com sucesso para o domínio @{domain}!",
        "generated": new_accounts,
        "total_vault": len(vault)
    }), 201


@app.route("/api/accounts/<account_id>", methods=["DELETE"])
@api_login_required
def delete_account(account_id):
    vault = load_accounts_vault()
    filtered = [acc for acc in vault if acc.get("id") != account_id]
    if len(filtered) != len(vault):
        save_accounts_vault(filtered)
        return jsonify({"message": "Conta removida do cofre com sucesso."})
    return jsonify({"error": "Conta não encontrada."}), 404


@app.route("/api/accounts/clear", methods=["DELETE"])
@api_login_required
def clear_accounts():
    save_accounts_vault([])
    return jsonify({"message": "Todas as contas foram limpas do cofre."})


@app.route("/api/accounts/export/txt", methods=["GET"])
@api_login_required
def export_accounts_txt():
    """Gera arquivo .txt formatado para download direto."""
    vault = load_accounts_vault()
    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    lines = [
        "=" * 78,
        "  LULATRON - COFRE DE CONTAS E CREDENCIAIS DAS REDES SOCIAIS",
        f"  Exportado em: {now_str}  |  Total de Contas: {len(vault)}",
        "=" * 78,
        "",
        "Instruções:",
        "- Cada e-mail e senha abaixo podem ser usados para cadastrar perfis",
        "  no Instagram, TikTok, Facebook e Kwai.",
        "- Utilize a função 'Ler E-mails' no Lulatron para capturar códigos de 6 dígitos.",
        "",
        "-" * 78,
    ]

    for idx, acc in enumerate(vault, 1):
        lines.append(f"CONTA #{idx:02d}")
        lines.append(f"  Usuário:   {acc.get('username')}")
        lines.append(f"  E-mail:    {acc.get('email')}")
        lines.append(f"  Senha:     {acc.get('password')}")
        lines.append(f"  Redes:     {', '.join(acc.get('platforms', []))}")
        lines.append(f"  Criado em: {acc.get('created_at')}")
        lines.append("-" * 78)

    content = "\n".join(lines)
    return Response(
        content,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment;filename=contas_lulatron.txt"}
    )


# --- API de Consulta de E-mails e Códigos de 6 Dígitos (Temp Mail Inbox) ---

@app.route("/api/accounts/inbox", methods=["GET"])
@api_login_required
def check_inbox():
    """
    Busca mensagens e extrai automaticamente códigos de 6 dígitos do Instagram, TikTok, etc.
    Suporta Mail.tm API oficial, Generator.email e fallback 1secmail.
    """
    email = request.args.get("email", "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "E-mail inválido."}), 400

    login, domain = email.split("@", 1)
    messages = []
    vault = load_accounts_vault()
    account = next((acc for acc in vault if acc.get("email", "").lower() == email), None)

    password = account.get("password") if account else None
    provider = account.get("provider") if account else ("mail.tm" if domain == "maxxspace.com" else "generator.email")

    generator_url = f"https://generator.email/{domain}/{login}"

    # 1. Se for Mail.tm (ex: maxxspace.com)
    if provider == "mail.tm" or domain == "maxxspace.com":
        if password:
            try:
                r_tok = requests.post(
                    "https://api.mail.tm/token",
                    json={"address": email, "password": password},
                    headers={"Content-Type": "application/json"},
                    timeout=6
                )
                if r_tok.status_code == 200:
                    token = r_tok.json().get("token")
                    r_msg = requests.get(
                        "https://api.mail.tm/messages",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=6
                    )
                    if r_msg.status_code == 200:
                        msg_list = r_msg.json().get("hydra:member", [])
                        for item in msg_list[:10]:
                            m_id = item.get("id")
                            r_det = requests.get(
                                f"https://api.mail.tm/messages/{m_id}",
                                headers={"Authorization": f"Bearer {token}"},
                                timeout=6
                            )
                            if r_det.status_code == 200:
                                d_data = r_det.json()
                                full_text = f"{d_data.get('subject', '')} {d_data.get('text', '')} {d_data.get('intro', '')}"
                                code_match = re.search(r'\b(\d{6})\b', full_text)
                                otp_code = code_match.group(1) if code_match else None
                                
                                messages.append({
                                    "id": m_id,
                                    "from": d_data.get("from", {}).get("address", "Desconhecido"),
                                    "subject": d_data.get("subject", "(Sem assunto)"),
                                    "date": d_data.get("createdAt", ""),
                                    "code": otp_code,
                                    "body": (d_data.get("text") or d_data.get("intro") or "")[:400]
                                })
            except Exception:
                pass

    # 2. Se for Generator.email (ou se não encontrou mensagens no Mail.tm)
    if not messages:
        try:
            s = requests.Session()
            s.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://generator.email/",
                "Origin": "https://generator.email"
            })
            s.cookies.set("inbox_ctx", f"{domain}%2F{login}%2F", domain="generator.email")
            
            gen_resp = s.get(generator_url, timeout=7)
            if gen_resp.status_code == 200:
                html = gen_resp.text
                codes = re.findall(r'\b(\d{6})\b', html)
                valid_codes = [c for c in codes if c not in ["100000", "000000", "123456"]]
                if valid_codes:
                    messages.append({
                        "id": "gen_otp",
                        "from": "generator.email",
                        "subject": f"Código recebido para {email}",
                        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "code": valid_codes[0],
                        "body": f"Código de confirmação de 6 dígitos capturado: {valid_codes[0]}"
                    })
        except Exception:
            pass

    # 3. Fallback adicional para 1secmail
    if not messages and "1secmail" in domain:
        try:
            api_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
            resp = requests.get(api_url, timeout=6)
            if resp.status_code == 200:
                for item in resp.json()[:6]:
                    m_id = item.get("id")
                    d_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={m_id}"
                    d_resp = requests.get(d_url, timeout=6)
                    if d_resp.status_code == 200:
                        d_data = d_resp.json()
                        full_text = f"{d_data.get('subject', '')} {d_data.get('textBody', '')} {d_data.get('body', '')}"
                        code_match = re.search(r'\b(\d{6})\b', full_text)
                        messages.append({
                            "id": m_id,
                            "from": d_data.get("from", "Desconhecido"),
                            "subject": d_data.get("subject", "(Sem assunto)"),
                            "date": d_data.get("date", ""),
                            "code": code_match.group(1) if code_match else None,
                            "body": (d_data.get("textBody") or d_data.get("body") or "")[:400]
                        })
        except Exception:
            pass

    return jsonify({
        "email": email,
        "provider": provider,
        "total": len(messages),
        "messages": messages,
        "generator_url": generator_url,
        "mailtm_url": "https://mail.tm"
    })


# ==============================================================================
# ROTAS DO EXTRATOR DE MÍDIA (TWITTER / X & INSTAGRAM)
# ==============================================================================

@app.route("/api/extractor/extract", methods=["POST"])
@api_login_required
def api_extract_media():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Por favor, informe o link do Twitter (X) ou Instagram."}), 400

    try:
        media_data = media_extractor.extract(url)
        return jsonify({"success": True, "media": media_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/extractor/history", methods=["GET"])
@api_login_required
def api_extractor_history():
    return jsonify({"history": media_extractor.get_history()})


@app.route("/api/extractor/history/<filename>", methods=["DELETE"])
@api_login_required
def api_extractor_delete(filename):
    clean_name = secure_filename(filename)
    media_extractor.delete_item(clean_name)
    return jsonify({"success": True, "message": "Mídia removida com sucesso."})


@app.route("/api/extractor/file/<filename>", methods=["GET"])
@api_login_required
def api_extractor_file(filename):
    clean_name = secure_filename(filename)
    return send_from_directory(media_extractor.extracted_dir, clean_name)


@app.route("/api/extractor/download/<filename>", methods=["GET"])
@api_login_required
def api_extractor_download(filename):
    clean_name = secure_filename(filename)
    return send_from_directory(
        media_extractor.extracted_dir,
        clean_name,
        as_attachment=True,
        download_name=clean_name
    )


@app.route("/api/extractor/convert-to-video", methods=["POST"])
@api_login_required
def api_extractor_convert_video():
    data = request.get_json() or {}
    filename = data.get("filename", "").strip()
    if not filename:
        return jsonify({"error": "Nome do arquivo não informado."}), 400

    try:
        res = media_extractor.convert_image_to_video(secure_filename(filename))
        return jsonify({"success": True, "video": res})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    print(f"[*] Iniciando Lulatron em http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)
