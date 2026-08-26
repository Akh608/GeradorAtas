import streamlit as st
import json
import os
import hashlib
from datetime import date, time

from utils.prompt_builder import aplicar_templates_ata, construir_prompt_refinamento_ia, chamar_groq_api
from utils.pdf_generator import gerar_pdf_ata

# Configuração inicial da página
st.set_page_config(page_title="Gerador de Atas", layout="centered", page_icon="📝")
st.title("📝 Gerador de Minutas de Atas")

# --- FUNÇÃO DE HASHING PARA SEGURANÇA DE PALAVRAS-PASSE ---
def gerar_hash(password: str) -> str:
    """Gera um hash SHA-256 seguro a partir da palavra-passe em texto limpo."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# --- GESTÃO DE UTILIZADORES ---
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

def eliminar_ata_por_id(id_ata_para_remover):
    """Remove uma ata especificada do ficheiro data/atas.json."""
    atas = carregar_json(caminho_atas)
    atas_filtradas = [a for a in atas if a.get("id_ata") != id_ata_para_remover]
    guardar_json(caminho_atas, atas_filtradas)

# --- FUNÇÃO DE RENDERIZAÇÃO DE CAMPOS DO FORMULÁRIO ---
def renderizar_campo_dinamico(campo, chave_unica, valor_predefinido=None):
    """Gera o widget Streamlit adequado com base no tipo especificado no JSON e preenche com valor pré-existente se disponível."""
    tipo = campo.get("tipo")
    label = campo.get("label")
    
    if tipo == "text_input":
        val = str(valor_predefinido) if valor_predefinido is not None else ""
        return st.text_input(label, value=val, key=chave_unica)
    elif tipo == "text_area":
        val = str(valor_predefinido) if valor_predefinido is not None else ""
        return st.text_area(label, value=val, key=chave_unica)
    elif tipo == "number":
        val = int(valor_predefinido) if valor_predefinido is not None else campo.get("default", 0)
        return st.number_input(label, min_value=campo.get("min", 0), value=val, key=chave_unica)
    elif tipo == "select":
        opcoes = campo.get("opcoes", [])
        index_def = opcoes.index(valor_predefinido) if valor_predefinido in opcoes else 0
        return st.selectbox(label, options=opcoes, index=index_def, key=chave_unica)
    elif tipo == "radio":
        opcoes = campo.get("opcoes", [])
        index_def = opcoes.index(valor_predefinido) if valor_predefinido in opcoes else 0
        return st.radio(label, options=opcoes, index=index_def, key=chave_unica)
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
if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = False

# ==========================================
# FLUXO 1: AUTENTICAÇÃO E REGISTO
# ==========================================
if not st.session_state.autenticado:
    utilizadores = carregar_utilizadores()

    # MODO 1B: REGISTO DE NOVO UTILIZADOR
    if st.session_state.modo_registo:
        st.subheader("Registo de Novo Utilizador")
        
        with st.form("form_registo_user"):
            st.markdown("##### Dados de Autenticação")
            novo_user = st.text_input("Nome de Utilizador (Username)").strip().lower()
            nova_pass = st.text_input("Palavra-passe", type="password")
            conf_pass = st.text_input("Confirmar Palavra-passe", type="password")
            
            st.markdown("##### Dados Pessoais e Profissionais")
            nome_completo = st.text_input("Nome Completo")
            nome_curto = st.text_input("Nome Curto")
            
            col_a, col_b = st.columns(2)
            with col_a:
                posto_categoria = st.text_input("Posto ou Categoria")
                arma_servico = st.text_input("Arma ou Serviço")
            with col_b:
                posto_encurtado = st.text_input("Posto/Categoria Encurtado")
                nim = st.text_input("NIM / Nº de Identificação")

            submeter = st.form_submit_button("Criar Registo", type="primary")
            
            if submeter:
                if not novo_user or not nova_pass or not nome_completo:
                    st.error("Por favor, preencha os campos obrigatórios.")
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
                    st.success("Registo criado com sucesso!")
                    st.session_state.modo_registo = False
                    st.rerun()

        if st.button("Voltar ao Login"):
            st.session_state.modo_registo = False
            st.rerun()

    # MODO 1A: LOGIN
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
        st.session_state.modo_edicao = False
        if "ata_em_edicao" in st.session_state:
            del st.session_state["ata_em_edicao"]
        if "ata_corrente" in st.session_state:
            del st.session_state["ata_corrente"]
        if "texto_gerado" in st.session_state:
            del st.session_state["texto_gerado"]
        st.rerun()

    st.header("1. Procedimento e Agendamento")
    
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

            # --- CAMPOS DE DATA E HORA DA REUNIÃO ---
            st.divider()
            st.subheader("📅 Data e Horário da Reunião")
            
            # Recuperar valores em caso de edição
            ata_ed = st.session_state.get("ata_em_edicao", {})
            data_def = date.fromisoformat(ata_ed["data_reuniao"]) if "data_reuniao" in ata_ed else date.today()
            hora_inicio_def = time.fromisoformat(ata_ed["hora_inicio"]) if "hora_inicio" in ata_ed else time(10, 0)
            hora_fim_def = time.fromisoformat(ata_ed["hora_fim"]) if "hora_fim" in ata_ed else time(11, 30)

            col_dt1, col_dt2, col_dt3 = st.columns(3)
            with col_dt1:
                data_reuniao = st.date_input("Data da Reunião", value=data_def, format="DD/MM/YYYY")
            with col_dt2:
                hora_inicio = st.time_input("Hora de Início", value=hora_inicio_def)
            with col_dt3:
                hora_fim = st.time_input("Hora de Encerramento", value=hora_fim_def)

            # --- GESTÃO DE ATAS EXISTENTES DO PROCEDIMENTO ---
            st.divider()
            st.subheader("📁 Atas Registadas para este Procedimento")
            
            atas_todas = carregar_json(caminho_atas)
            atas_procedimento = [a for a in atas_todas if a.get("procedimento_id", "").upper() == proc_sel["id"].upper()]
            
            if atas_procedimento:
                opcoes_atas = ["+ Criar Nova Ata"] + [f"{a['id_ata']} (Criada por: {a.get('criado_por', 'N/D')})" for a in atas_procedimento]
                
                escolha_ata = st.selectbox(
                    "Selecione uma ata existente para editar/visualizar ou crie uma nova:",
                    options=opcoes_atas,
                    key="sel_ata_existente"
                )
                
                if escolha_ata != "+ Criar Nova Ata":
                    id_sel = escolha_ata.split(" ")[0]
                    ata_selecionada = next((a for a in atas_procedimento if a["id_ata"] == id_sel), None)
                    
                    if ata_selecionada:
                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            if st.button("✏️ Carregar Dados para Edição", type="primary", use_container_width=True):
                                st.session_state.ata_em_edicao = ata_selecionada
                                st.session_state.ata_corrente = ata_selecionada
                                st.session_state.modo_edicao = True
                                if "texto_gerado" in ata_selecionada:
                                    st.session_state.texto_gerado = ata_selecionada["texto_gerado"]
                                st.success(f"Ata {id_sel} carregada para a sessão!")
                                st.rerun()
                        with col_act2:
                            if st.button("🗑️ Apagar esta Ata", type="secondary", use_container_width=True):
                                eliminar_ata_por_id(id_sel)
                                st.success(f"Ata {id_sel} eliminada com sucesso!")
                                st.rerun()
            else:
                st.info("Ainda não existem atas registadas para este procedimento.")

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
                                "juri": {"presidente": presidente, "vogal1": vogal1, "vogal2": vogal2}
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
        
        # Leitura dos tópicos em caso de modo de edição
        topicos_pre_selecionados = []
        respostas_guardadas_map = {}
        
        if st.session_state.get("modo_edicao") and "ata_em_edicao" in st.session_state:
            ordem_guardada = st.session_state.ata_em_edicao.get("ordem_trabalhos", [])
            topicos_pre_selecionados = [t["titulo"] for t in ordem_guardada if t["titulo"] in opcoes_topicos]
            for ot in ordem_guardada:
                respostas_guardadas_map[ot["topico_id"]] = ot.get("respostas", {})
        elif topicos_disponiveis:
            topicos_pre_selecionados = [topicos_disponiveis[0]["titulo"]]

        titulos_selecionados = st.multiselect(
            "Selecione os tópicos a tratar nesta ata (por ordem):",
            options=list(opcoes_topicos.keys()),
            default=topicos_pre_selecionados
        )
        
        if titulos_selecionados:
            st.header("3. Preenchimento do Questionário Específico")
            
            # 1. QUANTIDADES FORA DO FORMULÁRIO
            quantidades_por_topico = {}
            for idx, titulo in enumerate(titulos_selecionados):
                topico_sel = opcoes_topicos[titulo]

                if "rotulo_quantidade" in topico_sel:
                    min_qtd = 0 if topico_sel['id'] == "TOP-03" else 1
                    chave_qtd = f"qtd_{idx}_{topico_sel['id']}"
                    
                    val_qtd_guardada = respostas_guardadas_map.get(topico_sel['id'], {}).get("quantidade_itens", min_qtd)

                    quantidades_por_topico[topico_sel['id']] = st.number_input(
                        f"📌 **{topico_sel['titulo']}** — {topico_sel['rotulo_quantidade']}",
                        min_value=min_qtd,
                        value=int(val_qtd_guardada),
                        step=1,
                        key=chave_qtd
                    )

            st.divider()

            # 2. FORMULÁRIO PRINCIPAL DOS TÓPICOS
            respostas_ot = []

            with st.form("form_dinamico_ot"):
                for idx, titulo in enumerate(titulos_selecionados):
                    topico_sel = opcoes_topicos[titulo]
                    st.markdown(f"### 📌 Ponto {idx+1}: {topico_sel['titulo']}")
                    
                    respostas_campos = {}
                    respostas_topico_guardadas = respostas_guardadas_map.get(topico_sel['id'], {})
                    
                    # A) Campos Repetíveis
                    if "campos_repetiveis" in topico_sel:
                        qtd = quantidades_por_topico.get(topico_sel['id'], 1)
                        respostas_campos["quantidade_itens"] = qtd
                        itens_respostas = []
                        itens_guardados = respostas_topico_guardadas.get("itens", [])
                        
                        for i in range(int(qtd)):
                            st.markdown(f"**Item / Registo n.º {i+1}**")
                            resp_item = {}
                            item_guardado_atual = itens_guardados[i] if i < len(itens_guardados) else {}
                            
                            for campo in topico_sel["campos_repetiveis"]:
                                chave = f"f_{idx}_{topico_sel['id']}_item_{i}_{campo['id']}"
                                val_def = item_guardado_atual.get(campo['id'])
                                resp_item[campo['id']] = renderizar_campo_dinamico(campo, chave, valor_predefinido=val_def)
                            itens_respostas.append(resp_item)
                            st.markdown("---")
                        
                        respostas_campos["itens"] = itens_respostas

                    # B) Campos Globais
                    campos_globais = topico_sel.get("campos_globais", topico_sel.get("campos", []))
                    for campo in campos_globais:
                        chave = f"f_{idx}_{topico_sel['id']}_g_{campo['id']}"
                        val_def = respostas_topico_guardadas.get(campo['id'])
                        respostas_campos[campo['id']] = renderizar_campo_dinamico(campo, chave, valor_predefinido=val_def)

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

            # --- AÇÕES PÓS-SUBMISSÃO DO FORMULÁRIO ---
            if submeter_ata:
                atas_existentes = carregar_json(caminho_atas)
                
                if st.session_state.get("modo_edicao") and "ata_em_edicao" in st.session_state:
                    id_ata_final = st.session_state.ata_em_edicao["id_ata"]
                    atas_existentes = [a for a in atas_existentes if a["id_ata"] != id_ata_final]
                else:
                    id_ata_final = f"ATA-{proc_sel['id']}-{len(atas_existentes)+1:02d}"

                nova_ata = {
                    "id_ata": id_ata_final,
                    "procedimento_id": proc_sel['id'],
                    "procedimento_designacao": proc_sel['designacao'],
                    "criado_por": st.session_state.user_data.get("username"),
                    "data_reuniao": data_reuniao.strftime("%Y-%m-%d"),
                    "hora_inicio": hora_inicio.strftime("%H:%M"),
                    "hora_fim": hora_fim.strftime("%H:%M"),
                    "ordem_trabalhos": respostas_ot
                }
                
                if "texto_gerado" in st.session_state:
                    nova_ata["texto_gerado"] = st.session_state.texto_gerado

                atas_existentes.append(nova_ata)
                guardar_json(caminho_atas, atas_existentes)
                
                st.session_state.ata_corrente = nova_ata
                st.session_state.modo_edicao = False
                st.success(f"Ata **{id_ata_final}** guardada com sucesso!")

            # --- GERAÇÃO E REVISÃO DA MINUTA ---
            if "ata_corrente" in st.session_state:
                st.divider()
                st.subheader("📄 Ações Disponíveis para a Ata")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("📝 Gerar Minuta Base (Templates)", use_container_width=True):
                        minuta_base = aplicar_templates_ata(st.session_state.ata_corrente, proc_sel)
                        st.session_state.texto_gerado = minuta_base

                with col_btn2:
                    if st.button("✨ Refinar Minuta via IA", type="primary", use_container_width=True):
                        with st.spinner("A refinar minuta via Groq..."):
                            minuta_base = aplicar_templates_ata(st.session_state.ata_corrente, proc_sel)
                            prompt_ia = construir_prompt_refinamento_ia(minuta_base)
                            st.session_state.texto_gerado = chamar_groq_api(prompt_ia)
                            st.rerun()

                if "texto_gerado" in st.session_state:
                    st.markdown("### Minuta Final para Revisão")
                    texto_final = st.text_area(
                        "Pode editar diretamente o texto antes de exportar para PDF:",
                        value=st.session_state.texto_gerado,
                        height=400
                    )
                    
                    # Guarda as edições manuais no estado
                    st.session_state.texto_gerado = texto_final

                    st.divider()
                    st.subheader("📥 Exportação do Documento")
                    
                    id_ata_doc = st.session_state.get("ata_corrente", {}).get("id_ata", "ATA_FINAL")
                    pdf_bytes = gerar_pdf_ata(texto_final, titulo_documento=f"MINUTA DA {id_ata_doc}")

                    st.download_button(
                        label="📄 Descarregar Minuta em PDF",
                        data=pdf_bytes,
                        file_name=f"{id_ata_doc}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )