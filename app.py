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

# --- FUNÇÕES DE SUPORTE E LEITURA DE DADOS ---
caminho_procedimentos = os.path.join("data", "procedimentos.json")
caminho_topicos = os.path.join("data", "topicos_ot.json")
caminho_atas = os.path.join("data", "atas.json")

def carregar_json(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_json(caminho, dados):
    os.makedirs("data", exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# --- FUNÇÃO DE RENDERIZAÇÃO DE CAMPOS DO FORMULÁRIO ---
def renderizar_campo_dinamico(campo, chave_unica):
    """Gera o widget Streamlit adequado com base no tipo especificado no JSON."""
    tipo = campo.get("tipo")
    label = campo.get("label")
    
    if tipo == "text_input":
        return st.text_input(label, key=chave_unica)
    elif tipo == "text_area":
        return st.text_area(label, key=chave_unica)
    elif tipo == "number":
        return st.number_input(label, min_value=campo.get("min", 0), value=campo.get("default", 0), key=chave_unica)
    elif tipo == "select":
        return st.selectbox(label, options=campo.get("opcoes", []), key=chave_unica)
    elif tipo == "radio":
        return st.radio(label, options=campo.get("opcoes", []), key=chave_unica)
    return None

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
# FLUXO 2 E 3: PROCEDIMENTO E FORMULÁRIOS
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
    
    procedimentos = carregar_json(caminho_procedimentos)
    cod_procedimento = st.text_input("Indique o número / código do procedimento:", placeholder="Ex: PROC-2026-001").strip()

    proc_sel = None
    if cod_procedimento:
        proc_sel = next((p for p in procedimentos if p["id"].upper() == cod_procedimento.upper()), None)
        
        if proc_sel:
            st.session_state.criar_novo_proc = False
            st.success(f"Procedimento encontrado: **{proc_sel['designacao']}**")
            
            st.subheader("Confirmação dos Dados Gerais e do Júri")
            st.write(f"**Entidade:** {proc_sel.get('entidade', 'N/D')}")
            st.write(f"**Presidente do Júri:** {proc_sel['juri']['presidente']}")
            st.write(f"**1.º Vogal:** {proc_sel['juri']['vogal1']}")
            st.write(f"**2.º Vogal:** {proc_sel['juri']['vogal2']}")

        else:
            st.warning(f"O procedimento com o código **'{cod_procedimento}'** não foi encontrado.")
            
            if not st.session_state.criar_novo_proc:
                if st.button(f"Pretende criar o procedimento '{cod_procedimento}'?"):
                    st.session_state.criar_novo_proc = True
                    st.rerun()
            
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
                            guardar_json(caminho_procedimentos, procedimentos)
                            
                            st.session_state.criar_novo_proc = False
                            st.success("Procedimento guardado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Por favor, preencha a designação e o Presidente do Júri.")

    # --- FLUXO 3: ORDEM DE TRABALHOS E FORMULÁRIO DINÂMICO ---
    if proc_sel:
        st.divider()
        st.header("2. Definição da Ordem de Trabalhos")
        
        topicos_disponiveis = carregar_json(caminho_topicos)
        opcoes_topicos = {t["titulo"]: t for t in topicos_disponiveis}
        
        titulos_selecionados = st.multiselect(
            "Selecione os tópicos a tratar nesta ata (por ordem):",
            options=list(opcoes_topicos.keys()),
            default=[topicos_disponiveis[0]["titulo"]] if topicos_disponiveis else []
        )
        
        if titulos_selecionados:
            st.header("3. Preenchimento do Questionário Específico")
            
            # 1. PERGUNTAR QUANTIDADES FORA DO FORMULÁRIO (Para reatividade imediata)
            quantidades_por_topico = {}
            for idx, titulo in enumerate(titulos_selecionados):
                topico_sel = opcoes_topicos[titulo]

                if "rotulo_quantidade" in topico_sel:
                    # Permite 0 apenas se for o Tópico 03 (Audiência Prévia sem pronúncias)
                    min_qtd = 0 if topico_sel['id'] == "TOP-03" else 1
                    chave_qtd = f"qtd_{idx}_{topico_sel['id']}"

                    quantidades_por_topico[topico_sel['id']] = st.number_input(
                        f"📌 **{topico_sel['titulo']}** — {topico_sel['rotulo_quantidade']}",
                        min_value=min_qtd,
                        value=min_qtd,
                        step=1,
                        key=chave_qtd
                    )

            st.divider()

            # 2. FORMULÁRIO PRINCIPAL COM O CICLO DE CAMPOS REPETIDOS
            respostas_ot = []

            with st.form("form_dinamico_ot"):
                for idx, titulo in enumerate(titulos_selecionados):
                    topico_sel = opcoes_topicos[titulo]
                    st.markdown(f"### 📌 Ponto {idx+1}: {topico_sel['titulo']}")
                    
                    respostas_campos = {}
                    
                    # A) Renderizar blocos repetíveis (se existirem)
                    if "campos_repetiveis" in topico_sel:
                        qtd = quantidades_por_topico.get(topico_sel['id'], 1)
                        respostas_campos["quantidade_itens"] = qtd
                        itens_respostas = []
                        
                        for i in range(int(qtd)):
                            st.markdown(f"**Item / Registo n.º {i+1}**")
                            resp_item = {}
                            for campo in topico_sel["campos_repetiveis"]:
                                # A chave 'i' garante que cada campo do item 1, 2, 3... tem estado próprio
                                chave = f"f_{idx}_{topico_sel['id']}_item_{i}_{campo['id']}"
                                resp_item[campo['id']] = renderizar_campo_dinamico(campo, chave)
                            itens_respostas.append(resp_item)
                            st.markdown("---")
                        
                        respostas_campos["itens"] = itens_respostas

                    # B) Renderizar campos globais (que não se repetem)
                    campos_globais = topico_sel.get("campos_globais", topico_sel.get("campos", []))
                    for campo in campos_globais:
                        chave = f"f_{idx}_{topico_sel['id']}_g_{campo['id']}"
                        respostas_campos[campo['id']] = renderizar_campo_dinamico(campo, chave)

                    # C) Votação do Ponto
                    st.markdown("**Deliberação / Votação:**")
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        tipo_vot = st.selectbox("Resultado:", ["Unânime", "Por Maioria"], key=f"vot_tipo_{idx}")
                    
                    voto_vencido = {}
                    if tipo_vot == "Por Maioria":
                        with col_v2:
                            membro = st.text_input("Membro com Voto Vencido:", key=f"vv_membro_{idx}")
                        decl = st.text_area("Declaração de Voto Vencido:", key=f"vv_decl_{idx}")
                        voto_vencido = {"membro": membro, "declaracao": decl}

                    respostas_ot.append({
                        "ponto_num": idx + 1,
                        "topico_id": topico_sel['id'],
                        "titulo": topico_sel['titulo'],
                        "respostas": respostas_campos,
                        "votacao": {"tipo": tipo_vot, "voto_vencido": voto_vencido}
                    })
                    st.divider()

                submeter_ata = st.form_submit_button("Guardar Ata", type="primary")

                if submeter_ata:
                    atas_existentes = carregar_json(caminho_atas)
                    nova_ata = {
                        "id_ata": f"ATA-{proc_sel['id']}-{len(atas_existentes)+1:02d}",
                        "procedimento_id": proc_sel['id'],
                        "procedimento_designacao": proc_sel['designacao'],
                        "criado_por": st.session_state.user_data.get("username"),
                        "ordem_trabalhos": respostas_ot
                    }
                    atas_existentes.append(nova_ata)
                    guardar_json(caminho_atas, atas_existentes)
                    st.success(f"Ata **{nova_ata['id_ata']}** guardada com sucesso no ficheiro `data/atas.json`!")