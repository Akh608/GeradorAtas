# 📝 Gerador de Minutas de Atas

Aplicação web desenvolvida em **Python** e **Streamlit** para automação, gestão e refinamento de minutas de atas administrativas e de contratação pública.

## 🚀 Funcionalidades

- **Autenticação de Utilizadores:** Sistema simples de login e registo com encriptação SHA-256 local.
- **Gestão de Procedimentos e Júris:** Associação dinâmica de atas a processos de contratação.
- **Formulários Dinâmicos:** Geração de questionários específicos por tópicos e pontos da ordem de trabalhos.
- **Refinamento com IA (Groq Cloud):** Integração com o modelo `llama-3.1-8b-instant` via API REST para uma linguagem formal e rigorosa em Português de Portugal.
- **Exportação em PDF:** Geração direta de documentos formatados (A4) em memória através do ReportLab.

## 🛠️ Tecnologias Utilizadas

- **Interface:** [Streamlit](https://streamlit.io/)
- **Processamento de PDF:** [ReportLab](https://www.reportlab.com/)
- **Integração de IA:** API REST da [Groq Cloud](https://groq.com/)
- **Linguagem:** Python 3.10+

## ⚙️ Configuração e Instalação

### 1. Clonar o repositório

  bash:
  git clone [https://github.com/](https://github.com/)<teu-utilizador>/<nome-do-repo>.git
  cd <nome-do-repo>


### 2. Criar ambiente virtual e instalar dependências

  bash:
  python3 -m venv venv
  source venv/bin/activate
  pip install streamlit requests reportlab


### 3. Configurar a Chave da API (Secrets)
  Cria o ficheiro .streamlit/secrets.toml na raiz do projeto e adiciona a tua chave da Groq:

  GROQ_API_KEY = "gsk_a_tua_chave_aqui"


### 4. Executar a Aplicação

  streamlit run app.py


## 📂 Estrutura do Projeto

├── app.py                   # Aplicação principal Streamlit
├── utils/
│   ├── prompt_builder.py    # Templates de ata e integração com a API da Groq
│   └── pdf_generator.py     # Gerador de relatórios em PDF com ReportLab
├── data/                    # Base de dados em JSON (utilizadores, atas, procedimentos)
└── .streamlit/              # Ficheiros de configuração local (secrets)


