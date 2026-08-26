import streamlit as st
import json
import os
import hashlib

# Configuração inicial da página
st.set_page_config(page_title="Gerador de Atas", layout="centered", page_icon="📝")

st.title("📝 Gerador de Minutas de Atas")

# --- FUNÇÃO DE HASHING PARA SEGURANÇA DE PALAVRAS-PASSE ---
def gerar_hash(password: str) -> str:
    """Gera um hash SHA-256 seguro a partir da palavra-passe em texto limpo."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# --- GESTÃO DE UTILIZADORES (Leitura e Escrita) ---
caminho_utilizadores = os.path.join("data", "utilizadores.json")

def carregar_utilizadores():
    if os.path.exists(caminho_utilizadores):
        with open(caminho_utilizadores, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_utilizadores(lista):
    os.makedirs("data", exist_ok=True)
    with open(caminho_utilizadores, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

# --- ESTADO DA SESSÃO (Session State) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "modo_registo" not in st.session_state:
    st.session_state.modo_registo = False
if "criar_novo_proc" not in st.session_state:
    st.session_state.criar_novo_proc = False

# ==========================================
# FLUXO 1: AUTENTICAÇÃO E REGISTO
# ==========================================
if not st.session_state.autenticado:
    utilizadores = carregar_utilizadores()

    # MODO 1B: REGISTO DE NOVO UTILIZADOR (Fluxo Alternativo)
    if st.session_state.modo_registo:
        st.subheader("Registo de Novo Utilizador")
        
        with st.form("form_registo_user"):
            st.markdown("##### Dados de Autenticação")
            novo_user = st.text_input("Nome de Utilizador (Username)").strip().lower()
            nova_pass = st.text_input("Palavra-passe", type="password")
            conf_pass = st.text_input("Confirmar Palavra-passe", type="password")
            
            st.markdown("##### Dados Pessoais e Profissionais")
            nome_completo = st.text_input("Nome Completo")
            nome_curto = st.text_input("Nome Curto (ex: Pedro Leal)")
            
            col_a, col_b = st.columns(2)
            with col_a:
                posto_categoria = st.text_input("Posto ou Categoria (ex: Capitão / Técnico Superior)")
                arma_servico = st.text_input("Arma ou Serviço (ex: Engenharia / Adm.)")
            with col_b:
                posto_encurtado = st.text_input("Posto/Categoria Encurtado (ex: Cap. / TS)")
                nim = st.text_input("NIM / Nº de Identificação")

            submeter = st.form_submit_button("Criar Registo", type="primary")
            
            if submeter:
                if not novo_user or not nova_pass or not nome_completo:
                    st.error("Por favor, preencha pelo menos o Username, Palavra-passe e Nome Completo.")
                elif nova_pass != conf_pass:
                    st.error("As palavras-passe não coincidem.")
                elif any(u["username"].lower() == novo_user for u in utilizadores):
                    st.error(f"O utilizador '{novo_user}' já existe.")
                else:
                    novo_registo = {
                        "username": novo_user,
                        "password": gerar_hash(nova_pass),
                        "nome_completo": nome_completo,
                        "nome_curto": nome_curto if nome_curto else nome_completo,
                        "posto_categoria": posto_categoria,
                        "posto_encurtado": posto_encurtado if posto_encurtado else posto_categoria,
                        "arma_servico": arma_servico,
                        "nim": nim
                    }
                    utilizadores.append(novo_registo)
                    guardar_utilizadores(utilizadores)
                    st.success("Registo criado com sucesso! Pode agora efetuar o login.")
                    st.session_state.modo_registo = False
                    st.rerun()

        if st.button("Voltar ao Login"):
            st.session_state.modo_registo = False
            st.rerun()

    # MODO 1A: LOGIN (Fluxo Principal)
    else:
        st.subheader("Autenticação")
        user_input = st.text_input("Utilizador").strip().lower()
        pass_input = st.text_input("Palavra-passe", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Entrar", type="primary"):
                pass_hash_input = gerar_hash(pass_input)
                
                user_encontrado = next(
                    (u for u in utilizadores if u["username"].lower() == user_input and u["password"] == pass_hash_input), 
                    None
                )
                
                if user_encontrado:
                    st.session_state.autenticado = True
                    st.session_state.user_data = user_encontrado
                    st.rerun()
                else:
                    st.error("Utilizador ou palavra-passe incorretos.")
                    
        with col2:
            if st.button("Registar Novo Utilizador"):
                st.session_state.modo_registo = True
                st.rerun()

# ==========================================
# FLUXO 2: SELEÇÃO DE PROCEDIMENTO
# ==========================================
else:
    user_info = st.session_state.user_data
    nome_exibicao = user_info.get("nome_curto") or user_info.get("nome_completo") or user_info.get("username")
    posto_exibicao = user_info.get("posto_encurtado", "")
    
    st.sidebar.write(f"Sessão iniciada: **{posto_exibicao} {nome_exibicao}**".strip())
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.session_state.user_data = {}
        st.session_state.criar_novo_proc = False
        st.rerun()

    st.header("1. Procedimento")
    
    # Carregar dados dos procedimentos
    caminho_procedimentos = os.path.join("data", "procedimentos.json")
    procedimentos = []
    if os.path.exists(caminho_procedimentos):
        with open(caminho_procedimentos, "r", encoding="utf-8") as f:
            procedimentos = json.load(f)

    # Input do número/código do procedimento
    cod_procedimento = st.text_input("Indique o número / código do procedimento:", placeholder="Ex: PROC-2026-001").strip()

    if cod_procedimento:
        # Procurar o procedimento pelo ID
        proc_sel = next((p for p in procedimentos if p["id"].upper() == cod_procedimento.upper()), None)
        
        # CASO 2A: O procedimento existe
        if proc_sel:
            st.session_state.criar_novo_proc = False
            st.success(f"Procedimento encontrado: **{proc_sel['designacao']}**")
            
            st.subheader("Confirmação dos Dados Gerais e do Júri")
            st.write(f"**Entidade:** {proc_sel.get('entidade', 'N/D')}")
            st.write(f"**Presidente do Júri:** {proc_sel['juri']['presidente']}")
            st.write(f"**1.º Vogal:** {proc_sel['juri']['vogal1']}")
            st.write(f"**2.º Vogal:** {proc_sel['juri']['vogal2']}")
            
            if st.button("Confirmar e Avançar para a Ordem de Trabalhos", type="primary"):
                st.info("Próximo passo: Formulário da ordem de trabalhos.")

        # CASO 2B: O procedimento NÃO existe (Fluxo Alternativo)
        else:
            st.warning(f"O procedimento com o código **'{cod_procedimento}'** não foi encontrado.")
            
            if not st.session_state.criar_novo_proc:
                if st.button(f"Pretende criar o procedimento '{cod_procedimento}'?"):
                    st.session_state.criar_novo_proc = True
                    st.rerun()
            
            # Formulário de criação de novo procedimento
            if st.session_state.criar_novo_proc:
                st.divider()
                st.subheader(f"Registo do Novo Procedimento: {cod_procedimento}")
                
                with st.form("form_novo_procedimento"):
                    designacao = st.text_input("Designação do Procedimento")
                    entidade = st.text_input("Entidade", value="Direção de Infraestruturas")
                    presidente = st.text_input("Presidente do Júri")
                    vogal1 = st.text_input("1.º Vogal")
                    vogal2 = st.text_input("2.º Vogal")
                    
                    submetido = st.form_submit_button("Guardar Procedimento", type="primary")
                    
                    if submetido:
                        if designacao and presidente:
                            novo_proc = {
                                "id": cod_procedimento,
                                "designacao": designacao,
                                "entidade": entidade,
                                "juri": {
                                    "presidente": presidente,
                                    "vogal1": vogal1,
                                    "vogal2": vogal2
                                }
                            }
                            procedimentos.append(novo_proc)
                            
                            # Guardar no ficheiro JSON
                            os.makedirs("data", exist_ok=True)
                            with open(caminho_procedimentos, "w", encoding="utf-8") as f:
                                json.dump(procedimentos, f, ensure_ascii=False, indent=2)
                            
                            st.session_state.criar_novo_proc = False
                            st.success("Procedimento guardado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Por favor, preencha a designação e o Presidente do Júri.")