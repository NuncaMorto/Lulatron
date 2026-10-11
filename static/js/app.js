document.addEventListener('DOMContentLoaded', () => {
    // Alternador de Tema Exclusivo na Barra Lateral Esquerda
    const btnThemeLight = document.getElementById('btnThemeLight');
    const btnThemeDark = document.getElementById('btnThemeDark');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('lulatron_theme', theme);

        if (btnThemeLight && btnThemeDark) {
            if (theme === 'light') {
                btnThemeLight.classList.add('active');
                btnThemeDark.classList.remove('active');
            } else {
                btnThemeDark.classList.add('active');
                btnThemeLight.classList.remove('active');
            }
        }
    }

    const savedTheme = localStorage.getItem('lulatron_theme') || 'light';
    applyTheme(savedTheme);

    if (btnThemeLight) {
        btnThemeLight.addEventListener('click', () => applyTheme('light'));
    }
    if (btnThemeDark) {
        btnThemeDark.addEventListener('click', () => applyTheme('dark'));
    }

    // Navegação entre Telas
    const navItems = document.querySelectorAll('.nav-item');
    const viewScreens = document.querySelectorAll('.view-screen');
    const pageTitle = document.getElementById('pageTitle');
    const jobsBadgeCount = document.getElementById('jobsBadgeCount');
    const accountsBadgeCount = document.getElementById('accountsBadgeCount');
    const extractorBadgeCount = document.getElementById('extractorBadgeCount');

    // Upload & Preview
    const dropzone = document.getElementById('dropzone');
    const videoInput = document.getElementById('videoInput');
    const existingMediaFilename = document.getElementById('existingMediaFilename');
    const dropzonePlaceholder = document.getElementById('dropzonePlaceholder');
    const videoPreviewWrapper = document.getElementById('videoPreviewWrapper');
    const videoPreview = document.getElementById('videoPreview');
    const imagePreview = document.getElementById('imagePreview');
    const btnRemoveVideo = document.getElementById('btnRemoveVideo');

    // Formulário de Agendamento
    const scheduleForm = document.getElementById('scheduleForm');
    const captionInput = document.getElementById('caption');
    const charCount = document.getElementById('charCount');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnText = btnSubmit.querySelector('.btn-text');
    const btnSpinner = btnSubmit.querySelector('.btn-spinner');

    // Seleção de Plataformas
    const platformCheckboxes = document.querySelectorAll('input[name="platforms"]');
    const btnSelectAll = document.getElementById('btnSelectAllPlatforms');

    // Abas de Agendamento
    const tabButtons = document.querySelectorAll('.tab-btn');
    const scheduleModeInput = document.getElementById('scheduleMode');
    const scheduleOnceInputs = document.getElementById('scheduleOnceInputs');
    const scheduleDailyInputs = document.getElementById('scheduleDailyInputs');

    // Listas & Ações
    const jobsContainer = document.getElementById('jobsContainer');
    const historyContainer = document.getElementById('historyContainer');
    const btnRefreshJobs = document.getElementById('btnRefreshJobs');
    const btnRefreshHistory = document.getElementById('btnRefreshHistory');
    const btnRefreshHealth = document.getElementById('btnRefreshHealth');

    // Gerador de Contas
    const generatorForm = document.getElementById('generatorForm');
    const genQty = document.getElementById('genQty');
    const genPrefix = document.getElementById('genPrefix');
    const genDomain = document.getElementById('genDomain');
    const genDomainSelect = document.getElementById('genDomainSelect');
    const btnRefreshDomains = document.getElementById('btnRefreshDomains');
    const accountsTableBody = document.getElementById('accountsTableBody');
    const totalVaultAccounts = document.getElementById('totalVaultAccounts');
    const btnDownloadTxt = document.getElementById('btnDownloadTxt');
    const btnDownloadImage = document.getElementById('btnDownloadImage');
    const btnClearVault = document.getElementById('btnClearVault');
    const exportCanvas = document.getElementById('exportCanvas');

    // Modal de Caixa de Entrada
    const inboxModal = document.getElementById('inboxModal');
    const modalInboxEmail = document.getElementById('modalInboxEmail');
    const modalInboxProviderBadge = document.getElementById('modalInboxProviderBadge');
    const modalInboxMessagesList = document.getElementById('modalInboxMessagesList');
    const otpHighlightContainer = document.getElementById('otpHighlightContainer');
    const modalExternalLink = document.getElementById('modalExternalLink');
    const modalExternalLinkText = document.getElementById('modalExternalLinkText');
    const btnCloseInboxModal = document.getElementById('btnCloseInboxModal');
    const btnCloseInboxModalBottom = document.getElementById('btnCloseInboxModalBottom');
    const btnRefreshModalInbox = document.getElementById('btnRefreshModalInbox');
    let currentViewingEmail = "";

    // Status Pills
    const statusIG = document.getElementById('statusIG');
    const statusTT = document.getElementById('statusTT');
    const statusFB = document.getElementById('statusFB');
    const statusKW = document.getElementById('statusKW');

    const viewTitles = {
        'viewForm': 'Novo Agendamento',
        'viewExtractor': 'Extrator de Mídia • Twitter & Instagram',
        'viewJobs': 'Fila de Tarefas Ativas',
        'viewHistory': 'Histórico de Envios',
        'viewAccounts': 'Gerador de Contas & E-mails',
        'viewConnections': 'Conectar Redes Sociais'
    };

    // 1. Navegação de Telas
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetViewId = item.getAttribute('data-view');
            if (!targetViewId) return;

            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            viewScreens.forEach(screen => {
                if (screen.id === targetViewId) {
                    screen.style.display = 'block';
                    screen.classList.add('active');
                } else {
                    screen.style.display = 'none';
                    screen.classList.remove('active');
                }
            });

            if (pageTitle && viewTitles[targetViewId]) {
                pageTitle.textContent = viewTitles[targetViewId];
            }

            if (targetViewId === 'viewExtractor') loadExtractorHistory();
            if (targetViewId === 'viewJobs') loadJobs();
            if (targetViewId === 'viewHistory') loadHistory();
            if (targetViewId === 'viewAccounts') {
                loadAccounts();
                loadDomains();
            }
            if (targetViewId === 'viewConnections') {
                loadConnections();
            }
        });
    });

    // 2. Contador de Caracteres
    captionInput.addEventListener('input', () => {
        charCount.textContent = captionInput.value.length;
    });

    // 3. Seleção Individual de Redes Sociais (CORREÇÃO DEFINITIVA)
    platformCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const card = checkbox.closest('.checkbox-card');
            if (checkbox.checked) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });
    });

    // Botão "Selecionar Todas / Desmarcar Todas"
    btnSelectAll.addEventListener('click', () => {
        const allChecked = Array.from(platformCheckboxes).every(cb => cb.checked);
        platformCheckboxes.forEach(cb => {
            cb.checked = !allChecked;
            const card = cb.closest('.checkbox-card');
            if (!allChecked) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });
        btnSelectAll.textContent = allChecked ? 'Selecionar Todas' : 'Desmarcar Todas';
    });

    // 4. Modos de Agendamento
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const mode = btn.dataset.mode;
            scheduleModeInput.value = mode;

            if (mode === 'now') {
                scheduleOnceInputs.style.display = 'none';
                scheduleDailyInputs.style.display = 'none';
            } else if (mode === 'once') {
                scheduleOnceInputs.style.display = 'block';
                scheduleDailyInputs.style.display = 'none';
                const dtInput = document.getElementById('scheduleDatetime');
                if (!dtInput.value) {
                    const now = new Date(Date.now() + 60 * 60 * 1000);
                    dtInput.value = now.toISOString().slice(0, 16);
                }
            } else if (mode === 'daily') {
                scheduleOnceInputs.style.display = 'none';
                scheduleDailyInputs.style.display = 'block';
            }
        });
    });

    // 5. Drag & Drop e Preview
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            videoInput.files = e.dataTransfer.files;
            handleVideoSelect(e.dataTransfer.files[0]);
        }
    });

    videoInput.addEventListener('change', () => {
        if (videoInput.files && videoInput.files[0]) {
            handleVideoSelect(videoInput.files[0]);
        }
    });

    function handleVideoSelect(file) {
        if (!file.type.startsWith('video/') && !file.type.startsWith('image/')) {
            showToast('Por favor, selecione um arquivo de vídeo ou imagem válido.', 'error');
            return;
        }

        const objectUrl = URL.createObjectURL(file);
        if (file.type.startsWith('image/')) {
            if (imagePreview) {
                imagePreview.src = objectUrl;
                imagePreview.style.display = 'block';
            }
            videoPreview.style.display = 'none';
        } else {
            videoPreview.src = objectUrl;
            videoPreview.style.display = 'block';
            if (imagePreview) imagePreview.style.display = 'none';
        }
        dropzonePlaceholder.style.display = 'none';
        videoPreviewWrapper.style.display = 'block';
        if (existingMediaFilename) existingMediaFilename.value = '';
    }

    btnRemoveVideo.addEventListener('click', (e) => {
        e.stopPropagation();
        videoInput.value = '';
        if (existingMediaFilename) existingMediaFilename.value = '';
        videoPreview.pause();
        videoPreview.src = '';
        videoPreview.style.display = 'none';
        if (imagePreview) {
            imagePreview.src = '';
            imagePreview.style.display = 'none';
        }
        videoPreviewWrapper.style.display = 'none';
        dropzonePlaceholder.style.display = 'block';
    });

    // 6. Envio do Formulário de Agendamento
    scheduleForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const hasExisting = existingMediaFilename && existingMediaFilename.value.trim() !== '';
        const hasUpload = videoInput.files && videoInput.files.length > 0;

        if (!hasExisting && !hasUpload) {
            showToast('Selecione ou extraia um arquivo de mídia primeiro.', 'error');
            return;
        }

        const selectedPlatforms = Array.from(document.querySelectorAll('input[name="platforms"]:checked'));
        if (selectedPlatforms.length === 0) {
            showToast('Selecione pelo menos uma plataforma para publicar.', 'error');
            return;
        }

        const formData = new FormData(scheduleForm);

        btnSubmit.disabled = true;
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline-flex';

        try {
            const response = await fetch('/api/schedule', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showToast(data.message || 'Publicação agendada com sucesso!', 'success');
                scheduleForm.reset();
                charCount.textContent = '0';
                btnRemoveVideo.click();
                tabButtons[0].click();
                loadJobs();

                const jobsNavBtn = document.querySelector('.nav-item[data-view="viewJobs"]');
                if (jobsNavBtn) jobsNavBtn.click();
            } else {
                showToast(data.error || 'Erro ao processar o agendamento.', 'error');
            }
        } catch (err) {
            showToast(`Falha de comunicação: ${err.message}`, 'error');
        } finally {
            btnSubmit.disabled = false;
            btnText.style.display = 'inline-flex';
            btnSpinner.style.display = 'none';
        }
    });

    // 7. Listagem de Tarefas Ativas
    async function loadJobs() {
        try {
            const res = await fetch('/api/jobs');
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            const data = await res.json();
            const jobs = data.jobs || [];

            if (jobsBadgeCount) {
                if (jobs.length > 0) {
                    jobsBadgeCount.textContent = jobs.length;
                    jobsBadgeCount.style.display = 'inline-block';
                } else {
                    jobsBadgeCount.style.display = 'none';
                }
            }

            if (jobs.length === 0) {
                jobsContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-calendar-xmark" style="font-size: 32px; margin-bottom: 12px; display: block; color: var(--accent);"></i>
                        Nenhum agendamento ativo no momento.
                    </div>
                `;
                return;
            }

            jobsContainer.innerHTML = jobs.map(job => `
                <div class="job-card-full" data-job-id="${job.id}">
                    <div class="job-info-full">
                        <h4><i class="fa-solid fa-clock" style="color: var(--accent);"></i> ${job.name}</h4>
                        <p>Próximo disparo: <strong>${job.next_run_time}</strong></p>
                        <div class="job-meta-badges">
                            <span class="job-badge badge-active">Ativo no APScheduler</span>
                        </div>
                    </div>
                    <button class="btn-cancel-job-danger" onclick="cancelJob('${job.id}')">
                        <i class="fa-solid fa-trash-can"></i> Cancelar Agendamento
                    </button>
                </div>
            `).join('');
        } catch (err) {
            console.error('Erro ao carregar jobs:', err);
        }
    }

    // 8. Cancelar Tarefa
    window.cancelJob = async function(jobId) {
        if (!confirm('Deseja realmente cancelar este agendamento?')) return;

        try {
            const res = await fetch(`/api/jobs/${jobId}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok) {
                showToast(data.message, 'success');
                loadJobs();
            } else {
                showToast(data.error, 'error');
            }
        } catch (err) {
            showToast('Erro ao cancelar: ' + err.message, 'error');
        }
    };

    // 9. Carregar Histórico
    async function loadHistory() {
        try {
            const res = await fetch('/api/history');
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            const data = await res.json();
            const history = data.history || [];

            if (history.length === 0) {
                historyContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-inbox" style="font-size: 32px; margin-bottom: 12px; display: block; color: var(--accent);"></i>
                        Nenhuma postagem realizada ainda.
                    </div>
                `;
                return;
            }

            historyContainer.innerHTML = history.map(item => {
                const date = new Date(item.timestamp).toLocaleString('pt-BR');
                const isSuccess = item.status === 'success';
                const platformsList = Array.isArray(item.platforms) ? item.platforms.join(', ') : item.destination;

                return `
                    <div class="history-card-full ${isSuccess ? 'success' : 'failed'}">
                        <div class="history-card-top">
                            <span class="history-status-badge">
                                ${isSuccess ? '<i class="fa-solid fa-check"></i> Disparo Efetuado' : '<i class="fa-solid fa-xmark"></i> Falha no Disparo'}
                            </span>
                            <span class="history-date">${date}</span>
                        </div>
                        <div class="history-body">
                            <div class="history-caption-text">
                                ${item.caption ? item.caption : '<i>(Sem legenda enviada)</i>'}
                            </div>
                            <div class="history-platforms-tag">
                                Plataformas: <strong>${platformsList.toUpperCase()}</strong>
                            </div>
                            ${!isSuccess ? `
                                <div class="history-error-box">
                                    <strong>Detalhes do Erro:</strong><br>${item.error || JSON.stringify(item.details?.failed_platforms || 'Erro')}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        } catch (err) {
            console.error('Erro ao carregar histórico:', err);
        }
    }

    // 10. Status das Plataformas
    async function checkPlatforms() {
        [statusIG, statusTT, statusFB, statusKW].forEach(pill => {
            if (pill) {
                pill.className = 'status-pill checking';
                pill.textContent = 'Checando...';
            }
        });

        try {
            const res = await fetch('/api/platforms-status');
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            const data = await res.json();

            updateStatusPill(statusIG, data.instagram);
            updateStatusPill(statusTT, data.tiktok);
            updateStatusPill(statusFB, data.facebook);
            updateStatusPill(statusKW, data.kwai);

        } catch (err) {
            [statusIG, statusTT, statusFB, statusKW].forEach(pill => {
                if (pill) {
                    pill.className = 'status-pill error';
                    pill.textContent = 'Erro';
                }
            });
        }
    }

    function updateStatusPill(pill, platformData) {
        if (!pill || !platformData) return;
        if (platformData.status === 'connected') {
            pill.className = 'status-pill connected';
            pill.textContent = 'Conectado';
        } else if (platformData.status === 'unconfigured') {
            pill.className = 'status-pill unconfigured';
            pill.textContent = 'Configurar';
        } else {
            pill.className = 'status-pill error';
            pill.textContent = 'Desconectado';
        }
    }

    // ==============================================================================
    // 11. GERADOR DE CONTAS, COFRE E LEITOR DE CAIXA DE ENTRADA
    // ==============================================================================
    let currentVaultAccounts = [];

    async function loadAccounts() {
        try {
            const res = await fetch('/api/accounts');
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            const data = await res.json();
            currentVaultAccounts = data.accounts || [];

            totalVaultAccounts.textContent = currentVaultAccounts.length;
            if (accountsBadgeCount) {
                if (currentVaultAccounts.length > 0) {
                    accountsBadgeCount.textContent = currentVaultAccounts.length;
                    accountsBadgeCount.style.display = 'inline-block';
                } else {
                    accountsBadgeCount.style.display = 'none';
                }
            }

            if (currentVaultAccounts.length === 0) {
                accountsTableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="empty-state">
                            <i class="fa-solid fa-users" style="font-size: 28px; margin-bottom: 8px; display: block; color: var(--accent);"></i>
                            Nenhuma conta gerada ainda. Preencha o formulário acima e clique em "Gerar Credenciais"!
                        </td>
                    </tr>
                `;
                return;
            }

            accountsTableBody.innerHTML = currentVaultAccounts.map((acc, index) => `
                <tr id="row-${acc.id}">
                    <td><strong>#${index + 1}</strong></td>
                    <td>
                        <span class="code-badge">${acc.username}</span>
                        <button class="btn-icon-tiny" onclick="copyText('${acc.username}', 'Usuário')" title="Copiar Usuário">
                            <i class="fa-regular fa-copy"></i>
                        </button>
                    </td>
                    <td>
                        <span>${acc.email}</span>
                        <button class="btn-icon-tiny" onclick="copyText('${acc.email}', 'E-mail')" title="Copiar E-mail">
                            <i class="fa-regular fa-copy"></i>
                        </button>
                    </td>
                    <td>
                        <div class="vault-password-cell">
                            <span class="password-display" id="pwd-${acc.id}">••••••••••••</span>
                            <button class="btn-icon-tiny" onclick="togglePasswordVisibility('${acc.id}', '${acc.password}')" title="Mostrar/Ocultar Senha">
                                <i class="fa-regular fa-eye" id="eye-${acc.id}"></i>
                            </button>
                            <button class="btn-icon-tiny" onclick="copyText('${acc.password}', 'Senha')" title="Copiar Senha">
                                <i class="fa-regular fa-copy"></i>
                            </button>
                        </div>
                    </td>
                    <td>
                        <button class="btn-open-inbox" onclick="openInbox('${acc.email}')" title="Verificar códigos de confirmação recebidos">
                            <i class="fa-solid fa-envelope-open-text"></i> Ler E-mails
                        </button>
                    </td>
                    <td><small style="color: var(--text-muted);">${acc.created_at}</small></td>
                    <td>
                        <button class="btn-icon-tiny" style="color: var(--danger);" onclick="deleteAccount('${acc.id}')" title="Excluir Conta">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </td>
                </tr>
            `).join('');

        } catch (err) {
            console.error('Erro ao carregar contas:', err);
        }
    }

    // 11. Gerenciamento de Domínios e Geração de Contas
    async function loadDomains(refresh = false) {
        if (!genDomainSelect) return;
        try {
            if (refresh && btnRefreshDomains) {
                btnRefreshDomains.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i> Atualizando...';
            }
            const res = await fetch(`/api/accounts/domains?refresh=${refresh}`);
            const data = await res.json();
            const domains = data.domains || [];
            if (domains.length > 0) {
                const currentVal = genDomainSelect.value;
                genDomainSelect.innerHTML = domains.map(d => `
                    <option value="${d.domain}" ${d.recommended ? 'selected' : ''}>${d.label || d.domain}</option>
                `).join('') + '<option value="custom">✏️ Digitar outro domínio...</option>';

                if (currentVal && domains.some(d => d.domain === currentVal)) {
                    genDomainSelect.value = currentVal;
                    genDomain.value = currentVal;
                } else if (data.recommended) {
                    genDomainSelect.value = data.recommended;
                    genDomain.value = data.recommended;
                } else {
                    genDomain.value = domains[0].domain;
                }
            }
            if (refresh) showToast('Domínios ativos atualizados com sucesso!', 'success');
        } catch (err) {
            console.error('Erro ao buscar domínios:', err);
        } finally {
            if (btnRefreshDomains) {
                btnRefreshDomains.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Novos Domínios';
            }
        }
    }

    if (genDomainSelect) {
        genDomainSelect.addEventListener('change', () => {
            if (genDomainSelect.value === 'custom') {
                genDomain.style.display = 'block';
                genDomain.value = '';
                genDomain.focus();
            } else {
                genDomain.style.display = 'none';
                genDomain.value = genDomainSelect.value;
            }
        });
    }

    if (btnRefreshDomains) {
        btnRefreshDomains.addEventListener('click', () => loadDomains(true));
    }

    // Inicializa lista de domínios
    loadDomains();

    // Gerar Lote de Contas
    if (generatorForm) {
        generatorForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btnGenerateAccounts');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Gerando...';

            const selectedDomain = genDomain.value.trim() || 'maxxspace.com';

            const payload = {
                quantity: parseInt(genQty.value) || 5,
                prefix: genPrefix.value.trim(),
                domain: selectedDomain
            };

            try {
                const res = await fetch('/api/accounts/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    showToast(data.message, 'success');
                    loadAccounts();
                } else {
                    showToast(data.error || 'Erro ao gerar contas.', 'error');
                }
            } catch (err) {
                showToast('Falha na comunicação: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Gerar Credenciais';
            }
        });
    }

    // ==============================================================================
    // 12. LEITOR DE CAIXA DE ENTRADA & CÓDIGOS DE 6 DÍGITOS
    // ==============================================================================
    window.openInbox = function(email) {
        currentViewingEmail = email;
        modalInboxEmail.textContent = email;
        inboxModal.classList.add('show');
        fetchInboxMessages(email);
    };

    async function fetchInboxMessages(email) {
        modalInboxMessagesList.innerHTML = '<div class="empty-state"><i class="fa-solid fa-circle-notch fa-spin"></i> Verificando mensagens recebidas...</div>';
        otpHighlightContainer.style.display = 'none';
        otpHighlightContainer.innerHTML = '';

        try {
            const res = await fetch(`/api/accounts/inbox?email=${encodeURIComponent(email)}`);
            const data = await res.json();
            const messages = data.messages || [];

            // Atualiza badge de provedor e botão externo
            if (modalInboxProviderBadge) {
                const prov = data.provider || 'generator.email';
                if (prov === 'mail.tm') {
                    modalInboxProviderBadge.textContent = 'Mail.tm API (Ativo)';
                    modalInboxProviderBadge.style.color = '#10b981';
                    modalInboxProviderBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                    modalInboxProviderBadge.style.background = 'rgba(16, 185, 129, 0.12)';
                    if (modalExternalLink) {
                        modalExternalLink.href = data.mailtm_url || 'https://mail.tm';
                        if (modalExternalLinkText) modalExternalLinkText.textContent = 'Abrir no Mail.tm';
                    }
                } else {
                    modalInboxProviderBadge.textContent = 'Generator.email';
                    modalInboxProviderBadge.style.color = '#3b82f6';
                    modalInboxProviderBadge.style.borderColor = 'rgba(59, 130, 246, 0.4)';
                    modalInboxProviderBadge.style.background = 'rgba(59, 130, 246, 0.12)';
                    if (modalExternalLink) {
                        modalExternalLink.href = data.generator_url || `https://generator.email/${email}`;
                        if (modalExternalLinkText) modalExternalLinkText.textContent = 'Abrir no generator.email';
                    }
                }
            }

            let detectedCode = null;

            // Procura código de 6 dígitos em qualquer mensagem recebida
            for (const m of messages) {
                if (m.code) {
                    detectedCode = m.code;
                    break;
                }
            }

            if (detectedCode) {
                otpHighlightContainer.style.display = 'block';
                otpHighlightContainer.innerHTML = `
                    <div class="inbox-code-highlight">
                        <div class="inbox-code-left">
                            <i class="fa-solid fa-key" style="font-size: 26px; color: var(--success);"></i>
                            <div>
                                <strong style="font-size: 0.85rem; color: var(--text-primary); display: block;">Código de Verificação de 6 Dígitos:</strong>
                                <div class="inbox-code-badge">${detectedCode}</div>
                            </div>
                        </div>
                        <button class="btn-primary" style="padding: 10px 18px; font-size: 0.85rem; width: auto;" onclick="copyText('${detectedCode}', 'Código OTP')">
                            <i class="fa-solid fa-copy"></i> Copiar Código
                        </button>
                    </div>
                `;
            }

            if (messages.length === 0) {
                modalInboxMessagesList.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-envelope-circle-check" style="font-size: 32px; margin-bottom: 8px; display: block; color: var(--accent);"></i>
                        Nenhum e-mail recebido ainda.<br>
                        <small style="color: var(--text-muted);">Solicite o código de confirmação no Instagram/TikTok e clique em "Atualizar Mensagens".</small>
                    </div>
                `;
                return;
            }

            modalInboxMessagesList.innerHTML = messages.map(m => `
                <div class="inbox-message-item">
                    <div class="inbox-msg-top">
                        <span class="inbox-msg-sender"><i class="fa-solid fa-user"></i> De: ${m.from}</span>
                        <small style="color: var(--text-muted);"><i class="fa-solid fa-clock"></i> ${m.date}</small>
                    </div>
                    <div class="inbox-msg-subject">${m.subject}</div>
                    <div class="inbox-msg-body">${m.body}</div>
                    ${m.code ? `
                        <div style="margin-top: 8px;">
                            <button class="btn-secondary" style="padding: 4px 10px; font-size: 0.78rem;" onclick="copyText('${m.code}', 'Código OTP')">
                                <i class="fa-solid fa-copy"></i> Copiar Código (${m.code})
                            </button>
                        </div>
                    ` : ''}
                </div>
            `).join('');

        } catch (err) {
            modalInboxMessagesList.innerHTML = `<div class="empty-state" style="color: var(--danger);">Erro ao consultar caixa de entrada: ${err.message}</div>`;
        }
    }

    if (btnRefreshModalInbox) {
        btnRefreshModalInbox.addEventListener('click', () => {
            if (currentViewingEmail) fetchInboxMessages(currentViewingEmail);
        });
    }

    if (btnCloseInboxModal) {
        btnCloseInboxModal.addEventListener('click', () => inboxModal.classList.remove('show'));
    }
    if (btnCloseInboxModalBottom) {
        btnCloseInboxModalBottom.addEventListener('click', () => inboxModal.classList.remove('show'));
    }

    // Alternar Visualização da Senha
    window.togglePasswordVisibility = function(id, rawPassword) {
        const span = document.getElementById(`pwd-${id}`);
        const eye = document.getElementById(`eye-${id}`);
        if (!span || !eye) return;

        if (span.textContent === '••••••••••••') {
            span.textContent = rawPassword;
            eye.className = 'fa-regular fa-eye-slash';
        } else {
            span.textContent = '••••••••••••';
            eye.className = 'fa-regular fa-eye';
        }
    };

    // Copiar Texto para Área de Transferência
    window.copyText = function(text, label) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(`${label} copiado com sucesso!`, 'success');
        }).catch(() => {
            showToast('Erro ao copiar.', 'error');
        });
    };

    // Excluir Conta Individual
    window.deleteAccount = async function(id) {
        if (!confirm('Deseja remover esta credencial do cofre?')) return;
        try {
            const res = await fetch(`/api/accounts/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok) {
                showToast(data.message, 'success');
                loadAccounts();
            } else {
                showToast(data.error, 'error');
            }
        } catch (err) {
            showToast('Erro ao remover: ' + err.message, 'error');
        }
    };

    // Baixar Arquivo TXT
    if (btnDownloadTxt) {
        btnDownloadTxt.addEventListener('click', () => {
            if (currentVaultAccounts.length === 0) {
                showToast('Nenhuma conta no cofre para exportar.', 'error');
                return;
            }
            window.location.href = '/api/accounts/export/txt';
        });
    }

    // Limpar Todo o Cofre
    if (btnClearVault) {
        btnClearVault.addEventListener('click', async () => {
            if (currentVaultAccounts.length === 0) return;
            if (!confirm('Tem certeza que deseja apagar TODAS as contas do cofre? Essa ação não pode ser desfeita.')) return;

            try {
                const res = await fetch('/api/accounts/clear', { method: 'DELETE' });
                const data = await res.json();
                if (res.ok) {
                    showToast(data.message, 'success');
                    loadAccounts();
                }
            } catch (err) {
                showToast('Erro ao limpar cofre: ' + err.message, 'error');
            }
        });
    }

    // Baixar como Imagem PNG (Renderiza via Canvas com Identidade Lulatron)
    if (btnDownloadImage) {
        btnDownloadImage.addEventListener('click', () => {
            if (currentVaultAccounts.length === 0) {
                showToast('Gere ou adicione contas antes de baixar a imagem.', 'error');
                return;
            }

            const canvas = exportCanvas;
            const ctx = canvas.getContext('2d');

            const itemHeight = 60;
            const headerHeight = 120;
            const footerHeight = 50;
            const totalHeight = headerHeight + (currentVaultAccounts.length * itemHeight) + footerHeight;
            const totalWidth = 980;

            canvas.width = totalWidth;
            canvas.height = totalHeight;

            // Fundo Branco
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, totalWidth, totalHeight);

            // Cabeçalho da Campanha
            const gradient = ctx.createLinearGradient(0, 0, totalWidth, 0);
            gradient.addColorStop(0, '#b91c1c');
            gradient.addColorStop(0.5, '#dc2626');
            gradient.addColorStop(1, '#c8102e');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, totalWidth, headerHeight);

            // Título Oficial Lulatron
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 26px "Plus Jakarta Sans", sans-serif';
            ctx.fillText('★ LULATRON - COFRE DE CONTAS & CREDENCIAIS', 30, 48);

            ctx.font = '14px "Plus Jakarta Sans", sans-serif';
            ctx.fillStyle = '#fef2f2';
            const dateStr = new Date().toLocaleString('pt-BR');
            ctx.fillText(`Exportado em: ${dateStr}  |  Total de Contas: ${currentVaultAccounts.length}  |  Instagram • TikTok • Facebook • Kwai`, 30, 82);

            // Cabeçalho da Tabela
            const tableTop = headerHeight;
            ctx.fillStyle = '#f1f5f9';
            ctx.fillRect(0, tableTop, totalWidth, 36);

            ctx.fillStyle = '#475569';
            ctx.font = 'bold 12px "Plus Jakarta Sans", sans-serif';
            ctx.fillText('#', 30, tableTop + 24);
            ctx.fillText('USUÁRIO', 80, tableTop + 24);
            ctx.fillText('E-MAIL', 320, tableTop + 24);
            ctx.fillText('SENHA DE ACESSO', 620, tableTop + 24);
            ctx.fillText('CRIADO EM', 850, tableTop + 24);

            // Linhas de Contas
            let currentY = tableTop + 36;
            currentVaultAccounts.forEach((acc, i) => {
                if (i % 2 === 0) {
                    ctx.fillStyle = '#ffffff';
                } else {
                    ctx.fillStyle = '#f8fafc';
                }
                ctx.fillRect(0, currentY, totalWidth, itemHeight);

                ctx.strokeStyle = '#e2e8f0';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(0, currentY + itemHeight);
                ctx.lineTo(totalWidth, currentY + itemHeight);
                ctx.stroke();

                ctx.fillStyle = '#1e293b';
                ctx.font = 'bold 13px "Plus Jakarta Sans", sans-serif';
                ctx.fillText(`${i + 1}`, 30, currentY + 35);

                ctx.font = '13px monospace';
                ctx.fillStyle = '#c8102e';
                ctx.fillText(acc.username, 80, currentY + 35);

                ctx.fillStyle = '#334155';
                ctx.font = '13px "Plus Jakarta Sans", sans-serif';
                ctx.fillText(acc.email, 320, currentY + 35);

                ctx.fillStyle = '#0f172a';
                ctx.font = 'bold 13px monospace';
                ctx.fillText(acc.password, 620, currentY + 35);

                ctx.fillStyle = '#64748b';
                ctx.font = '11px "Plus Jakarta Sans", sans-serif';
                ctx.fillText(acc.created_at || '-', 850, currentY + 35);

                currentY += itemHeight;
            });

            // Rodapé
            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(0, currentY, totalWidth, footerHeight);
            ctx.fillStyle = '#64748b';
            ctx.font = '12px "Plus Jakarta Sans", sans-serif';
            ctx.fillText('Segurança: Guarde esta imagem em local seguro e não compartilhe senhas publicamente.', 30, currentY + 30);

            // Dispara Download
            const link = document.createElement('a');
            link.download = `contas_lulatron_${Date.now()}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();

            showToast('Imagem PNG do Lulatron baixada com sucesso!', 'success');
        });
    }

    // Toast Helper
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast show toast-${type}`;
        setTimeout(() => {
            toast.className = 'toast';
        }, 4000);
    }

    // ==============================================================================
    // 14. GERENCIAMENTO DE CONEXÕES DE REDES SOCIAIS (VIEW CONNECTIONS)
    // ==============================================================================
    const btnRefreshConnections = document.getElementById('btnRefreshConnections');
    const formConnIG = document.getElementById('formConnIG');
    const formConnTT = document.getElementById('formConnTT');
    const formConnFB = document.getElementById('formConnFB');
    const formConnKW = document.getElementById('formConnKW');
    const btnDisconnectIG = document.getElementById('btnDisconnectIG');
    const btnToggleIgPass = document.getElementById('btnToggleIgPass');
    const connIgPass = document.getElementById('connIgPass');
    const connIgCodeGroup = document.getElementById('connIgCodeGroup');
    const connIgCode = document.getElementById('connIgCode');
    const connDetailsIG = document.getElementById('connDetailsIG');

    // Toggle Senha Instagram
    if (btnToggleIgPass && connIgPass) {
        btnToggleIgPass.addEventListener('click', () => {
            const isPassword = connIgPass.type === 'password';
            connIgPass.type = isPassword ? 'text' : 'password';
            btnToggleIgPass.innerHTML = isPassword ? '<i class="fa-regular fa-eye-slash"></i>' : '<i class="fa-regular fa-eye"></i>';
        });
    }

    async function loadConnections(isManualRefresh = false) {
        try {
            if (isManualRefresh && btnRefreshConnections) {
                btnRefreshConnections.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i> Atualizando...';
            }

            const res = await fetch('/api/connections');
            const data = await res.json();

            // 1. Instagram
            const ig = data.instagram || {};
            const igUser = document.getElementById('connIgUser');
            const igProxy = document.getElementById('connIgProxy');
            const igTotp = document.getElementById('connIgTotp');
            const igStatus = document.getElementById('connStatusIG');
            const igPassHint = document.getElementById('connIgPassHint');

            if (igUser) igUser.value = ig.username || '';
            if (igProxy) igProxy.value = ig.proxy || '';
            if (igTotp) igTotp.value = ig.totp_seed || '';
            if (igPassHint) {
                igPassHint.textContent = ig.has_password ? 'Senha atual salva no .env (deixe em branco para mantê-la).' : 'Nenhuma senha configurada ainda.';
            }

            if (igStatus) {
                const s = ig.status || {};
                if (s.status === 'connected') {
                    igStatus.className = 'status-pill online';
                    igStatus.textContent = 'Conectado';
                    if (connDetailsIG) {
                        connDetailsIG.style.display = 'flex';
                        connDetailsIG.innerHTML = `
                            <i class="fa-solid fa-circle-check" style="color: var(--success); font-size: 1.1rem;"></i>
                            <div>
                                <strong>@${s.username || ig.username}</strong> ${s.full_name ? `(${s.full_name})` : ''}
                                <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">
                                    ${s.follower_count || 0} seguidores • ${s.media_count || 0} posts
                                </div>
                            </div>
                        `;
                    }
                } else if (s.status === 'unconfigured') {
                    igStatus.className = 'status-pill offline';
                    igStatus.textContent = 'Não configurado';
                    if (connDetailsIG) connDetailsIG.style.display = 'none';
                } else {
                    igStatus.className = 'status-pill offline';
                    igStatus.textContent = 'Desconectado / Erro';
                    if (connDetailsIG) {
                        connDetailsIG.style.display = 'flex';
                        connDetailsIG.innerHTML = `
                            <i class="fa-solid fa-triangle-exclamation" style="color: var(--danger); font-size: 1.1rem;"></i>
                            <div><strong style="color: var(--danger);">Falha:</strong> <small>${s.message || 'Erro de autenticação'}</small></div>
                        `;
                    }
                }
            }

            // 2. Facebook
            const fb = data.facebook || {};
            const fbPageId = document.getElementById('connFbPageId');
            const fbToken = document.getElementById('connFbToken');
            const fbStatus = document.getElementById('connStatusFB');

            if (fbPageId) fbPageId.value = fb.page_id || '';
            if (fbToken) fbToken.value = fb.access_token || '';
            if (fbStatus) {
                const s = fb.status || {};
                if (s.status === 'connected') {
                    fbStatus.className = 'status-pill online';
                    fbStatus.textContent = `Conectado (${s.name || 'Página'})`;
                } else if (s.status === 'unconfigured') {
                    fbStatus.className = 'status-pill offline';
                    fbStatus.textContent = 'Não configurado';
                } else {
                    fbStatus.className = 'status-pill offline';
                    fbStatus.textContent = 'Token Inválido';
                }
            }

            // 3. TikTok
            const tt = data.tiktok || {};
            const ttSession = document.getElementById('connTtSession');
            const ttToken = document.getElementById('connTtToken');
            const ttProxy = document.getElementById('connTtProxy');
            const ttStatus = document.getElementById('connStatusTT');

            if (ttSession) ttSession.value = tt.session_id || '';
            if (ttToken) ttToken.value = tt.access_token || '';
            if (ttProxy) ttProxy.value = tt.proxy || '';
            if (ttStatus) {
                const s = tt.status || {};
                if (s.status === 'connected') {
                    ttStatus.className = 'status-pill online';
                    ttStatus.textContent = `Conectado (${s.display_name || 'Criador'})`;
                } else {
                    ttStatus.className = 'status-pill offline';
                    ttStatus.textContent = 'Não configurado';
                }
            }

            // 4. Kwai
            const kw = data.kwai || {};
            const kwAppId = document.getElementById('connKwAppId');
            const kwToken = document.getElementById('connKwToken');
            const kwProxy = document.getElementById('connKwProxy');
            const kwStatus = document.getElementById('connStatusKW');

            if (kwAppId) kwAppId.value = kw.app_id || '';
            if (kwToken) kwToken.value = kw.access_token || '';
            if (kwProxy) kwProxy.value = kw.proxy || '';
            if (kwStatus) {
                const s = kw.status || {};
                if (s.status === 'connected') {
                    kwStatus.className = 'status-pill online';
                    kwStatus.textContent = 'Conectado';
                } else {
                    kwStatus.className = 'status-pill offline';
                    kwStatus.textContent = 'Não configurado';
                }
            }

            // Atualiza também os pills da barra lateral
            checkPlatforms();

            if (isManualRefresh) showToast('Status de todas as conexões atualizado!', 'success');
        } catch (err) {
            console.error('Erro ao carregar conexões:', err);
        } finally {
            if (btnRefreshConnections) {
                btnRefreshConnections.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Recarregar Status';
            }
        }
    }

    if (btnRefreshConnections) {
        btnRefreshConnections.addEventListener('click', () => loadConnections(true));
    }

    // Salvar e Conectar Instagram
    if (formConnIG) {
        formConnIG.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btnSaveConnIG');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Autenticando...';

            const payload = {
                username: document.getElementById('connIgUser').value.trim(),
                password: document.getElementById('connIgPass').value,
                proxy: document.getElementById('connIgProxy').value.trim(),
                totp_seed: document.getElementById('connIgTotp').value.trim(),
                verification_code: connIgCode ? connIgCode.value.trim() : ''
            };

            try {
                const res = await fetch('/api/connections/instagram', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (data.status === '2fa_required' || data.status === 'challenge_required') {
                    if (connIgCodeGroup) connIgCodeGroup.style.display = 'block';
                    if (connIgCode) connIgCode.focus();
                    showToast('Código de 2FA ou SMS necessário! Digite o código no campo em destaque e clique novamente.', 'warning');
                } else if (res.ok) {
                    showToast(data.message, 'success');
                    if (connIgCodeGroup) connIgCodeGroup.style.display = 'none';
                    if (connIgCode) connIgCode.value = '';
                    loadConnections();
                } else {
                    showToast(data.error || 'Erro ao conectar Instagram.', 'error');
                }
            } catch (err) {
                showToast('Falha na comunicação: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-plug"></i> Conectar & Salvar';
            }
        });
    }

    // Desconectar Instagram
    if (btnDisconnectIG) {
        btnDisconnectIG.addEventListener('click', async () => {
            if (!confirm('Deseja realmente desconectar a conta do Instagram e limpar a sessão salva?')) return;
            try {
                const res = await fetch('/api/connections/instagram/disconnect', { method: 'POST' });
                const data = await res.json();
                showToast(data.message, 'success');
                if (connIgCodeGroup) connIgCodeGroup.style.display = 'none';
                loadConnections();
            } catch (err) {
                showToast('Erro ao desconectar: ' + err.message, 'error');
            }
        });
    }

    // Salvar TikTok
    if (formConnTT) {
        formConnTT.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btnSaveConnTT');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Salvando...';

            const payload = {
                session_id: document.getElementById('connTtSession').value.trim(),
                access_token: document.getElementById('connTtToken').value.trim(),
                proxy: document.getElementById('connTtProxy').value.trim()
            };

            try {
                const res = await fetch('/api/connections/tiktok', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                showToast(data.message || 'Configurações do TikTok salvas!', 'success');
                loadConnections();
            } catch (err) {
                showToast('Erro ao salvar TikTok: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar TikTok';
            }
        });
    }

    // Salvar Facebook
    if (formConnFB) {
        formConnFB.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btnSaveConnFB');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Salvando...';

            const payload = {
                page_id: document.getElementById('connFbPageId').value.trim(),
                access_token: document.getElementById('connFbToken').value.trim()
            };

            try {
                const res = await fetch('/api/connections/facebook', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                showToast(data.message || 'Configurações do Facebook salvas!', 'success');
                loadConnections();
            } catch (err) {
                showToast('Erro ao salvar Facebook: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Facebook';
            }
        });
    }

    // Salvar Kwai
    if (formConnKW) {
        formConnKW.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btnSaveConnKW');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Salvando...';

            const payload = {
                app_id: document.getElementById('connKwAppId').value.trim(),
                access_token: document.getElementById('connKwToken').value.trim(),
                proxy: document.getElementById('connKwProxy').value.trim()
            };

            try {
                const res = await fetch('/api/connections/kwai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                showToast(data.message || 'Configurações do Kwai salvas!', 'success');
                loadConnections();
            } catch (err) {
                showToast('Erro ao salvar Kwai: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Kwai';
            }
        });
    }

    // ==============================================================================
    // 15. EXTRATOR DE MÍDIA (TWITTER / X & INSTAGRAM)
    // ==============================================================================
    const extractorUrlInput = document.getElementById('extractorUrlInput');
    const btnPasteExtractorUrl = document.getElementById('btnPasteExtractorUrl');
    const btnClearExtractorUrl = document.getElementById('btnClearExtractorUrl');
    const btnRunExtractor = document.getElementById('btnRunExtractor');
    const extractorResultContainer = document.getElementById('extractorResultContainer');
    const extractedPlatformBadge = document.getElementById('extractedPlatformBadge');
    const extractedTypeBadge = document.getElementById('extractedTypeBadge');
    const extractedFilesize = document.getElementById('extractedFilesize');
    const extractedDuration = document.getElementById('extractedDuration');
    const extractedVideoPlayer = document.getElementById('extractedVideoPlayer');
    const extractedImagePreview = document.getElementById('extractedImagePreview');
    const extractedAuthorName = document.getElementById('extractedAuthorName');
    const extractedCaptionText = document.getElementById('extractedCaptionText');
    const btnCopyExtractedCaption = document.getElementById('btnCopyExtractedCaption');
    const btnSendToPosting = document.getElementById('btnSendToPosting');
    const btnDownloadExtracted = document.getElementById('btnDownloadExtracted');
    const btnConvertImageToVideo = document.getElementById('btnConvertImageToVideo');
    const btnRefreshExtractorHistory = document.getElementById('btnRefreshExtractorHistory');
    const extractorHistoryGrid = document.getElementById('extractorHistoryGrid');

    let currentExtractedMedia = null;

    function updateClearButtonVisibility() {
        if (!btnClearExtractorUrl || !extractorUrlInput) return;
        if (extractorUrlInput.value && extractorUrlInput.value.trim().length > 0) {
            btnClearExtractorUrl.style.display = 'inline-flex';
        } else {
            btnClearExtractorUrl.style.display = 'none';
        }
    }

    if (extractorUrlInput) {
        extractorUrlInput.addEventListener('input', updateClearButtonVisibility);
        extractorUrlInput.addEventListener('change', updateClearButtonVisibility);
    }

    if (btnClearExtractorUrl && extractorUrlInput) {
        btnClearExtractorUrl.addEventListener('click', () => {
            extractorUrlInput.value = '';
            updateClearButtonVisibility();
            extractorUrlInput.focus();
        });
    }

    // Colar URL da Área de Transferência
    if (btnPasteExtractorUrl && extractorUrlInput) {
        btnPasteExtractorUrl.addEventListener('click', async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text && text.trim()) {
                    extractorUrlInput.value = text.trim();
                    updateClearButtonVisibility();
                    extractorUrlInput.scrollLeft = 0;
                    showToast('Link colado da área de transferência!', 'success');
                } else {
                    showToast('Área de transferência vazia.', 'error');
                }
            } catch (err) {
                showToast('Permissão de colar negada. Cole manualmente com Ctrl+V.', 'error');
            }
        });
    }

    // Executar Extração ao dar Enter no Input
    if (extractorUrlInput && btnRunExtractor) {
        extractorUrlInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                btnRunExtractor.click();
            }
        });
    }

    // Executar Extração
    if (btnRunExtractor) {
        btnRunExtractor.addEventListener('click', async () => {
            const url = extractorUrlInput.value.trim();
            if (!url) {
                showToast('Cole o link do Twitter (X) ou Instagram primeiro.', 'error');
                extractorUrlInput.focus();
                return;
            }

            const btnText = btnRunExtractor.querySelector('.btn-extract-text');
            const btnSpinner = btnRunExtractor.querySelector('.btn-extract-spinner');

            btnRunExtractor.disabled = true;
            if (btnText) btnText.style.display = 'none';
            if (btnSpinner) btnSpinner.style.display = 'inline-flex';

            try {
                const res = await fetch('/api/extractor/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                const data = await res.json();

                if (!res.ok) {
                    throw new Error(data.error || 'Falha ao extrair mídia.');
                }

                currentExtractedMedia = data.media;
                displayExtractedMedia(data.media);
                showToast('Mídia extraída com sucesso em alta resolução!', 'success');
                loadExtractorHistory();

            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                btnRunExtractor.disabled = false;
                if (btnText) btnText.style.display = 'inline-flex';
                if (btnSpinner) btnSpinner.style.display = 'none';
            }
        });
    }

    function displayExtractedMedia(media) {
        if (!extractorResultContainer || !media) return;

        extractorResultContainer.style.display = 'block';

        // Badge de Plataforma
        if (extractedPlatformBadge) {
            if (media.platform === 'twitter') {
                extractedPlatformBadge.innerHTML = '<i class="fa-brands fa-x-twitter"></i> Twitter / X';
                extractedPlatformBadge.style.background = '#0f172a';
            } else if (media.platform === 'instagram') {
                extractedPlatformBadge.innerHTML = '<i class="fa-brands fa-instagram"></i> Instagram';
                extractedPlatformBadge.style.background = '#e1306c';
            } else {
                extractedPlatformBadge.innerHTML = '<i class="fa-solid fa-globe"></i> Web';
                extractedPlatformBadge.style.background = '#475569';
            }
        }

        // Badge de Tipo
        if (extractedTypeBadge) {
            if (media.media_type === 'video') {
                extractedTypeBadge.innerHTML = '<i class="fa-solid fa-video"></i> Vídeo MP4';
                extractedTypeBadge.style.color = 'var(--success)';
                extractedTypeBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
            } else {
                extractedTypeBadge.innerHTML = '<i class="fa-solid fa-image"></i> Imagem Estática';
                extractedTypeBadge.style.color = '#3b82f6';
                extractedTypeBadge.style.borderColor = 'rgba(59, 130, 246, 0.4)';
            }
        }

        // Tamanho e Duração
        if (extractedFilesize) {
            extractedFilesize.innerHTML = `<i class="fa-solid fa-hard-drive"></i> ${media.filesize_formatted || '0 MB'}`;
        }
        if (extractedDuration) {
            if (media.duration) {
                extractedDuration.style.display = 'inline-flex';
                extractedDuration.innerHTML = `<i class="fa-solid fa-stopwatch"></i> ${media.duration}`;
            } else {
                extractedDuration.style.display = 'none';
            }
        }

        // Player / Imagem
        if (media.media_type === 'video') {
            if (extractedVideoPlayer) {
                extractedVideoPlayer.src = media.file_url;
                extractedVideoPlayer.style.display = 'block';
                extractedVideoPlayer.load();
            }
            if (extractedImagePreview) {
                extractedImagePreview.style.display = 'none';
            }
            if (btnConvertImageToVideo) btnConvertImageToVideo.style.display = 'none';
        } else {
            if (extractedImagePreview) {
                extractedImagePreview.src = media.file_url;
                extractedImagePreview.style.display = 'block';
            }
            if (extractedVideoPlayer) {
                extractedVideoPlayer.pause();
                extractedVideoPlayer.src = '';
                extractedVideoPlayer.style.display = 'none';
            }
            if (btnConvertImageToVideo) btnConvertImageToVideo.style.display = 'inline-flex';
        }

        // Autor e Legenda
        if (extractedAuthorName) {
            extractedAuthorName.textContent = media.author || 'Autor da Publicação';
        }
        if (extractedCaptionText) {
            extractedCaptionText.textContent = media.caption || '(Esta publicação não possui texto na legenda)';
        }

        // Botão de Download
        if (btnDownloadExtracted) {
            btnDownloadExtracted.href = media.download_url || media.file_url;
            btnDownloadExtracted.download = media.filename;
        }

        // Scroll suave até o resultado
        extractorResultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Copiar Legenda Extraída
    if (btnCopyExtractedCaption && extractedCaptionText) {
        btnCopyExtractedCaption.addEventListener('click', () => {
            const text = extractedCaptionText.textContent;
            if (text && text !== '(Esta publicação não possui texto na legenda)') {
                copyText(text, 'Legenda original');
            } else {
                showToast('Nenhuma legenda para copiar.', 'error');
            }
        });
    }

    // Ação: Lançar Mídia para a Aba de Postagem
    window.sendExtractedToPosting = function(media) {
        if (!media) return;

        // 1. Configura arquivo existente no formulário
        if (existingMediaFilename) {
            existingMediaFilename.value = media.filename;
        }

        // Limpa input de arquivo físico
        if (videoInput) {
            videoInput.value = '';
            videoInput.required = false;
        }

        // 2. Configura pré-visualização na dropzone
        if (media.media_type === 'image') {
            if (imagePreview) {
                imagePreview.src = media.file_url;
                imagePreview.style.display = 'block';
            }
            if (videoPreview) {
                videoPreview.pause();
                videoPreview.src = '';
                videoPreview.style.display = 'none';
            }
        } else {
            if (videoPreview) {
                videoPreview.src = media.file_url;
                videoPreview.style.display = 'block';
                videoPreview.load();
            }
            if (imagePreview) {
                imagePreview.style.display = 'none';
            }
        }

        if (videoPreviewWrapper) videoPreviewWrapper.style.display = 'block';
        if (dropzonePlaceholder) dropzonePlaceholder.style.display = 'none';

        // 3. Preenche a legenda se houver
        if (captionInput && media.caption) {
            captionInput.value = media.caption;
            charCount.textContent = media.caption.length;
        }

        // 4. Muda suavemente para a aba de postagem
        const navPostBtn = document.querySelector('.nav-item[data-view="viewForm"]');
        if (navPostBtn) navPostBtn.click();

        // 5. Scroll suave até o topo do formulário
        scheduleForm.scrollIntoView({ behavior: 'smooth', block: 'start' });

        showToast('Mídia e legenda enviadas com sucesso para a aba de postagem!', 'success');
    };

    if (btnSendToPosting) {
        btnSendToPosting.addEventListener('click', () => {
            if (currentExtractedMedia) {
                sendExtractedToPosting(currentExtractedMedia);
            }
        });
    }

    // Ação: Converter Imagem em Vídeo 9:16
    if (btnConvertImageToVideo) {
        btnConvertImageToVideo.addEventListener('click', async () => {
            if (!currentExtractedMedia || currentExtractedMedia.media_type !== 'image') return;

            btnConvertImageToVideo.disabled = true;
            btnConvertImageToVideo.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Convertendo para Vídeo 9:16...';

            try {
                const res = await fetch('/api/extractor/convert-to-video', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: currentExtractedMedia.filename })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Falha na conversão.');

                const videoData = data.video;
                // Atualiza a mídia atual com a versão em vídeo
                currentExtractedMedia.filename = videoData.filename;
                currentExtractedMedia.file_url = videoData.file_url;
                currentExtractedMedia.download_url = videoData.download_url;
                currentExtractedMedia.media_type = 'video';
                currentExtractedMedia.filesize_formatted = videoData.filesize_formatted;
                currentExtractedMedia.duration = videoData.duration;

                displayExtractedMedia(currentExtractedMedia);
                showToast('Foto convertida com sucesso em vídeo 9:16 para Reels/TikTok/Kwai!', 'success');
                loadExtractorHistory();

            } catch (err) {
                showToast('Erro ao converter: ' + err.message, 'error');
            } finally {
                btnConvertImageToVideo.disabled = false;
                btnConvertImageToVideo.innerHTML = '<i class="fa-solid fa-film"></i> Converter Foto em Vídeo 9:16 (5s)';
            }
        });
    }

    // Carregar Histórico de Mídias Extraídas
    async function loadExtractorHistory() {
        if (!extractorHistoryGrid) return;

        try {
            const res = await fetch('/api/extractor/history');
            const data = await res.json();
            const list = data.history || [];

            if (extractorBadgeCount) {
                if (list.length > 0) {
                    extractorBadgeCount.textContent = list.length;
                    extractorBadgeCount.style.display = 'inline-block';
                } else {
                    extractorBadgeCount.style.display = 'none';
                }
            }

            if (list.length === 0) {
                extractorHistoryGrid.innerHTML = '<div class="empty-state">Nenhuma mídia extraída ainda. Cole um link acima para começar!</div>';
                return;
            }

            extractorHistoryGrid.innerHTML = list.map(item => {
                const isVideo = item.media_type === 'video';
                const platformIcon = item.platform === 'twitter' ? 'fa-brands fa-x-twitter' : (item.platform === 'instagram' ? 'fa-brands fa-instagram' : 'fa-solid fa-globe');
                const platformLabel = item.platform === 'twitter' ? 'Twitter' : (item.platform === 'instagram' ? 'Instagram' : 'Web');
                const safeItemJson = encodeURIComponent(JSON.stringify(item));

                return `
                    <div class="extractor-history-item">
                        <div class="extractor-history-preview">
                            ${isVideo ? `
                                <video src="${item.file_url}" preload="metadata" muted></video>
                            ` : `
                                <img src="${item.file_url}" alt="Prévia" loading="lazy">
                            `}
                            <span class="extractor-history-pill">
                                <i class="${platformIcon}"></i> ${platformLabel} • ${isVideo ? 'Vídeo' : 'Foto'}
                            </span>
                        </div>
                        <div class="extractor-history-body">
                            <div class="extractor-history-title" title="${item.author || item.title}">${item.author || item.title}</div>
                            <div class="extractor-history-meta">
                                <span><i class="fa-solid fa-hard-drive"></i> ${item.filesize_formatted || ''}</span>
                                <span><i class="fa-solid fa-clock"></i> ${item.created_at || ''}</span>
                            </div>
                            <div class="extractor-history-actions">
                                <button type="button" class="btn-hist-post" title="Lançar para Postagem" onclick='sendExtractedItemFromHistory("${safeItemJson}")'>
                                    <i class="fa-solid fa-paper-plane"></i> Postar
                                </button>
                                <a href="${item.download_url}" class="btn-hist-dl" title="Baixar no dispositivo" download>
                                    <i class="fa-solid fa-download"></i> Baixar
                                </a>
                                <button type="button" class="btn-hist-del" title="Excluir do histórico" onclick="deleteExtractedItem('${item.filename}')">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

        } catch (err) {
            extractorHistoryGrid.innerHTML = `<div class="empty-state" style="color: var(--danger);">Erro ao carregar histórico: ${err.message}</div>`;
        }
    }

    window.sendExtractedItemFromHistory = function(encodedJson) {
        try {
            const item = JSON.parse(decodeURIComponent(encodedJson));
            sendExtractedToPosting(item);
        } catch (e) {
            showToast('Erro ao carregar mídia para postagem.', 'error');
        }
    };

    if (btnRefreshExtractorHistory) {
        btnRefreshExtractorHistory.addEventListener('click', loadExtractorHistory);
    }

    // Excluir Item Extraído
    window.deleteExtractedItem = async function(filename) {
        if (!confirm('Deseja remover esta mídia extraída do servidor?')) return;
        try {
            const res = await fetch(`/api/extractor/history/${encodeURIComponent(filename)}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok) {
                showToast(data.message || 'Mídia removida com sucesso!', 'success');
                if (currentExtractedMedia && currentExtractedMedia.filename === filename) {
                    if (extractorResultContainer) extractorResultContainer.style.display = 'none';
                    currentExtractedMedia = null;
                }
                loadExtractorHistory();
            } else {
                showToast(data.error || 'Erro ao remover mídia.', 'error');
            }
        } catch (err) {
            showToast('Erro ao remover: ' + err.message, 'error');
        }
    };

    // Eventos Manuais
    btnRefreshJobs.addEventListener('click', loadJobs);
    btnRefreshHistory.addEventListener('click', loadHistory);
    btnRefreshHealth.addEventListener('click', checkPlatforms);

    // Inicialização
    loadJobs();
    loadHistory();
    checkPlatforms();
    loadAccounts();
    loadConnections();
    loadExtractorHistory();

    // Alternar painéis expansíveis de Bypass (TikTok / Kwai)
    window.toggleBypass = function(bodyId, iconId) {
        const body = document.getElementById(bodyId);
        const icon = document.getElementById(iconId);
        if (!body) return;

        const isHidden = body.style.display === 'none';
        body.style.display = isHidden ? 'flex' : 'none';
        if (icon) {
            if (isHidden) {
                icon.classList.add('open');
            } else {
                icon.classList.remove('open');
            }
        }
    };

    // Copiar script de desbloqueio do TikTok para o console F12
    window.copyTikTokBypassScript = function() {
        const script = `(function(){document.querySelectorAll('[class*="download"], [class*="modal"], [class*="mask"], [class*="overlay"]').forEach(e=>e.remove());document.body.style.overflow='auto';document.documentElement.style.overflow='auto';alert('Trava do TikTok removida com sucesso!');})();`;
        navigator.clipboard.writeText(script).then(() => {
            showToast('Script anti-trava copiado! Cole no Console do F12 no TikTok.', 'success');
        }).catch(() => {
            showToast('Erro ao copiar script.', 'error');
        });
    };

    // Polling a cada 30s
    setInterval(loadJobs, 30000);
});
