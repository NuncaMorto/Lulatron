#!/bin/bash
# ==============================================================================
# Script de Deploy Automatizado para VPS Ubuntu/Debian
# ==============================================================================

set -e

echo "==> Atualizando pacotes do sistema..."
sudo apt update && sudo apt upgrade -y

echo "==> Instalando dependências do sistema (Python, FFmpeg, Nginx, Git)..."
sudo apt install -y python3 python3-pip python3-venv ffmpeg nginx curl git

PROJECT_DIR=$(pwd)

echo "==> Criando ambiente virtual Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "==> Instalando dependências do projeto..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "==> Garantindo permissões dos diretórios operacionais..."
mkdir -p uploads sessions
chmod 755 uploads sessions

echo "==> Criando serviço Systemd para execução 24/7..."
SERVICE_FILE="/etc/systemd/system/socialbot.service"
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=SocialBot Pro - Multi-Platform Automation
After=network.target

[Service]
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 --timeout 180 wsgi:app
Restart=always
RestartSec=5
EnvironmentFile=$PROJECT_DIR/.env

[Install]
WantedBy=multi-user.target
EOL

echo "==> Habilitando e iniciando serviço SocialBot..."
sudo systemctl daemon-reload
sudo systemctl enable socialbot
sudo systemctl restart socialbot

echo "==> Configurando Nginx Reverse Proxy..."
sudo cp nginx.conf /etc/nginx/sites-available/socialbot
sudo ln -sf /etc/nginx/sites-available/socialbot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "======================================================================"
echo " [OK] Deploy concluído com sucesso!"
echo " Acesse seu bot via IP da VPS ou domínio na porta 80."
echo " Status do serviço: sudo systemctl status socialbot"
echo " Logs em tempo real: sudo journalctl -u socialbot -f"
echo "======================================================================"
