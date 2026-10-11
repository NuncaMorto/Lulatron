# ⚡ Lulatron — Automação Multi-Plataforma & Extrator de Mídias

> **Sistema Web Full-Stack profissional para automação, extração de mídias e publicação de vídeos e imagens nas principais redes sociais (Instagram, Facebook, TikTok e Kwai).**

---

## 🎯 Principais Recursos

- **🚀 Publicação Multi-Redes:**
  - **Instagram:** Feed, Reels e Stories com suporte a 2FA e gerenciamento de sessões persistentes.
  - **Facebook:** Páginas e Reels via Meta Graph API oficial.
  - **TikTok:** Publicação de vídeos em alta resolução e sessões de criador.
  - **Kwai:** Postagem automatizada em formato vertical.
- **⏰ Agendador Inteligente (APScheduler + SQLite):**
  - **Postar Agora:** Publicação simultânea instantânea em todas as redes selecionadas.
  - **Horário Específico:** Agendamento pontual com data e hora.
  - **Várias Vezes ao Dia:** Publicação diária recorrente em horários personalizados.
- **🪄 Extrator de Mídias (Twitter / X & Instagram):**
  - Extração de vídeos (Reels/Clips) e imagens estáticas em qualidade máxima original.
  - Conversão inteligente de imagens estáticas em vídeos verticais 9:16 (1080x1920, 30fps) prontos para Reels/TikTok.
  - Botão de envio imediato da mídia extraída direto para a esteira de postagem.
- **🛡️ Cofre e Gerador de Contas (Lulatron Vault):**
  - Gerador de e-mails temporários com domínios anti-bloqueio.
  - Leitor de caixa de entrada em tempo real para captura de códigos de 6 dígitos (OTP) de verificação.
  - Exportação das credenciais em formato `.txt` organizado ou imagem PNG.
- **🔒 Segurança Robusta:**
  - Painel administrativo com proteção contra força bruta (Rate Limiting).
  - Cookies de sessão protegidos (`HTTPOnly`, `SameSite=Lax`).
  - Prevenção ativa contra vazamento de credenciais via `.gitignore` rigoroso.

---

## 📁 Estrutura do Repositório

```text
BOTInsta/
├── platforms/                  # Módulos de integração com as redes sociais
│   ├── facebook_service.py     # Meta Graph API (Páginas e Reels)
│   ├── tiktok_service.py       # TikTok Content Posting API / Sessions
│   └── kwai_service.py         # Kwai Video API
├── static/                     # Assets da interface (CSS, JavaScript, ícones)
│   ├── css/style.css           # Estilos e Dark Mode com tema personalizável
│   └── js/app.js               # Lógica interativa do painel, AJAX e players
├── templates/                  # Templates HTML (Jinja2)
│   ├── index.html              # Dashboard completa do sistema
│   └── login.html              # Tela de autenticação protegida
├── uploads/                    # Diretório local para armazenamento de mídias
│   └── extracted/              # Mídias baixadas pelo extrator
├── sessions/                   # Armazenamento seguro de sessões serializadas
├── .env.example                # Modelo de variáveis de ambiente e segurança
├── .gitignore                  # Regras estritas de proteção de arquivos sensíveis
├── app.py                      # Servidor principal Flask e rotas da API
├── config.py                   # Configurações centralizadas do sistema
├── env_manager.py              # Gerenciador seguro do arquivo .env
├── instagram_bot.py            # Automação do Instagram via instagrapi
├── media_extractor.py          # Motor de extração (yt-dlp, curl_cffi, FFmpeg)
├── scheduler_service.py        # Orquestração de tarefas agendadas em segundo plano
├── social_publisher.py         # Publicador unificado multi-plataforma
├── iniciar.bat                 # Script de inicialização rápida no Windows
├── requirements.txt            # Dependências Python do projeto
└── README.md                   # Documentação do projeto
```

---

## 🛠️ Como Executar o Projeto

### 1. Pré-requisitos
- **Python 3.10 ou superior** instalado ([python.org](https://www.python.org/downloads/)).
- **Git** instalado ([git-scm.com](https://git-scm.com/)).
- *(Opcional no Windows)* O FFmpeg já é configurado e detectado automaticamente via pacote `imageio-ffmpeg`. No Linux/VPS, instale com `sudo apt install ffmpeg`.

---

### 2. Clonar o Repositório
```bash
git clone https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git
cd NOME_DO_REPOSITORIO
```

---

### 3. Criar e Ativar o Ambiente Virtual

- **No Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

- **No Windows (Prompt de Comando - CMD):**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```

- **No Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

---

### 4. Instalar as Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 5. Configurar as Variáveis de Ambiente
Copie o arquivo de exemplo `.env.example` criando o seu `.env`:

- **Windows:**
  ```cmd
  copy .env.example .env
  ```
- **Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

Abra o arquivo `.env` e configure suas credenciais de acesso ao painel e às redes:
```ini
# Acesso ao Painel Web
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=SuaSenhaForte123!
SECRET_KEY=uma_chave_longa_e_aleatoria

# Configurações do Servidor
HOST=127.0.0.1
PORT=5000

# Redes Sociais (Podem ser configuradas diretamente pela Dashboard na aba "Conexões")
IG_USERNAME=
IG_PASSWORD=
FB_PAGE_ID=
FB_PAGE_ACCESS_TOKEN=
TIKTOK_ACCESS_TOKEN=
KWAI_APP_ID=
KWAI_ACCESS_TOKEN=
```

---

### 6. Iniciar o Servidor

- **No Windows (1 Clique):**
  Basta dar um duplo clique no arquivo `iniciar.bat`.

- **Pelo Terminal:**
  ```bash
  python app.py
  ```

O terminal exibirá:
```text
 * Running on http://127.0.0.1:5000
```

Abra seu navegador em: **[http://127.0.0.1:5000](http://127.0.0.1:5000)** e faça login com as credenciais definidas no `.env`.

---

## 🔒 Segurança e Boas Práticas

> [!IMPORTANT]
> **Nunca comite o seu arquivo `.env`, o diretório `sessions/` ou `accounts_vault.json`!**
> O `.gitignore` deste projeto já está pré-configurado para impedir o envio acidental de senhas, cookies de sessão, mídias baixadas ou histórico para o GitHub.

- **Proxies Residenciais:** Se você for executar o bot em uma VPS (nuvem como AWS, DigitalOcean, Hetzner), configure um proxy residencial no `.env` para evitar que as redes sociais bloqueiem o IP do datacenter.
- **Intervalo de Publicação:** Não publique dezenas de vídeos em intervalos curtos. Utilize o agendador para espaçar as publicações em pelo menos 45 a 90 minutos.

---

## 📜 Licença

Projeto desenvolvido para fins de automação e produtividade em redes sociais. Uso livre para modificações e melhorias.
