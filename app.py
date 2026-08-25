import streamlit as st
import json
import os

st.set_page_config(page_title="Gerador de Atas", layout="centered", page_icon="📝")

st.title("📝 Gerador de Minutas de Atas")

# Gestão do estado da sessão (Session State)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "utilizador" not in st.session_state:
    st.session_state.utilizador = ""

# --- FLUXO 1: AUTENTICAÇÃO ---
if not st.session_state.autenticado:
    st.subheader("Autenticação")
    utilizador = st.text_input("Utilizador")
    palavra_passe = st.text_input("Palavra-passe", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar", type="primary"):
            if utilizador:
                st.session_state.autenticado = True
                st.session_state.utilizador = utilizador
                st.rerun()
            else:
                st.error("Por favor, indique o utilizador.")
    with col2:
        if st.button("Registar Novo Utilizador"):
            st.info("Fluxo alternativo: Encaminhar para formulário de registo de utilizador.")

# --- FLUXO 2: SELEÇÃO DE PROCEDIMENTO ---
else:
    st.sidebar.write(f"Sessão iniciada: **{st.session_state.utilizador}**")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

    st.header("1. Seleção do Procedimento")
    
    # Carregar dados dos procedimentos
    caminho_json = os.path.join("data", "procedimentos.json")
    procedimentos = []
    if os.path.exists(caminho_json):
        with open(caminho_json, "r", encoding="utf-8") as f:
            procedimentos = json.load(f)

    opcoes = [f"{p['id']} - {p['designacao']}" for p in procedimentos]
    opcoes.append("+ Criar Novo Procedimento")
    
    escolha = st.selectbox("Selecione o procedimento:", opcoes)
    
    if escolha == "+ Criar Novo Procedimento":
        st.subheader("Novo Procedimento (Fluxo Alternativo)")
        st.text_input("Código do Procedimento")
        st.text_input("Designação")
        st.text_input("Presidente do Júri")
        st.button("Guardar Procedimento")
    else:
        # Obter o procedimento selecionado
        proc_sel = next((p for p in procedimentos if f"{p['id']} - {p['designacao']}" == escolha), None)
        
        if proc_sel:
            st.success(f"Procedimento selecionado: **{proc_sel['designacao']}**")
            
            st.subheader("Confirmação de Dados Gerais")
            st.write(f"**Entidade:** {proc_sel.get('entidade', 'N/D')}")
            st.write(f"**Presidente do Júri:** {proc_sel['juri']['presidente']}")
            st.write(f"**Vogais:** {proc_sel['juri']['vogal1']}, {proc_sel['juri']['vogal2']}")
            
            if st.button("Avançar para a Ordem de Trabalhos", type="primary"):
                st.info("Próximo passo: Formulário dinâmico da ordem de trabalhos.")