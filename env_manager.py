import os
import re
from pathlib import Path
import config

ENV_PATH = config.BASE_DIR / ".env"

# Chaves estritamente permitidas para alteração via Dashboard (Prevenção de Injeção de Variáveis)
ALLOWED_ENV_KEYS = {
    "IG_USERNAME",
    "IG_PASSWORD",
    "IG_PROXY",
    "IG_TOTP_SEED",
    "FB_PAGE_ID",
    "FB_PAGE_ACCESS_TOKEN",
    "TIKTOK_ACCESS_TOKEN",
    "TIKTOK_SESSION_ID",
    "TIKTOK_PROXY",
    "KWAI_APP_ID",
    "KWAI_ACCESS_TOKEN",
    "KWAI_PROXY",
    "DASHBOARD_USERNAME",
    "DASHBOARD_PASSWORD",
    "HOST",
    "PORT",
}


def read_env_file() -> dict:
    """Lê todas as variáveis do arquivo .env em um dicionário de forma segura."""
    data = {}
    if not ENV_PATH.exists():
        return data

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                clean_key = key.strip()
                clean_val = val.strip().strip('"').strip("'")
                data[clean_key] = clean_val
    return data


def update_env_file(updates: dict):
    """
    Atualiza as variáveis no arquivo .env mantendo os comentários e a formatação existente.
    Higieniza quebras de linha (CRLF Injection) e valida contra chaves permitidas.
    Atualiza também os.environ e as variáveis correspondentes no módulo config.
    """
    # Filtra e higieniza chaves e valores
    sanitized_updates = {}
    for key, val in updates.items():
        if key not in ALLOWED_ENV_KEYS:
            continue
        clean_val = str(val if val is not None else "").replace("\r", "").replace("\n", "").strip()
        sanitized_updates[key] = clean_val

    if not sanitized_updates:
        return

    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    applied_keys = set()
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _ = stripped.split("=", 1)
            key = key.strip()
            if key in sanitized_updates:
                new_val = sanitized_updates[key]
                new_lines.append(f"{key}={new_val}\n")
                applied_keys.add(key)
                continue
        new_lines.append(line)

    # Se alguma chave nova não existia no .env, adiciona no final
    remaining_keys = set(sanitized_updates.keys()) - applied_keys
    if remaining_keys:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append("\n# Adicionado via Dashboard Lulatron\n")
        for key in sorted(remaining_keys):
            new_lines.append(f"{key}={sanitized_updates[key]}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Atualiza em memória imediatamente (os.environ e módulo config)
    for key, val_str in sanitized_updates.items():
        os.environ[key] = val_str
        if hasattr(config, key):
            setattr(config, key, val_str)
