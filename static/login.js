// Configurações e constantes
const CONFIG = {
    API_BASE_URL: window.location.origin,
    CREDENTIALS: {
        username: 'douglas.mosken',
        password: 'Inst123@'
    },
    MAIN_PAGE: 'index_fixed.html',
    MAX_LOGIN_ATTEMPTS: 5,
    LOCKOUT_TIME: 5 * 60 * 1000, // 5 minutos
    SESSION_DURATION: 24 * 60 * 60 * 1000 // 24 horas
};

// Elementos DOM
let elements = {};

// Controle de tentativas de login
let loginAttempts = 0;
let lockoutTime = null;

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    setupEventListeners();
    checkExistingSession();
    setupPasswordToggle();
    setupFormValidation();
    loadLoginAttempts();
});

// Inicializar referências dos elementos
function initializeElements() {
    elements = {
        loginForm: document.getElementById('loginForm'),
        usernameInput: document.getElementById('username'),
        passwordInput: document.getElementById('password'),
        rememberMeCheckbox: document.getElementById('rememberMe'),
        loginBtn: document.getElementById('loginBtn'),
        btnText: document.querySelector('.btn-text'),
        loadingSpinner: document.querySelector('.loading-spinner'),
        errorMessage: document.getElementById('errorMessage'),
        errorText: document.getElementById('errorText'),
        togglePassword: document.getElementById('togglePassword')
    };
}

// Configurar event listeners
function setupEventListeners() {
    // Submit do formulário
    elements.loginForm.addEventListener('submit', handleLogin);
    
    // Enter nos campos de input
    elements.usernameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            elements.passwordInput.focus();
        }
    });
    
    elements.passwordInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleLogin(e);
        }
    });
    
    // Limpar mensagem de erro quando o usuário começar a digitar
    elements.usernameInput.addEventListener('input', clearErrorMessage);
    elements.passwordInput.addEventListener('input', clearErrorMessage);
    
    // Animação de foco nos inputs
    [elements.usernameInput, elements.passwordInput].forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
            this.parentElement.style.transform = 'scale(1.02)';
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
            this.parentElement.style.transform = 'scale(1)';
        });
    });
}

// Configurar toggle de senha
function setupPasswordToggle() {
    elements.togglePassword.addEventListener('click', function() {
        const passwordField = elements.passwordInput;
        const icon = this.querySelector('i');
        
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            passwordField.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    });
}

// Configurar validação do formulário
function setupFormValidation() {
    // Validação em tempo real
    elements.usernameInput.addEventListener('blur', function() {
        validateField(this, 'Usuário é obrigatório');
    });
    
    elements.passwordInput.addEventListener('blur', function() {
        validateField(this, 'Senha é obrigatória');
    });
}

// Validar campo individual
function validateField(field, errorMessage) {
    const value = field.value.trim();
    
    if (!value) {
        field.classList.add('error');
        return false;
    } else {
        field.classList.remove('error');
        return true;
    }
}

// Carregar tentativas de login do localStorage
function loadLoginAttempts() {
    const savedAttempts = localStorage.getItem('login_attempts');
    const savedLockout = localStorage.getItem('lockout_time');
    
    if (savedAttempts) {
        loginAttempts = parseInt(savedAttempts);
    }
    
    if (savedLockout) {
        lockoutTime = parseInt(savedLockout);
        
        // Verificar se o lockout ainda está ativo
        if (new Date().getTime() >= lockoutTime) {
            // Lockout expirado, resetar
            resetLoginAttempts();
        }
    }
}

// Salvar tentativas de login no localStorage
function saveLoginAttempts() {
    localStorage.setItem('login_attempts', loginAttempts.toString());
    if (lockoutTime) {
        localStorage.setItem('lockout_time', lockoutTime.toString());
    }
}

// Resetar tentativas de login
function resetLoginAttempts() {
    loginAttempts = 0;
    lockoutTime = null;
    localStorage.removeItem('login_attempts');
    localStorage.removeItem('lockout_time');
}

// Verificar se está em lockout
function checkLockout() {
    if (lockoutTime && new Date().getTime() < lockoutTime) {
        const remainingTime = Math.ceil((lockoutTime - new Date().getTime()) / 1000);
        showErrorMessage(`Muitas tentativas de login. Tente novamente em ${remainingTime} segundos.`);
        return true;
    }
    return false;
}

// Verificar se já existe uma sessão ativa
function checkExistingSession() {
    const savedSession = localStorage.getItem('instagram_tracker_session');
    
    if (savedSession) {
        try {
            const sessionData = JSON.parse(savedSession);
            const now = new Date().getTime();
            
            // Verificar se a sessão ainda é válida
            if (sessionData.timestamp && (now - sessionData.timestamp) < CONFIG.SESSION_DURATION) {
                showMessage('Sessão ativa encontrada. Redirecionando...', 'success');
                setTimeout(() => {
                    redirectToMainPage();
                }, 1000);
                return;
            } else {
                // Sessão expirada
                localStorage.removeItem('instagram_tracker_session');
            }
        } catch (error) {
            console.error('Erro ao verificar sessão:', error);
            localStorage.removeItem('instagram_tracker_session');
        }
    }
    
    // Focar no campo de usuário se não houver sessão
    setTimeout(() => {
        elements.usernameInput.focus();
    }, 500);
}

// Manipular o login
async function handleLogin(event) {
    event.preventDefault();
    
    // Verificar lockout
    if (checkLockout()) {
        return;
    }
    
    // Validar campos
    if (!validateForm()) {
        return;
    }
    
    const username = elements.usernameInput.value.trim();
    const password = elements.passwordInput.value;
    const rememberMe = elements.rememberMeCheckbox.checked;
    
    // Mostrar loading
    setLoadingState(true);
    clearErrorMessage();
    
    try {
        // Simular delay de autenticação
        await simulateLoginDelay();
        
        // Verificar credenciais
        if (username === CONFIG.CREDENTIALS.username && password === CONFIG.CREDENTIALS.password) {
            // Login bem-sucedido
            resetLoginAttempts();
            
            // Salvar sessão
            saveSession(username, rememberMe);
            
            // Atualizar botão para sucesso
            elements.btnText.innerHTML = '<i class="fas fa-check"></i> Login realizado com sucesso!';
            elements.loginBtn.style.background = 'linear-gradient(45deg, #28a745, #20c997)';
            
            showMessage('Login realizado com sucesso!', 'success');
            
            // Redirecionar após um breve delay
            setTimeout(() => {
                redirectToMainPage();
            }, 1500);
            
        } else {
            // Credenciais inválidas
            loginAttempts++;
            saveLoginAttempts();
            
            if (loginAttempts >= CONFIG.MAX_LOGIN_ATTEMPTS) {
                lockoutTime = new Date().getTime() + CONFIG.LOCKOUT_TIME;
                saveLoginAttempts();
                showErrorMessage('Muitas tentativas de login falharam. Acesso bloqueado por 5 minutos.');
            } else {
                const remainingAttempts = CONFIG.MAX_LOGIN_ATTEMPTS - loginAttempts;
                showErrorMessage(`Usuário ou senha incorretos. ${remainingAttempts} tentativa(s) restante(s).`);
            }
            
            // Limpar senha e focar no usuário
            elements.passwordInput.value = '';
            setTimeout(() => {
                elements.usernameInput.focus();
                elements.usernameInput.select();
            }, 100);
        }
        
    } catch (error) {
        console.error('Erro no login:', error);
        showErrorMessage('Erro interno do servidor. Tente novamente.');
        
    } finally {
        setLoadingState(false);
    }
}

// Validar formulário completo
function validateForm() {
    const usernameValid = validateField(elements.usernameInput, 'Usuário é obrigatório');
    const passwordValid = validateField(elements.passwordInput, 'Senha é obrigatória');
    
    if (!usernameValid) {
        showErrorMessage('Por favor, digite seu usuário.');
        elements.usernameInput.focus();
        return false;
    }
    
    if (!passwordValid) {
        showErrorMessage('Por favor, digite sua senha.');
        elements.passwordInput.focus();
        return false;
    }
    
    return true;
}

// Simular delay de autenticação para melhor UX
function simulateLoginDelay() {
    return new Promise(resolve => {
        setTimeout(resolve, 1500);
    });
}

// Salvar sessão no localStorage
function saveSession(username, rememberMe) {
    const sessionData = {
        username: username,
        timestamp: new Date().getTime(),
        loginTime: new Date().toISOString(),
        rememberMe: rememberMe
    };
    
    localStorage.setItem('instagram_tracker_session', JSON.stringify(sessionData));
    localStorage.setItem('instagram_tracker_logged_in', 'true');
    localStorage.setItem('instagram_tracker_user', username);
    localStorage.setItem('instagram_tracker_login_time', sessionData.timestamp.toString());
}

// Redirecionar para a página principal
function redirectToMainPage() {
    // Verificar se a página principal existe
    fetch(CONFIG.MAIN_PAGE, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                window.location.href = CONFIG.MAIN_PAGE;
            } else {
                // Fallback para index.html se index_fixed.html não existir
                window.location.href = 'index.html';
            }
        })
        .catch(() => {
            // Em caso de erro, tentar index.html
            window.location.href = 'index.html';
        });
}

// Definir estado de loading
function setLoadingState(isLoading) {
    elements.loginBtn.disabled = isLoading;
    
    if (isLoading) {
        elements.btnText.style.display = 'none';
        elements.loadingSpinner.style.display = 'block';
        elements.loginBtn.classList.add('loading');
    } else {
        elements.btnText.style.display = 'block';
        elements.loadingSpinner.style.display = 'none';
        elements.loginBtn.classList.remove('loading');
        
        // Resetar texto do botão
        elements.btnText.innerHTML = 'Entrar';
        elements.loginBtn.style.background = '';
    }
}

// Mostrar mensagem de erro
function showErrorMessage(message) {
    elements.errorText.textContent = message;
    elements.errorMessage.style.display = 'flex';
    
    // Adicionar animação de shake
    elements.errorMessage.classList.remove('shake');
    setTimeout(() => {
        elements.errorMessage.classList.add('shake');
    }, 10);
    
    // Scroll para a mensagem
    elements.errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Auto-hide após 8 segundos
    setTimeout(() => {
        clearErrorMessage();
    }, 8000);
}

// Limpar mensagem de erro
function clearErrorMessage() {
    elements.errorMessage.style.display = 'none';
    elements.errorText.textContent = '';
    elements.errorMessage.classList.remove('shake');
}

// Mostrar mensagem genérica (sucesso, info, etc.)
function showMessage(message, type = 'info') {
    // Criar elemento de mensagem temporário
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    // Adicionar estilos
    messageEl.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 500;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(messageEl);
    
    // Remover após 3 segundos
    setTimeout(() => {
        messageEl.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 300);
    }, 3000);
}

// Adicionar estilos CSS para animações das mensagens
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .form-group.focused label {
        color: #667eea;
    }
    
    .form-group input.error {
        border-color: #ef4444;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
    }
    
    .shake {
        animation: shake 0.5s ease-in-out;
    }
    
    .form-group {
        transition: transform 0.2s ease;
    }
`;
document.head.appendChild(style);

// Função para logout (pode ser útil futuramente)
function logout() {
    localStorage.removeItem('instagram_tracker_session');
    localStorage.removeItem('instagram_tracker_logged_in');
    localStorage.removeItem('instagram_tracker_user');
    localStorage.removeItem('instagram_tracker_login_time');
    resetLoginAttempts();
    window.location.href = 'login.html';
}

// Expor funções globalmente se necessário
window.InstagramTrackerLogin = {
    logout: logout,
    checkSession: checkExistingSession
};

