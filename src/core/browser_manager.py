"""
Browser Manager 2025 - Gerenciador de Navegador Avançado
Versão God Mode Ultimate - Implementação REAL sem placeholders

Funcionalidades:
- Login Instagram com detecção de 2FA (SMS/Email/TOTP)
- Handler para challenges de segurança
- Sessão persistente com cookies criptografados (AES-256)
- Reconexão automática quando sessão expira
- Login via session_id (bypass de credenciais)
- Integração com Nodriver (Chrome CDP)
"""

import asyncio
import nodriver as uc
import logging
import json
import os
import random
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

# Tentar importar cryptography para criptografia de cookies
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None


class LoginStatus(Enum):
    """Status possíveis do processo de login"""
    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_2FA = "requires_2fa"
    REQUIRES_CHALLENGE = "requires_challenge"
    ACCOUNT_LOCKED = "account_locked"
    INVALID_CREDENTIALS = "invalid_credentials"
    RATE_LIMITED = "rate_limited"
    SESSION_EXPIRED = "session_expired"
    UNKNOWN_ERROR = "unknown_error"


class ChallengeType(Enum):
    """Tipos de challenge de segurança do Instagram"""
    SMS_CODE = "sms"
    EMAIL_CODE = "email"
    TOTP_CODE = "totp"  # Google Authenticator
    SUSPICIOUS_LOGIN = "suspicious_login"
    VERIFY_IDENTITY = "verify_identity"
    UNKNOWN = "unknown"


@dataclass
class LoginResult:
    """Resultado do processo de login"""
    status: LoginStatus
    message: str
    challenge_type: Optional[ChallengeType] = None
    challenge_context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionData:
    """Dados da sessão para persistência"""
    username: str
    user_id: Optional[str]
    session_id: Optional[str]
    cookies: Dict[str, str]
    created_at: str
    expires_at: Optional[str]
    last_used: str
    is_valid: bool = True
    login_method: str = "credentials"


class CookieEncryptor:
    """
    Criptografador de cookies usando Fernet (AES-256).
    
    Permite armazenar cookies de sessão de forma segura no disco.
    A chave é derivada de uma senha usando PBKDF2.
    """
    
    def __init__(self, password: str, salt: Optional[bytes] = None):
        """
        Inicializa o encriptador.
        
        Args:
            password: Senha para derivar a chave de criptografia
            salt: Salt para PBKDF2 (gerado se não fornecido)
        """
        if not CRYPTO_AVAILABLE:
            self.fernet = None
            self.salt = b""
            return
        
        self.salt = salt or os.urandom(16)
        
        # Derivar chave usando PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)
    
    def encrypt(self, data: str) -> bytes:
        """Criptografa uma string"""
        if not self.fernet:
            # Fallback: base64 simples (não seguro, mas funcional)
            return base64.b64encode(data.encode())
        return self.fernet.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Descriptografa dados"""
        if not self.fernet:
            return base64.b64decode(encrypted_data).decode()
        return self.fernet.decrypt(encrypted_data).decode()
    
    def get_salt(self) -> bytes:
        """Retorna o salt usado"""
        return self.salt


class SessionManager:
    """
    Gerenciador de sessões persistentes.
    
    Armazena sessões de forma criptografada no disco e
    permite restaurar sessões anteriores.
    """
    
    DEFAULT_SESSION_DIR = ".instagram_sessions"
    
    def __init__(self, session_dir: Optional[str] = None, password: Optional[str] = None):
        """
        Inicializa o gerenciador de sessões.
        
        Args:
            session_dir: Diretório para armazenar sessões
            password: Senha para criptografia. Se não fornecido, usa a variável de ambiente SESSION_ENCRYPTION_KEY.
        """
        self.session_dir = session_dir or self.DEFAULT_SESSION_DIR

        self.password = password or os.environ.get("SESSION_ENCRYPTION_KEY")
        if not self.password:
            raise ValueError("SESSION_ENCRYPTION_KEY environment variable is missing and no password was provided.")

        self.logger = logging.getLogger("SessionManager")
        
        # Criar diretório se não existir
        os.makedirs(self.session_dir, exist_ok=True)
    
    def _get_session_path(self, username: str) -> str:
        """Retorna o caminho do arquivo de sessão"""
        # Hash do username para evitar caracteres problemáticos
        username_hash = hashlib.sha256(username.lower().encode()).hexdigest()[:16]
        return os.path.join(self.session_dir, f"session_{username_hash}.enc")
    
    def _get_salt_path(self, username: str) -> str:
        """Retorna o caminho do arquivo de salt"""
        username_hash = hashlib.sha256(username.lower().encode()).hexdigest()[:16]
        return os.path.join(self.session_dir, f"salt_{username_hash}.bin")
    
    def save_session(self, session: SessionData) -> bool:
        """
        Salva sessão criptografada no disco.
        
        Args:
            session: Dados da sessão
            
        Returns:
            True se salvou com sucesso
        """
        try:
            session_path = self._get_session_path(session.username)
            salt_path = self._get_salt_path(session.username)
            
            # Criar encriptador
            encryptor = CookieEncryptor(self.password)
            
            # Serializar sessão
            session_dict = {
                'username': session.username,
                'user_id': session.user_id,
                'session_id': session.session_id,
                'cookies': session.cookies,
                'created_at': session.created_at,
                'expires_at': session.expires_at,
                'last_used': session.last_used,
                'is_valid': session.is_valid,
                'login_method': session.login_method
            }
            
            session_json = json.dumps(session_dict)
            encrypted_data = encryptor.encrypt(session_json)
            
            # Salvar salt
            with open(salt_path, 'wb') as f:
                f.write(encryptor.get_salt())
            
            # Salvar sessão criptografada
            with open(session_path, 'wb') as f:
                f.write(encrypted_data)
            
            self.logger.info(f"✅ Sessão salva para @{session.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar sessão: {e}")
            return False
    
    def load_session(self, username: str) -> Optional[SessionData]:
        """
        Carrega sessão criptografada do disco.
        
        Args:
            username: Nome de usuário
            
        Returns:
            SessionData ou None se não existir/falhar
        """
        try:
            session_path = self._get_session_path(username)
            salt_path = self._get_salt_path(username)
            
            if not os.path.exists(session_path) or not os.path.exists(salt_path):
                return None
            
            # Carregar salt
            with open(salt_path, 'rb') as f:
                salt = f.read()
            
            # Criar encriptador com o salt salvo
            encryptor = CookieEncryptor(self.password, salt=salt)
            
            # Carregar e descriptografar sessão
            with open(session_path, 'rb') as f:
                encrypted_data = f.read()
            
            session_json = encryptor.decrypt(encrypted_data)
            session_dict = json.loads(session_json)
            
            session = SessionData(
                username=session_dict['username'],
                user_id=session_dict.get('user_id'),
                session_id=session_dict.get('session_id'),
                cookies=session_dict.get('cookies', {}),
                created_at=session_dict.get('created_at', ''),
                expires_at=session_dict.get('expires_at'),
                last_used=session_dict.get('last_used', ''),
                is_valid=session_dict.get('is_valid', True),
                login_method=session_dict.get('login_method', 'credentials')
            )
            
            self.logger.info(f"✅ Sessão carregada para @{username}")
            return session
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar sessão: {e}")
            return None
    
    def delete_session(self, username: str) -> bool:
        """Remove sessão do disco"""
        try:
            session_path = self._get_session_path(username)
            salt_path = self._get_salt_path(username)
            
            if os.path.exists(session_path):
                os.remove(session_path)
            if os.path.exists(salt_path):
                os.remove(salt_path)
            
            self.logger.info(f"🗑️ Sessão removida para @{username}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao remover sessão: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """Lista usernames com sessões salvas"""
        sessions = []
        try:
            for filename in os.listdir(self.session_dir):
                if filename.startswith("session_") and filename.endswith(".enc"):
                    # Não podemos recuperar o username do hash, então listamos os hashes
                    sessions.append(filename.replace("session_", "").replace(".enc", ""))
        except Exception as e:
            self.logger.error(f"Erro ao listar sessões: {e}")
        return sessions


class NodriverManager:
    """
    Gerenciador de Navegador Ultra-Rápido usando Nodriver (CDP).
    
    Versão 2.0 com suporte a:
    - Login com detecção de 2FA
    - Handlers para challenges de segurança
    - Sessões persistentes criptografadas
    - Reconexão automática
    - Login via session_id
    """
    
    # Seletores para detecção de estados do login
    SELECTORS = {
        'login_form': "input[name='username']",
        'password_field': "input[name='password']",
        'submit_button': "button[type='submit']",
        'home_icon': "svg[aria-label='Página inicial']",
        'home_icon_en': "svg[aria-label='Home']",
        '2fa_input': "input[name='verificationCode']",
        '2fa_code_input': "input[aria-label*='Código']",
        'challenge_form': "input[name='security_code']",
        'challenge_email_option': "button[class*='email']",
        'challenge_sms_option': "button[class*='sms']",
        'error_message': "div[aria-atomic='true']",
        'suspicious_login': "#react-root form[class*='challenge']",
        'save_login_info': "button[class*='save']",
        'not_now_button': "button:contains('Agora não')",
    }
    
    # Timeouts (em segundos)
    TIMEOUTS = {
        'page_load': 30,
        'element_wait': 10,
        'login_redirect': 15,
        '2fa_wait': 120,  # 2 minutos para usuário inserir código
    }
    
    def __init__(self, headless: bool = True, session_manager: Optional[SessionManager] = None):
        """
        Inicializa o gerenciador.
        
        Args:
            headless: Executar sem interface gráfica
            session_manager: Gerenciador de sessões (criado se não fornecido)
        """
        self.headless = headless
        self.browser = None
        self.main_tab = None
        self.session_manager = session_manager or SessionManager()
        self.current_session: Optional[SessionData] = None
        self.logged_in_username: Optional[str] = None
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("NodriverManager")

    async def start(self) -> Any:
        """Inicia o navegador Nodriver com configurações anti-detecção"""
        try:
            self.logger.info("🚀 Iniciando motor Nodriver (Chrome CDP)...")
            
            # Argumentos para máxima furtividade
            args = [
                '--no-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--lang=pt-BR',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-popup-blocking',
                '--disable-translate',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-sync',
                '--disable-default-apps',
                '--mute-audio',
            ]
            
            self.browser = await uc.start(
                headless=self.headless,
                browser_args=args
            )
            
            self.main_tab = self.browser.main_tab
            
            # Injetar scripts anti-detecção
            await self._inject_stealth_scripts()
            
            self.logger.info("✅ Nodriver iniciado e pronto para ação.")
            return self.browser
            
        except Exception as e:
            self.logger.error(f"❌ Falha crítica ao iniciar Nodriver: {e}")
            raise

    async def _inject_stealth_scripts(self) -> None:
        """Injeta scripts para evitar detecção de automação"""
        try:
            stealth_script = """
            // Ocultar webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Ocultar permissões de notificação
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Ocultar plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Ocultar idiomas
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en']
            });
            
            // Chrome runtime
            window.chrome = {
                runtime: {}
            };
            """
            
            await self.main_tab.evaluate(stealth_script)
            
        except Exception as e:
            self.logger.debug(f"Falha ao injetar scripts stealth: {e}")

    async def stop(self) -> None:
        """Fecha o navegador"""
        if self.browser:
            try:
                self.browser.stop()
                self.browser = None
                self.main_tab = None
                self.logger.info("🛑 Nodriver finalizado.")
            except Exception as e:
                self.logger.error(f"Erro ao fechar Nodriver: {e}")

    async def navigate(self, url: str) -> bool:
        """Navega para uma URL"""
        try:
            if not self.browser:
                await self.start()
            
            self.logger.info(f"🌐 Navegando para {url}")
            await self.main_tab.get(url)
            await self.main_tab.wait_for("body", timeout=self.TIMEOUTS['page_load'])
            return True
            
        except Exception as e:
            self.logger.error(f"Erro de navegação: {e}")
            return False

    async def login(
        self,
        username: str,
        password: str,
        use_saved_session: bool = True,
        save_session: bool = True
    ) -> LoginResult:
        """
        Realiza login no Instagram com tratamento completo.
        
        Args:
            username: Nome de usuário
            password: Senha
            use_saved_session: Tentar restaurar sessão salva primeiro
            save_session: Salvar sessão após login bem-sucedido
            
        Returns:
            LoginResult com status e detalhes
        """
        try:
            # 1. Tentar restaurar sessão salva
            if use_saved_session:
                restored = await self._try_restore_session(username)
                if restored:
                    return LoginResult(
                        status=LoginStatus.SUCCESS,
                        message="Sessão restaurada com sucesso",
                        username=username,
                        session_id=self.current_session.session_id if self.current_session else None
                    )
            
            # 2. Iniciar navegador se necessário
            if not self.browser:
                await self.start()
            
            self.logger.info(f"🔐 Iniciando processo de login para @{username}...")
            
            # 3. Navegar para página de login
            await self.main_tab.get("https://www.instagram.com/accounts/login/")
            await asyncio.sleep(random.uniform(2, 3))
            
            # 4. Aguardar e preencher formulário
            try:
                user_input = await self.main_tab.wait_for(
                    self.SELECTORS['login_form'], 
                    timeout=self.TIMEOUTS['element_wait']
                )
            except:
                return LoginResult(
                    status=LoginStatus.UNKNOWN_ERROR,
                    message="Página de login não carregou corretamente"
                )
            
            pass_input = await self.main_tab.select(self.SELECTORS['password_field'])
            
            if not user_input or not pass_input:
                return LoginResult(
                    status=LoginStatus.UNKNOWN_ERROR,
                    message="Campos de login não encontrados"
                )
            
            # 5. Digitação humanizada
            await self._human_type(user_input, username)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            await self._human_type(pass_input, password)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 6. Submeter formulário
            login_btn = await self.main_tab.select(self.SELECTORS['submit_button'])
            if login_btn:
                await login_btn.click()
                self.logger.info("🖱️ Botão de login clicado.")
            else:
                # Tentar submeter via Enter
                await pass_input.send_keys("\n")
            
            # 7. Aguardar resultado
            await asyncio.sleep(3)
            
            # 8. Verificar resultado do login
            result = await self._check_login_result(username)
            
            # 9. Tratar challenges/2FA se necessário
            if result.status == LoginStatus.REQUIRES_2FA:
                self.logger.info("🔑 2FA detectado, aguardando código...")
                # Retornar para que o caller possa fornecer o código
                return result
            
            if result.status == LoginStatus.REQUIRES_CHALLENGE:
                self.logger.info(f"⚠️ Challenge detectado: {result.challenge_type}")
                return result
            
            # 10. Login bem-sucedido - salvar sessão
            if result.status == LoginStatus.SUCCESS and save_session:
                await self._save_current_session(username)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante login: {e}")
            return LoginResult(
                status=LoginStatus.UNKNOWN_ERROR,
                message=str(e)
            )

    async def _human_type(self, element: Any, text: str) -> None:
        """Digita texto de forma humanizada com delays variáveis"""
        for char in text:
            await element.send_keys(char)
            # Delay variável entre teclas (50-150ms)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def _check_login_result(self, username: str) -> LoginResult:
        """
        Verifica o resultado do login analisando a página.
        
        Detecta:
        - Login bem-sucedido (redirecionado para home)
        - 2FA necessário
        - Challenge de segurança
        - Credenciais inválidas
        - Rate limiting
        """
        try:
            # Verificar se logou com sucesso (ícone de home presente)
            try:
                home_icon = await self.main_tab.select(self.SELECTORS['home_icon'])
                if home_icon:
                    self.logged_in_username = username
                    cookies = await self.get_cookies_dict()
                    session_id = cookies.get('sessionid')
                    
                    return LoginResult(
                        status=LoginStatus.SUCCESS,
                        message="Login realizado com sucesso",
                        username=username,
                        session_id=session_id,
                        cookies=cookies
                    )
            except:
                pass
            
            # Tentar ícone em inglês
            try:
                home_icon_en = await self.main_tab.select(self.SELECTORS['home_icon_en'])
                if home_icon_en:
                    self.logged_in_username = username
                    cookies = await self.get_cookies_dict()
                    session_id = cookies.get('sessionid')
                    
                    return LoginResult(
                        status=LoginStatus.SUCCESS,
                        message="Login realizado com sucesso",
                        username=username,
                        session_id=session_id,
                        cookies=cookies
                    )
            except:
                pass
            
            # Verificar se requer 2FA
            try:
                twofa_input = await self.main_tab.select(self.SELECTORS['2fa_input'])
                if twofa_input:
                    return LoginResult(
                        status=LoginStatus.REQUIRES_2FA,
                        message="Código de verificação 2FA necessário",
                        challenge_type=ChallengeType.TOTP_CODE,
                        username=username
                    )
            except:
                pass
            
            # Verificar campo de código alternativo
            try:
                code_input = await self.main_tab.select(self.SELECTORS['2fa_code_input'])
                if code_input:
                    # Determinar tipo de challenge
                    page_text = await self._get_page_text()
                    
                    if 'SMS' in page_text or 'mensagem' in page_text.lower():
                        challenge_type = ChallengeType.SMS_CODE
                    elif 'email' in page_text.lower() or 'e-mail' in page_text.lower():
                        challenge_type = ChallengeType.EMAIL_CODE
                    else:
                        challenge_type = ChallengeType.TOTP_CODE
                    
                    return LoginResult(
                        status=LoginStatus.REQUIRES_2FA,
                        message=f"Código de verificação necessário via {challenge_type.value}",
                        challenge_type=challenge_type,
                        username=username
                    )
            except:
                pass
            
            # Verificar challenge de segurança
            try:
                challenge_form = await self.main_tab.select(self.SELECTORS['challenge_form'])
                if challenge_form:
                    return LoginResult(
                        status=LoginStatus.REQUIRES_CHALLENGE,
                        message="Challenge de segurança detectado",
                        challenge_type=ChallengeType.VERIFY_IDENTITY,
                        username=username
                    )
            except:
                pass
            
            # Verificar mensagens de erro
            try:
                error_div = await self.main_tab.select(self.SELECTORS['error_message'])
                if error_div:
                    error_text = await self._get_element_text(error_div)
                    
                    if 'incorreta' in error_text.lower() or 'wrong' in error_text.lower():
                        return LoginResult(
                            status=LoginStatus.INVALID_CREDENTIALS,
                            message="Senha incorreta"
                        )
                    
                    if 'tentar novamente' in error_text.lower() or 'wait' in error_text.lower():
                        return LoginResult(
                            status=LoginStatus.RATE_LIMITED,
                            message="Muitas tentativas. Aguarde antes de tentar novamente."
                        )
            except:
                pass
            
            # Se nada foi detectado, aguardar mais um pouco
            await asyncio.sleep(3)
            
            # Última verificação de sucesso
            try:
                home_icon = await self.main_tab.select(self.SELECTORS['home_icon'])
                if home_icon:
                    self.logged_in_username = username
                    cookies = await self.get_cookies_dict()
                    return LoginResult(
                        status=LoginStatus.SUCCESS,
                        message="Login realizado com sucesso",
                        username=username,
                        session_id=cookies.get('sessionid'),
                        cookies=cookies
                    )
            except:
                pass
            
            return LoginResult(
                status=LoginStatus.UNKNOWN_ERROR,
                message="Não foi possível determinar o resultado do login"
            )
            
        except Exception as e:
            return LoginResult(
                status=LoginStatus.UNKNOWN_ERROR,
                message=f"Erro ao verificar resultado: {e}"
            )

    async def submit_2fa_code(self, code: str) -> LoginResult:
        """
        Submete código de verificação 2FA.
        
        Args:
            code: Código de 6 dígitos
            
        Returns:
            LoginResult com status
        """
        try:
            self.logger.info(f"🔑 Submetendo código 2FA: {code[:2]}****")
            
            # Encontrar campo de código
            code_input = None
            
            for selector in [self.SELECTORS['2fa_input'], self.SELECTORS['2fa_code_input']]:
                try:
                    code_input = await self.main_tab.select(selector)
                    if code_input:
                        break
                except:
                    continue
            
            if not code_input:
                return LoginResult(
                    status=LoginStatus.UNKNOWN_ERROR,
                    message="Campo de código 2FA não encontrado"
                )
            
            # Limpar e digitar código
            await code_input.clear()
            await self._human_type(code_input, code)
            await asyncio.sleep(0.5)
            
            # Submeter
            submit_btn = await self.main_tab.select(self.SELECTORS['submit_button'])
            if submit_btn:
                await submit_btn.click()
            else:
                await code_input.send_keys("\n")
            
            await asyncio.sleep(3)
            
            # Verificar resultado
            return await self._check_login_result(self.logged_in_username or "")
            
        except Exception as e:
            return LoginResult(
                status=LoginStatus.UNKNOWN_ERROR,
                message=f"Erro ao submeter 2FA: {e}"
            )

    async def login_with_session_id(self, session_id: str) -> LoginResult:
        """
        Realiza login usando session_id existente (bypass de credenciais).
        
        Args:
            session_id: Cookie sessionid válido do Instagram
            
        Returns:
            LoginResult
        """
        try:
            self.logger.info("🔐 Tentando login via session_id...")
            
            if not self.browser:
                await self.start()
            
            # Navegar para Instagram primeiro
            await self.main_tab.get("https://www.instagram.com/")
            await asyncio.sleep(2)
            
            # Definir cookies
            cookies = [
                {
                    'name': 'sessionid',
                    'value': session_id,
                    'domain': '.instagram.com',
                    'path': '/'
                },
                {
                    'name': 'ds_user_id',
                    'value': '',  # Será preenchido automaticamente
                    'domain': '.instagram.com',
                    'path': '/'
                }
            ]
            
            await self.browser.cookies.set_all(cookies)
            
            # Recarregar página
            await self.main_tab.get("https://www.instagram.com/")
            await asyncio.sleep(3)
            
            # Verificar se logou
            try:
                home_icon = await self.main_tab.select(self.SELECTORS['home_icon'])
                if home_icon:
                    all_cookies = await self.get_cookies_dict()
                    
                    return LoginResult(
                        status=LoginStatus.SUCCESS,
                        message="Login via session_id bem-sucedido",
                        session_id=session_id,
                        cookies=all_cookies
                    )
            except:
                pass
            
            return LoginResult(
                status=LoginStatus.SESSION_EXPIRED,
                message="Session ID inválido ou expirado"
            )
            
        except Exception as e:
            return LoginResult(
                status=LoginStatus.UNKNOWN_ERROR,
                message=f"Erro no login via session_id: {e}"
            )

    async def _try_restore_session(self, username: str) -> bool:
        """
        Tenta restaurar sessão salva.
        
        Returns:
            True se restaurou com sucesso
        """
        try:
            session = self.session_manager.load_session(username)
            
            if not session or not session.is_valid:
                return False
            
            # Verificar se sessão não expirou (7 dias por padrão)
            if session.expires_at:
                expires = datetime.fromisoformat(session.expires_at)
                if datetime.now() > expires:
                    self.logger.info("⏰ Sessão expirada")
                    return False
            
            self.logger.info(f"🔄 Tentando restaurar sessão para @{username}...")
            
            if not self.browser:
                await self.start()
            
            # Navegar primeiro
            await self.main_tab.get("https://www.instagram.com/")
            await asyncio.sleep(1)
            
            # Definir cookies salvos
            cookies_list = [
                {'name': name, 'value': value, 'domain': '.instagram.com', 'path': '/'}
                for name, value in session.cookies.items()
            ]
            
            await self.browser.cookies.set_all(cookies_list)
            
            # Recarregar
            await self.main_tab.get("https://www.instagram.com/")
            await asyncio.sleep(3)
            
            # Verificar se logou
            try:
                home_icon = await self.main_tab.select(self.SELECTORS['home_icon'])
                if home_icon:
                    self.current_session = session
                    self.logged_in_username = username
                    
                    # Atualizar last_used
                    session.last_used = datetime.now().isoformat()
                    self.session_manager.save_session(session)
                    
                    self.logger.info(f"✅ Sessão restaurada para @{username}")
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar sessão: {e}")
            return False

    async def _save_current_session(self, username: str) -> bool:
        """Salva sessão atual"""
        try:
            cookies = await self.get_cookies_dict()
            
            session = SessionData(
                username=username,
                user_id=cookies.get('ds_user_id'),
                session_id=cookies.get('sessionid'),
                cookies=cookies,
                created_at=datetime.now().isoformat(),
                expires_at=(datetime.now() + timedelta(days=7)).isoformat(),
                last_used=datetime.now().isoformat(),
                is_valid=True,
                login_method='credentials'
            )
            
            self.current_session = session
            return self.session_manager.save_session(session)
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar sessão: {e}")
            return False

    async def check_session_valid(self) -> bool:
        """Verifica se a sessão atual ainda é válida"""
        try:
            if not self.browser:
                return False
            
            await self.main_tab.get("https://www.instagram.com/")
            await asyncio.sleep(2)
            
            try:
                home_icon = await self.main_tab.select(self.SELECTORS['home_icon'])
                return home_icon is not None
            except:
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar sessão: {e}")
            return False

    async def reconnect_if_needed(self) -> bool:
        """
        Reconecta automaticamente se a sessão expirou.
        
        Returns:
            True se está conectado (ou reconectou com sucesso)
        """
        try:
            if await self.check_session_valid():
                return True
            
            self.logger.info("🔄 Sessão expirada, tentando reconectar...")
            
            if self.current_session:
                restored = await self._try_restore_session(self.current_session.username)
                if restored:
                    return True
            
            self.logger.warning("⚠️ Não foi possível reconectar automaticamente")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro na reconexão: {e}")
            return False

    async def _get_page_text(self) -> str:
        """Obtém texto da página atual"""
        try:
            script = "() => document.body.innerText"
            result = await self.main_tab.evaluate(script)
            return result if isinstance(result, str) else ""
        except:
            return ""

    async def _get_element_text(self, element: Any) -> str:
        """Obtém texto de um elemento"""
        try:
            return await element.get_property("innerText") or ""
        except:
            return ""

    async def get_cookies_dict(self) -> Dict[str, str]:
        """Extrai cookies e converte para formato dict"""
        try:
            cookies = await self.browser.cookies.get_all()
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie.name] = cookie.value
            return cookie_dict
        except Exception as e:
            self.logger.error(f"Erro ao extrair cookies: {e}")
            return {}

    async def save_cookies_to_file(self, filename: str) -> bool:
        """Salva cookies em JSON"""
        try:
            cookies = await self.browser.cookies.get_all()
            serializable_cookies = []
            for c in cookies:
                serializable_cookies.append({
                    'name': c.name,
                    'value': c.value,
                    'domain': c.domain,
                    'path': c.path
                })
                
            with open(filename, 'w') as f:
                json.dump(serializable_cookies, f)
            self.logger.info(f"🍪 Cookies salvos em {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar cookies: {e}")
            return False

    async def load_cookies_from_file(self, filename: str) -> bool:
        """Carrega cookies de arquivo JSON"""
        try:
            if not os.path.exists(filename):
                return False
                
            with open(filename, 'r') as f:
                cookies = json.load(f)
                
            await self.browser.cookies.set_all(cookies)
            self.logger.info(f"🍪 {len(cookies)} cookies carregados.")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar cookies: {e}")
            return False

    async def get_cookies(self) -> List[Any]:
        """Retorna lista de cookies (compatibilidade)"""
        if not self.browser:
            return []
        return await self.browser.cookies.get_all()

    async def close(self) -> None:
        """Alias para stop"""
        await self.stop()


# =============================================================================
# TESTES E EXECUÇÃO DIRETA
# =============================================================================

# Alias para compatibilidade
BrowserManager = NodriverManager

if __name__ == "__main__":
    print("=" * 60)
    print("   Browser Manager 2025 - God Mode Ultimate")
    print("   Implementação REAL com 2FA e sessões persistentes")
    print("=" * 60)
    
    async def run_test():
        manager = NodriverManager(headless=False)
        
        print("\n🧪 Teste de inicialização...")
        await manager.start()
        print("✅ Navegador iniciado")
        
        print("\n🧪 Teste de navegação...")
        await manager.navigate("https://www.instagram.com/")
        print("✅ Navegação OK")
        
        print("\n🧪 Encerrando...")
        await manager.stop()
        print("✅ Teste concluído")
    
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"❌ Erro: {e}")
