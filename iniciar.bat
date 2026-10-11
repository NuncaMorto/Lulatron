@echo off
title Lulatron - Servidor Local
echo ======================================================
echo       INICIANDO LULATRON (PAINEL WEB)
echo ======================================================
echo.
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    echo [*] Servidor rodando em: http://127.0.0.1:5000
    echo [*] Pressione Ctrl + C para encerrar.
    echo.
    venv\Scripts\python.exe app.py
) else (
    echo [ERRO] Ambiente virtual nao encontrado na pasta venv!
    pause
)
