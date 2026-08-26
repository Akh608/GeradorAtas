import os
import json
import requests
import streamlit as st
from datetime import datetime

def formatar_data_extenso(data_iso: str) -> str:
    """Converte '2026-08-26' para '26 de agosto de 2026'."""
    try:
        dt = datetime.strptime(data_iso, "%Y-%m-%d")
        meses = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return data_iso

def obter_groq_key() -> str:
    """Recupera a chave da API a partir do Secrets do Streamlit ou variáveis de ambiente."""
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return os.getenv("GROQ_API_KEY", "")

def chamar_groq_api(prompt: str, api_key: str = None) -> str:
    """Diagnóstico: Tenta consultar os modelos disponíveis e envia o pedido."""
    if not api_key:
        api_key = obter_groq_key()
        
    if not api_key:
        return "Erro: Chave GROQ_API_KEY não configurada em st.secrets ou variáveis de ambiente."

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    # 1. PASSO DE DIAGNÓSTICO: Consultar lista de modelos ativos na sua conta
    try:
        res_models = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
        if res_models.status_code != 200:
            return f"Erro ao validar Chave/Conta na Groq (Código {res_models.status_code}): {res_models.text}"
        
        # Extrai os IDs de todos os modelos disponíveis
        modelos_disponiveis = [m["id"] for m in res_models.json().get("data", [])]
        if not modelos_disponiveis:
            return "Erro: A sua conta Groq não devolveu nenhum modelo ativo."
            
    except Exception as e:
        return f"Erro ao ligar ao servidor da Groq: {str(e)}"

    # 2. PASSO DE EXECUÇÃO: Usa o primeiro modelo disponível devolvido pela própria Groq
    modelo_a_usar = modelos_disponiveis[0]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": modelo_a_usar,
        "messages": [
            {
                "role": "system",
                "content": "És um assistente especializado na redação de atas administrativas e contratação pública em Portugal. Responde sempre com um tom formal, rigoroso e tecnicamente correto em Português de Portugal."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Erro na geração com o modelo '{modelo_a_usar}' (Código {response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro no envio da mensagem: {str(e)}"


def carregar_json(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def aplicar_templates_ata(dados_ata: dict, dados_procedimento: dict) -> str:
    """Aplica os dados recolhidos aos moldes de texto base."""
    
    # 1. Extração dos novos campos de data e horário
    data_raw = dados_ata.get("data_reuniao", "")
    data_extenso = formatar_data_extenso(data_raw) if data_raw else "[Data por definir]"
    
    hora_inicio = dados_ata.get("hora_inicio", "[Hora início]")
    hora_fim = dados_ata.get("hora_fim", "[Hora fim]")
    
    # 2. Construção do cabeçalho formal
    cabecalho = (
        f"Aos {data_extenso}, pelas {hora_inicio} horas, reuniu o Júri do procedimento "
        f"relativo a \"{dados_procedimento.get('designacao', '')}\" ({dados_procedimento.get('id', '')}), "
        f"designado pela {dados_procedimento.get('entidade', 'Direção de Infraestruturas')}.\n\n"
        f"Estiveram presentes os seguintes membros do Júri:\n"
        f"- Presidente: {dados_procedimento.get('juri', {}).get('presidente', '')}\n"
        f"- 1.º Vogal: {dados_procedimento.get('juri', {}).get('vogal1', '')}\n"
        f"- 2.º Vogal: {dados_procedimento.get('juri', {}).get('vogal2', '')}\n\n"
    )

    # 3. Processamento dos pontos da Ordem de Trabalhos
    corpo_pontos = ""
    for ot in dados_ata.get("ordem_trabalhos", []):
        corpo_pontos += f"PONTO {ot.get('ponto_num')}: {ot.get('titulo')}\n"
        # ... (mantém a lógica existente para renderizar as respostas de cada ponto) ...
        corpo_pontos += "\n"

    # 4. Encerramento com a hora de fim
    encerramento = (
        f"\nE nada mais havendo a tratar, a reunião foi encerrada pelas {hora_fim} horas, "
        f"da qual se lavrou a presente ata que, depois de lida e aprovada, vai ser assinada pelo Júri."
    )

    return cabecalho + corpo_pontos + encerramento

def construir_prompt_refinamento_ia(texto_minuta_base: str) -> str:
    """Prepara o prompt final enviando o rascunho dos templates para o LLM apenas otimizar o tom/fluidez."""
    return f"""
És um perito em redação administrativa de Contratação Pública em Portugal.
Abaixo encontra-se a minuta estruturada de uma ata. A tua única tarefa é rever o texto, aperfeiçoar a fluidez gramatical e garantir uma linguagem formal e coesa, SEM alterar qualquer facto, dado, decisão ou resultado de votação.

MINUTA BASE:
---
{texto_minuta_base}
---

Devolve apenas o texto final revisto da ata em estilo formal.
"""