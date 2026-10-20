@echo off
rem ===================================================================
rem  GymSystem - sobe o servidor e abre o app no navegador.
rem  Uso: dois cliques neste arquivo (ou "iniciar.bat" no terminal).
rem  Pré-requisito: seção 1 do README (MySQL, .venv, .env e seed).
rem ===================================================================
chcp 65001 > nul
title GymSystem - servidor

rem Vai para a pasta backend, ao lado deste arquivo (funciona de qualquer lugar).
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  [ERRO] Ambiente virtual .venv não encontrado em backend\.venv
    echo.
    echo  Siga a seção 1 do README.md ^(Instalação no Windows, do zero^)
    echo  para criar o .venv e instalar as bibliotecas.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo.
    echo  [ERRO] Arquivo backend\.env não encontrado.
    echo.
    echo  Siga o passo 1.4 da seção 1 do README.md: copie o .env.example para .env
    echo  e coloque a senha do usuário gym em DB_PASSWORD.
    echo.
    pause
    exit /b 1
)

echo.
echo  GymSystem: subindo o servidor em http://localhost:5000
echo  O navegador abre sozinho em alguns segundos.
echo  Para parar o servidor: Ctrl+C nesta janela (ou feche a janela).
echo.

rem Abre o navegador ~4 segundos depois, em segundo plano, enquanto o servidor sobe.
rem (ping como espera: o "timeout" não funciona em segundo plano.)
start "" /b cmd /c "ping -n 5 127.0.0.1 > nul & start http://localhost:5000"

".venv\Scripts\python.exe" app.py

rem Só chega aqui quando o servidor para. Se foi por erro (ex.: MySQL desligado),
rem a pausa deixa a mensagem visível em vez de fechar a janela.
echo.
echo  Servidor encerrado.
pause
