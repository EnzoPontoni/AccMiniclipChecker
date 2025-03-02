# Verificador de Contas EP Miniclip

Uma aplicação GUI sofisticada para validar contas do Miniclip, com funcionalidades de teste automatizado de login e resolução de captchas.

![Screenshot do EP Miniclip Checker](https://i.imgur.com/wRXRVDa.png)

## 🌟 Funcionalidades

- **Verificação em Massa**: Teste múltiplas contas a partir de um arquivo de texto no formato `email:senha`.
- **Resolução Automática de Captchas**: Integração com a API 2Captcha para resolver automaticamente captchas Turnstile.
- **Logs Detalhados**: Registro em tempo real do processo de verificação com mensagens de status coloridas.
- **Rastreamento de Resultados**: Arquivos separados para contas válidas e inválidas.
- **Monitoramento de Progresso**: Barra de progresso e estatísticas em tempo real.
- **Modo Claro/Escuro**: Alternância entre temas visuais para uso confortável.
- **Automação com Navegador Headless**: Utiliza Selenium com Chrome WebDriver para testes eficientes.

## 📋 Pré-requisitos

- Python 3.6+
- Navegador Chrome instalado
- Conexão com a internet
- Chave de API 2Captcha (para resolução de captchas)

## 🔧 Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/EnzoPontoni/AccMiniclipChecker.git
   cd ep-miniclip-checker
   ```

2. **Instale os pacotes necessários**
   ```bash
   pip install -r requirements.txt
   ```

   Pacotes necessários incluem:
   - PyQt5
   - requests
   - selenium
   - webdriver_manager

3. **Configure a chave de API**
   
   Abra o script e substitua a chave de API de exemplo pela sua chave real da 2Captcha:
   ```python
   TWOCAPTCHA_API_KEY = "sua_chave_api_aqui"
   ```

## 🚀 Como Usar

1. **Inicie a aplicação**
   ```bash
   python ep_miniclip_checker.py
   ```

2. **Selecione um arquivo de contas**
   - Clique no botão "Selecionar arquivo de contas"
   - Escolha um arquivo de texto com contas no formato `email:senha` (uma por linha)

3. **Inicie a verificação**
   - Clique em "Iniciar verificação" para começar a processar as contas
   - Monitore o progresso no painel de log
   - As estatísticas serão atualizadas em tempo real

4. **Visualize os resultados**
   - Contas válidas são salvas em `WORKING.txt`
   - Contas inválidas são salvas em `ERROR.txt`

## 🔄 Como Funciona

1. A aplicação lê as credenciais das contas de um arquivo de texto.
2. Para cada conta, ela:
   - Abre um navegador Chrome em modo headless
   - Navega até a página de login do Miniclip
   - Insere o email e a senha
   - Detecta o desafio Turnstile captcha
   - Envia o desafio para o serviço 2Captcha para resolução
   - Aplica a solução e envia o formulário de login
   - Verifica o login bem-sucedido procurando por elementos de logout
   - Registra o resultado (válido/inválido)

3. Os resultados são registrados em tempo real e salvos nos respectivos arquivos de saída.

## 📊 Solução de Problemas

- **Capturas de Tela**: A aplicação salva automaticamente screenshots quando ocorrem erros para ajudar na depuração.
- **Logs**: Logs detalhados ajudam a identificar problemas com contas específicas ou com o serviço de resolução de captchas.
- **Saldo da API de Captcha**: Certifique-se de que sua conta 2Captcha possui saldo suficiente para resolver captchas.

## 🔒 Considerações de Segurança

- Esta ferramenta é apenas para fins educacionais ou verificação legítima de contas.
- Nunca compartilhe suas chaves de API ou credenciais.
- A aplicação não transmite detalhes da conta para serviços de terceiros, exceto durante o processo de resolução de captchas.

## ⚙️ Opções de Configuração

Você pode modificar estas constantes no código:

```python
SITE_URL = "https://me.miniclip.com/login"  # URL de login
TWOCAPTCHA_API_KEY = "sua_chave_api_aqui"   # Chave API 2Captcha
WORKING_FILE = "WORKING.txt"                # Arquivo de saída para contas válidas
ERROR_FILE = "ERROR.txt"                    # Arquivo de saída para contas inválidas
```

## 🛠️ Personalização Avançada

- **Opções do Navegador**: Modifique as ChromeOptions no código para alterar o comportamento do navegador.
- **Timeouts**: Ajuste os tempos de espera para diferentes elementos se sua conexão com a internet for lenta.
- **Estilo da Interface**: Personalize a aparência modificando as configurações de stylesheet.

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## 🤝 Contribuições

Contribuições, problemas e solicitações de recursos são bem-vindos! Sinta-se à vontade para verificar a página de issues.

## 📧 Contato

Discord - brrxis

Link do Projeto: https://github.com/EnzoPontoni/AccMiniclipChecker

---

⭐️ Criado com paixão por Enzo Pontoni ⭐️
