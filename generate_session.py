"""
Script auxiliar para realizar o primeiro login no Instagram e gerar o session.json.
Execute este script se a sua conta tiver Autenticação de 2 Fatores (2FA) ou exigir
desafio por SMS/E-mail (Challenge Required).
"""

import sys
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired
import config

def main():
    print("=" * 60)
    print("  INSTAGRAM BOT - GERADOR E VALIDADOR DE SESSÃO (session.json)")
    print("=" * 60)

    username = config.IG_USERNAME or input("Digite seu usuário do Instagram: ").strip()
    password = config.IG_PASSWORD or input("Digite sua senha do Instagram: ").strip()

    if not username or not password:
        print("[ERRO] Usuário e senha são obrigatórios.")
        sys.exit(1)

    cl = Client()
    if config.IG_PROXY:
        print(f"[*] Utilizando Proxy: {config.IG_PROXY}")
        cl.set_proxy(config.IG_PROXY)

    session_path = Path(config.SESSION_FILE)

    # Verifica se já existe sessão
    if session_path.exists():
        print(f"[*] Sessão existente encontrada em {session_path}. Testando validade...")
        try:
            cl.load_settings(session_path)
            cl.login(username, password)
            cl.get_timeline_feed()
            print("[SUCESSO] A sessão atual ainda é 100% válida! Nenhuma ação necessária.")
            return
        except Exception as e:
            print(f"[!] Sessão expirada ou inválida ({e}). Gerando nova sessão...")

    try:
        print(f"[*] Realizando login para @{username}...")
        cl.login(username, password)
        cl.dump_settings(session_path)
        print(f"[SUCESSO] Login concluído com sucesso!")
        print(f"[SUCESSO] Arquivo de sessão gerado com sucesso em: {session_path}")

    except TwoFactorRequired:
        print("\n[!] Autenticação de Dois Fatores (2FA) detectada.")
        code = input("Digite o código 2FA recebido por SMS ou aplicativo autenticador: ").strip()
        try:
            cl.login(username, password, verification_code=code)
            cl.dump_settings(session_path)
            print(f"[SUCESSO] 2FA verificado e sessão salva em: {session_path}")
        except Exception as err:
            print(f"[ERRO] Falha ao verificar 2FA: {err}")

    except ChallengeRequired:
        print("\n[!] Desafio de segurança exigido pelo Instagram (Challenge Required).")
        try:
            cl.challenge_resolve(cl.last_json)
            cl.dump_settings(session_path)
            print(f"[SUCESSO] Desafio resolvido com sucesso! Sessão salva em: {session_path}")
        except Exception as err:
            print(f"[ERRO] Falha ao resolver o desafio de segurança: {err}")
            print("Dica: Faça login uma vez pelo navegador ou app oficial no mesmo IP para autorizar o acesso.")

    except Exception as e:
        print(f"[ERRO] Falha no login: {e}")

if __name__ == "__main__":
    main()
