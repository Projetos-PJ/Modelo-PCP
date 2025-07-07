# ==============================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go

# --- Configuração da Página e Logging ---
st.set_page_config(page_title="Ambiente de Projetos", layout="wide", initial_sidebar_state="expanded")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==============================================================================
# 2. CONSTANTES E ESTILOS GLOBAIS
# ==============================================================================

# --- Constantes da Interface ---
CARGOS_EXCLUIDOS = [
    "Liderança de Outbound", "Coordenador de Negócios", "Coordenador de Inovação Comercial",
    "Gerente Comercial", "Coordenador de Projetos", "Coordenador de Inovação de Projetos",
    "Gerente de Projetos",
]

DATE_COLUMNS = [
    "Início previsto Projeto 1", "Início Real Projeto 1", "Fim previsto do Projeto 1 (sem atraso)", "Fim estimado do Projeto 1 (com atraso)",
    "Início previsto Projeto 2", "Início Real Projeto 2", "Fim previsto do Projeto 2 (sem atraso)", "Fim estimado do Projeto 2 (com atraso)",
    "Início previsto Projeto 3", "Início Real Projeto 3", "Fim previsto do Projeto 3 (sem atraso)", "Fim estimado do Projeto 3 (com atraso)",
    "Início previsto Projeto 4", "Início Real Projeto 4", "Fim previsto do Projeto 4 (sem atraso)", "Fim estimado do Projeto 4 (com atraso)",
    "Início do Projeto Interno 1", "Fim do Projeto Interno 1", "Início do Projeto Interno 2", "Fim do Projeto Interno 2",
    "Início do Projeto Interno 3", "Fim do Projeto Interno 3",
]

nucleo_cores = {"NCiv": ("#cd9a0f", "#e0d19b"),
    "NCon": ("#0db54b", "#91cfa7"),
    "NDados": ("#7419BE", "#c19be0"),
    "NI": ("#c91616", "#c26868"),
    "NTec": ("#1117c3", "#7477bf")}

# --- Estilo CSS Customizado ---
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

    <style>
        /* Seus estilos globais */
        * { font-family: 'Poppins', sans-serif !important; }
        [data-testid="stHeader"] { background-color: #064381; }
        #MainMenu, footer { visibility: hidden; }

        /* 2. Estilo específico para o nosso ícone na barra lateral */
        .sidebar-icon {
            padding-top: 10px;      /* Espaço no topo */
            padding-left: 15px;     /* Espaço na esquerda */
            font-size: 2.2em;       /* Tamanho do ícone */
            color: #064381;      /* Cor do ícone */
            text-align: left;       /* Alinhamento */
        }
    </style>
    """, 
    unsafe_allow_html=True
)

# ==============================================================================
# 3. CARREGAMENTO E CACHE DE DADOS (BACKEND)
# ==============================================================================

@st.cache_data(ttl=86400)  # Cache de 1 dia
def load_data_from_source():
    """Função principal que carrega e processa os dados da fonte (Google Sheets)."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(credentials)
        planilha = client.open("PCP Auto")
        
        abas = ["NDados", "NTec", "NCiv", "NI", "NCon"]
        todas_abas = {}

        for aba in abas:
            try:
                aba_aberta = planilha.worksheet(aba)
                data = aba_aberta.get_all_values()
                if not data:
                    todas_abas[aba] = pd.DataFrame()
                    continue

                headers = data[0]
                values = data[1:]

                pcp_df = pd.DataFrame(values, columns=headers)
                pcp_df.replace('', np.nan, inplace=True)
                
                # Limpeza primária dos dados
                if 'Membro' in pcp_df.columns:
                    pcp_df.dropna(subset=['Membro'], inplace=True)
                if "Cargo no núcleo" in pcp_df.columns:
                    pcp_df = pcp_df[~pcp_df["Cargo no núcleo"].isin(CARGOS_EXCLUIDOS)]

                # Conversão de tipos de dados (Datas e Números)
                for date_col in DATE_COLUMNS:
                    if date_col in pcp_df.columns:
                        pcp_df[date_col] = pd.to_datetime(pcp_df[date_col], format="%d/%m/%Y", errors='coerce')
                
                todas_abas[aba] = pcp_df

            except Exception as e:
                logging.error(f"Erro ao processar aba '{aba}': {e}", exc_info=True)
                todas_abas[aba] = pd.DataFrame()
        return todas_abas
        
    except Exception as e:
        logging.error(f"Erro fatal ao conectar ou carregar dados: {e}", exc_info=True)
        st.error("Erro fatal de conexão. Verifique as credenciais e a API do Google Sheets.", icon="🚨")
        st.stop()


# ==============================================================================
# 4. FUNÇÕES DE LÓGICA (BACKEND)
# ==============================================================================

def escolher_nucleo(nucleo):
    """Filtra e retorna o DataFrame para o núcleo selecionado."""
    correção_nucleo = {"nciv": "NCiv", "ncon": "NCon", "ndados": "NDados", "ni": "NI", "ntec": "NTec"}
    aba = correção_nucleo.get(nucleo.lower(), nucleo)
    
    if "pcp_data" not in st.session_state:
        st.session_state.pcp_data = load_data_from_source()
        
    df = st.session_state.pcp_data.get(aba)
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Remove colunas que estejam totalmente vazias
    return df.dropna(axis=1, how='all').copy()

def calculo_disponibilidade(df, inicio_novo_projeto):
    """ Calcula as horas de disponibilidade para cada membro (versão vetorizada e segura). """
    horas = pd.Series(30.0, index=df.index)
    inicio_novo_projeto = pd.to_datetime(inicio_novo_projeto) # Garante que a data seja do tipo correto

    # --- Descontos por atividades numéricas (Acesso Seguro) ---
    if "N° Aprendizagens" in df:
        horas -= pd.to_numeric(df["N° Aprendizagens"], errors='coerce').fillna(0) * 5
    if "N° Assessorias" in df:
        horas -= pd.to_numeric(df["N° Assessorias"], errors='coerce').fillna(0) * 10

    # --- Descontos por projetos internos e cargos (Acesso Seguro) ---
    for i in range(1, 5):
        col_interno = f"Início do Projeto Interno {i}"
        if col_interno in df.columns:
            horas -= np.where(df[col_interno].notna(), 5, 0)
    
    cargos_especiais = ["SDR", "Hunter", "Analista Sênior", "Liderança de Chapter", "Product Manager"]
    if "Cargo no núcleo" in df.columns:
        # .str acessores são seguros contra valores nulos (NaN)
        is_special_role = df["Cargo no núcleo"].str.strip().str.upper().isin(cargos_especiais)
        horas -= np.where(is_special_role.fillna(False), 10, 0)
        
    # --- Descontos por projetos externos (Acesso Seguro) ---
    for i in range(1, 5):
        col_projeto = f"Projeto {i}"
        if col_projeto in df.columns:
            col_fim_estimado = f"Fim estimado do Projeto {i} (com atraso)"
            col_fim_previsto = f"Fim previsto do Projeto {i} (sem atraso)"

            # Acessa a coluna de data apenas se ela existir, senão cria uma série vazia.
            fim_estimado = df[col_fim_estimado] if col_fim_estimado in df else pd.Series(pd.NaT, index=df.index)
            fim_previsto = df[col_fim_previsto] if col_fim_previsto in df else pd.Series(pd.NaT, index=df.index)
            
            # Agora a operação .fillna() é 100% segura.
            fim_final = fim_estimado.fillna(fim_previsto)
            
            # Lógica de desconto baseada na data de fim
            data_final_existe = fim_final.notna()
            dias_restantes = (fim_final - inicio_novo_projeto).dt.days
            
            desconto_com_data = np.select(
                [dias_restantes > 14, (dias_restantes > 7) & (dias_restantes <= 14), dias_restantes <= 7],
                [10, 4, 1],
                default=0
            )
            horas -= np.where(data_final_existe, desconto_com_data, 0)
            
            # Lógica para projeto que existe mas não tem data de fim
            sem_data_final = df[col_projeto].notna() & fim_final.isna()
            horas -= np.where(sem_data_final, 10, 0)
            
    return horas

def calculo_afinidade(df, portfolio):
    """Calcula a nota de afinidade para cada membro (versão vetorizada e segura)."""

    # --- Critério 1: Satisfação com o Portfólio (Acesso Seguro) ---
    col_satisfacao = f"Satisfação com o Portfólio: {portfolio}"
    if col_satisfacao in df:
        # Se a coluna existir, calcula a satisfação a partir dela
        satisfacao = pd.to_numeric(df[col_satisfacao], errors='coerce').fillna(3.0) * 2
    else:
        # Se não existir, atribui um valor padrão para todos os membros
        satisfacao = pd.Series(6.0, index=df.index)  # (Valor padrão 3.0 * 2)

    # --- Critério 2: Capacidade Técnica (Lógica já era segura) ---
    col_capacidade = [f"Validação média do Projeto {i}" for i in range(1, 5) if f"Validação média do Projeto {i}" in df.columns]
    if col_capacidade:
        capacidade = df[col_capacidade].apply(pd.to_numeric, errors='coerce').mean(axis=1).fillna(3.0) * 2
    else:
        # Se nenhuma coluna de validação existir, atribui um valor padrão
        capacidade = pd.Series(6.0, index=df.index)

    # --- Critério 3: Saúde Mental (Acesso Seguro) ---
    # Sentimento em relação à carga
    if "Como se sente em relação à carga" in df:
        sentimento_map = {"SUBALOCADO": 10, "ESTOU SATISFEITO": 5, "SUPERALOCADO": 1}
        pontuacao_sentimento = df["Como se sente em relação à carga"].str.strip().str.upper().map(sentimento_map).fillna(5)
    else:
        pontuacao_sentimento = pd.Series(5.0, index=df.index)
        
    # Saúde mental na PJ
    if "Saúde mental na PJ" in df:
        saude_mental = pd.to_numeric(df["Saúde mental na PJ"], errors='coerce').fillna(5.0)
    else:
        saude_mental = pd.Series(5.0, index=df.index)

    saude_mental_final = (pontuacao_sentimento + saude_mental) / 2
    
    # --- Cálculo Final da Afinidade ---
    return (satisfacao + capacidade + saude_mental_final) / 3

def calculo_alocacoes(df):
    """Calcula o número total de alocações para cada membro (versão ajustada)."""
    conta = pd.Series(0, index=df.index, dtype=int)
    
    # --- 1. Contagem de projetos externos ---
    for i in range(1, 5):
        col_projeto = f"Projeto {i}"
        if col_projeto in df.columns:
            
            # --- LÓGICA ALTERADA ---
            # Agora, um projeto conta como uma alocação simplesmente se ele existe (tem um nome na célula).
            # A verificação da data de fim foi removida para esta contagem.
            ativo = df[col_projeto].notna()
            conta += ativo.astype(int)

    # --- 2. Contagem de atividades "flag" ---
    atividades_simples = ["Projeto Interno 1", "Projeto Interno 2", "Projeto Interno 3", "Cargo WI", "Cargo MKT"]
    for col in atividades_simples:
        if col in df.columns:
            conta += df[col].notna().astype(int)

    # --- 3. Soma dos valores de atividades numéricas ---
    atividades_numericas = ["N° Aprendizagens", "N° Assessorias"]
    for col in atividades_numericas:
        if col in df.columns:
            valores_numericos = pd.to_numeric(df[col], errors='coerce').fillna(0)
            conta += valores_numericos.astype(int)

    # --- 4. Contagem de cargos específicos (LÓGICA CORRIGIDA) ---
    if "Cargo no núcleo" in df.columns:
        # Adiciona 1 se o cargo contiver a palavra "Comercial"
        eh_comercial = df["Cargo no núcleo"].str.contains("Comercial", case=False, na=False)
        conta += eh_comercial.astype(int)
        
    return conta

def sincronizar_pesos():
    """Verifica qual caixa foi alterada e ajusta a outra."""
    # Identifica qual caixa de número acionou a mudança
    caixa_peso = st.session_state.get('changed_input')
    
    # Arredonda para evitar problemas com ponto flutuante (ex: 0.299999)
    if caixa_peso == 'disp':
        st.session_state.peso_afin = round(1.0 - st.session_state.peso_disp, 2)
    elif caixa_peso == 'afin':
        st.session_state.peso_disp = round(1.0 - st.session_state.peso_afin, 2)

def exibir_gantt_membro(df_membro, nucleo_selecionado, cores_por_nucleo):
    """
    Gera e exibe um gráfico de Gantt completo com todas as alocações de um membro (versão segura).
    """
    if df_membro.empty or len(df_membro) > 1:
        st.warning("Selecione um único membro para ver o gráfico de alocações.")
        return

    # --- Prepara Cores e Dados Iniciais ---
    cores_atuais = cores_por_nucleo.get(nucleo_selecionado, ("#064381", "#decda9"))
    cor_proj_externo = cores_atuais[0]
    cor_proj_interno = cores_atuais[1]
    cor_atividades_extra = "#c72fc7"

    nome_membro = df_membro['Membro'].iloc[0]
    nome_formatado = " ".join(part.capitalize() for part in nome_membro.split("."))
    st.subheader(f"Linha do Tempo de Alocações: {nome_formatado}")

    fig = go.Figure()
    yaxis_labels = []
    yaxis_pos = []
    current_pos = 0

    # --- 1. Adiciona Projetos Externos ---
    for i in range(1, 5):
        col_projeto = f"Projeto {i}"
        if col_projeto in df_membro.columns and pd.notna(df_membro[col_projeto].iloc[0]):
            col_inicio = f"Início Real Projeto {i}"
            col_fim_estimado = f"Fim estimado do Projeto {i} (com atraso)"
            col_fim_previsto = f"Fim previsto do Projeto {i} (sem atraso)"
            
            inicio = df_membro[col_inicio].iloc[0] if col_inicio in df_membro and pd.notna(df_membro[col_inicio].iloc[0]) else None
            fim = None
            if col_fim_estimado in df_membro and pd.notna(df_membro[col_fim_estimado].iloc[0]):
                fim = df_membro[col_fim_estimado].iloc[0]
            elif col_fim_previsto in df_membro and pd.notna(df_membro[col_fim_previsto].iloc[0]):
                fim = df_membro[col_fim_previsto].iloc[0]

            if pd.notna(inicio) and pd.notna(fim):
                current_pos += 1
                yaxis_labels.append(df_membro[col_projeto].iloc[0])
                yaxis_pos.append(current_pos)
                fig.add_trace(go.Scatter(x=[inicio, fim], y=[current_pos, current_pos], mode="lines", name=df_membro[col_projeto].iloc[0], line=dict(color=cor_proj_externo, width=15), showlegend=False))

    # --- 2. Adiciona Projetos Internos (LÓGICA CORRIGIDA) ---
    for i in range(1, 4):
        col_projeto = f"Projeto Interno {i}"
        if col_projeto in df_membro.columns and pd.notna(df_membro[col_projeto].iloc[0]):
            
            col_inicio = f"Início do Projeto Interno {i}"
            col_fim = f"Fim do Projeto Interno {i}"
            
            inicio = df_membro[col_inicio].iloc[0] if col_inicio in df_membro and pd.notna(df_membro[col_inicio].iloc[0]) else None
            fim = df_membro[col_fim].iloc[0] if col_fim in df_membro and pd.notna(df_membro[col_fim].iloc[0]) else None
            
            if pd.notna(inicio) and pd.notna(fim):
                current_pos += 1
                yaxis_labels.append(df_membro[col_projeto].iloc[0])
                yaxis_pos.append(current_pos)
                fig.add_trace(go.Scatter(x=[inicio, fim], y=[current_pos, current_pos], mode="lines", name=df_membro[col_projeto].iloc[0], line=dict(color=cor_proj_interno, width=15), showlegend=False))

    # --- 3. Adiciona Alocações Extras (Aprendizagens/Assessorias) ---
    hoje = datetime.today()
    trimestre_inicio_mes = ((hoje.month - 1) // 3) * 3 + 1
    data_inicio_trimestre = datetime(hoje.year, trimestre_inicio_mes, 1)
    data_fim_trimestre = (data_inicio_trimestre + pd.DateOffset(months=3)) - pd.DateOffset(days=1)

    if "N° Aprendizagens" in df_membro.columns and pd.to_numeric(df_membro["N° Aprendizagens"].iloc[0], errors='coerce') > 0:
        current_pos += 1
        label = f"Aprendizagem(ns) ({int(df_membro['N° Aprendizagens'].iloc[0])})"
        yaxis_labels.append(label)
        yaxis_pos.append(current_pos)
        fig.add_trace(go.Scatter(x=[data_inicio_trimestre, data_fim_trimestre], y=[current_pos, current_pos], mode="lines", name=label, line=dict(color=cor_atividades_extra, width=15), showlegend=False))

    if "N° Assessorias" in df_membro.columns and pd.to_numeric(df_membro["N° Assessorias"].iloc[0], errors='coerce') > 0:
        current_pos += 1
        label = f"Assessoria(s) ({int(df_membro['N° Assessorias'].iloc[0])})"
        yaxis_labels.append(label)
        yaxis_pos.append(current_pos)
        fig.add_trace(go.Scatter(x=[data_inicio_trimestre, data_fim_trimestre], y=[current_pos, current_pos], mode="lines", name=label, line=dict(color=cor_atividades_extra, width=15), showlegend=False))

    # --- Configura e exibe o gráfico ---
    if not yaxis_labels:
        st.info(f"{nome_formatado} não possui alocações com datas para exibir no gráfico.")
        return
        
    fig.update_layout(
        xaxis_title=None, yaxis_title=None,
        xaxis=dict(tickformat="%d/%m/%Y", showgrid=True, gridcolor='lightgrey'),
        yaxis=dict(tickvals=yaxis_pos, ticktext=yaxis_labels, autorange="reversed"),
        plot_bgcolor='white', margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 5. FUNÇÕES DE EXIBIÇÃO (FRONTEND)
# ==============================================================================

def card_membro(dado_coluna, media_disp, media_afin, cores_nucleo):
    """Gera o HTML para exibir um card de membro."""
    nome = " ".join(part.capitalize() for part in dado_coluna['Membro'].split("."))
    
    # Define cores com base no tipo de linha (membro vs. média)
    if "Média Do Núcleo ⚠" == nome or "Média Do Núcleo" == nome:
        primary_color, bg_color = cores_nucleo
    else:
        primary_color, bg_color = "#064381", "#decda9"

    availability_pct = min(100, (dado_coluna['Disponibilidade'] / 30.0) * 100)
    availability_color = '#2fa83b' if availability_pct > 70 else '#fbac04' if availability_pct >= 40 else '#c93220'
    
    affinity_pct = min(100, (dado_coluna['Afinidade'] / 10.0) * 100)
    affinity_color = '#2fa83b' if affinity_pct > 70 else '#fbac04' if affinity_pct >= 40 else '#c93220'
    
    avg_availability_pct = min(100, (media_disp / 30.0) * 100)
    avg_affinity_pct = min(100, (media_afin / 10.0) * 100)

    card_html = f"""
    <div style="border: 2px solid #a1a1a1; padding: 15px; border-radius: 10px; width: 700px; color:{primary_color}; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <h3>{nome}</h3>
                <p style="margin-bottom: 0;">Disponibilidade</p>
                <div style="width: 80%; background-color: {bg_color}; border-radius: 5px; height: 20px; position: relative; margin-bottom: 5px;">
                    <div style="width: {availability_pct}%; background-color: {availability_color}; height: 100%;"></div>
                    <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {avg_availability_pct}%;"></div>
                </div>
                <p style="margin-bottom: 10px;">{dado_coluna['Disponibilidade']:.2f}h / 30.0h</p>
                <p style="margin-bottom: 0;">Afinidade</p>
                <div style="width: 80%; background-color: {bg_color}; border-radius: 5px; height: 20px; position: relative;">
                    <div style="width: {affinity_pct}%; background-color: {affinity_color}; height: 100%;"></div>
                    <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {avg_affinity_pct}%;"></div>
                </div>
                <p>{dado_coluna['Afinidade']:.2f} / 10.0</p>
            </div>
            <div style="text-align: right;"><h3>{dado_coluna['Nota Final']:.2f}</h3></div>
        </div>
    </div>
    """

    # Exibe o card HTML
    st.markdown(card_html, unsafe_allow_html=True)


# ==============================================================================
# 6. LÓGICA PRINCIPAL DA INTERFACE
# ==============================================================================

# --- Navegação e Título ---
pagina = st.selectbox("Escolha uma página", ("Base Consolidada", "PCP"))
st.title(pagina)

# --- Seleção de Núcleo ---
if "nucleo" not in st.session_state: st.session_state.nucleo = None
colnan, colciv, colcon, coldados, colni, coltec = st.columns([1, 2, 2, 2, 2, 2])
if colciv.button("NCiv"): st.session_state.nucleo = "NCiv"
if colcon.button("NCon"): st.session_state.nucleo = "NCon"
if coldados.button("NDados"): st.session_state.nucleo = "NDados"
if colni.button("NI"): st.session_state.nucleo = "NI"
if coltec.button("NTec"): st.session_state.nucleo = "NTec"

# ---------------------------------
# --- PÁGINA: BASE CONSOLIDADA ---
# ---------------------------------

if pagina == "Base Consolidada":
    if st.session_state.nucleo:
        with st.spinner("Carregando dados da base..."):
            df = escolher_nucleo(st.session_state.nucleo)
            if df.empty:
                st.warning("Nenhum dado encontrado para este núcleo.")
                st.stop()

            # --- Filtros da Página ---
            colcargo, colnome, colaloc = st.columns(3)
            #filtro pelo cargo
            if "Cargo no núcleo" in df.columns:  
                opcoes_cargo = sorted(df["Cargo no núcleo"].dropna().unique())
            else:
                opcoes_cargo = ["Todos"]
            cargo_filtro = colcargo.selectbox("**Filtrar por Cargo**", options=opcoes_cargo, index= None, placeholder="Selecione o Cargo")
            #filtro pelo nome
            opcoes_nome = sorted(df["Membro"].dropna().unique())
            nome_filtro = colnome.selectbox("**Filtrar por Membro**", options=opcoes_nome, index= None, placeholder="Selecione o Membro")
            #filtro pelo número de alocações
            opcoes_aloc = ["Desalocado", "1 Alocação", "2 Alocações", "3 Alocações", "4+ Alocações"]
            aloc_filtro = colaloc.selectbox("**Filtrar por Número de Alocações**", options=opcoes_aloc, placeholder="Alocações", index=None)

            # --- Aplicação dos Filtros ---
            df['Contagem Alocações'] = calculo_alocacoes(df)
            if nome_filtro in opcoes_nome:
                df = df[df["Membro"] == nome_filtro]
            if cargo_filtro in opcoes_cargo:
                df = df[df["Cargo no núcleo"] == cargo_filtro]
            if aloc_filtro:
                map_aloc = {"Desalocado": 0, "1 Alocação": 1, "2 Alocações": 2, "3 Alocações": 3}
                if aloc_filtro in map_aloc:
                    df = df[df['Contagem Alocações'] == map_aloc[aloc_filtro]]
                elif aloc_filtro == "4+ Alocações":
                    df = df[df['Contagem Alocações'] >= 4]

            # --- Exibição dos Dados ---
            st.dataframe(df.drop(columns=["Contagem Alocações"], errors = 'ignore'), hide_index=True)

            if len(df) == 1:
                st.markdown("---")
                # Chama a nova função para desenhar o gráfico para aquele membro
                exibir_gantt_membro(df_membro=df, nucleo_selecionado=st.session_state.nucleo, cores_por_nucleo=nucleo_cores)
    
    else:
        st.info("Por favor, selecione um núcleo para visualizar a base de dados.")

# --------------------------
# --- PÁGINA: PCP ---
# --------------------------

if pagina == "PCP":
    if not st.session_state.nucleo:
        st.warning("Por favor, selecione um núcleo primeiro.", icon="⚠️")
        st.stop()

    df = escolher_nucleo(st.session_state.nucleo)
    if df.empty:
        st.warning(f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️")
        st.stop()

    # --- Filtros da Página PCP ---
    colport, col2, col3 = st.columns(3)

    portfolios = { #rever portfolios
        "NCiv": ["Completo", "Design de Interiores", "HEE", "Sondagem"], 
        "NCon": ["Gestão de Processos", "Pesquisa de Mercado", "Planejamento Estratégico"],
        "NDados": ["Ciência de Dados", "Engenharia de Dados", "Inteligência Artificial", "Inteligência de Negócios", "DSaaS"],
        "NI": ["Inovacamp", "VBaaS", "Quick Inovation"],
        "NTec": ["Product Discovery", "Desenvolvimento", "Escopo Aberto"]}
    escopo = colport.selectbox("**Portfólio**", options=portfolios[st.session_state.nucleo], index= None, placeholder="Selecione o portfólio")
    analistas = sorted(df["Membro"].unique())
    analistas_selecionados = col2.multiselect("**Analistas**", options=analistas, default=[], placeholder="Selecione os analistas")
    inicio_proj = col3.date_input("**Data de Início do Projeto**", value=datetime.today().date(), format="DD/MM/YYYY")

    # --- LÓGICA PARA SINCRONIZAR OS PESOS DA DISPONIBILIDADE E AFINIDADE + data fim projeto ---

    if 'peso_disp' not in st.session_state:
        st.session_state.peso_disp = 0.50
    if 'peso_afin' not in st.session_state:
        st.session_state.peso_afin = 0.50

    col_disp, col_afin, col6 = st.columns(3)

    with col_disp:
        st.number_input(
            "**Peso da Disponibilidade (0.3 - 0.7)**", min_value=0.3, max_value=0.7, step=0.1,
            key='peso_disp', # Chave para acessar o valor no st.session_state
            on_change=lambda: st.session_state.update(changed_input='disp') or sincronizar_pesos())

    with col_afin:
        st.number_input(
            "**Peso da Afinidade (0.3 - 0.7)**", min_value=0.3, max_value=0.7, step=0.1,
            key='peso_afin', # Chave para acessar o valor no st.session_state
            on_change=lambda: st.session_state.update(changed_input='afin') or sincronizar_pesos())   

    peso_disp = st.session_state.peso_disp
    peso_afin = st.session_state.peso_afin

    with col6:
        # Calcula uma data de fim padrão (ex: 2 meses após a data de início)
        fim_padrao = (pd.to_datetime(inicio_proj) + pd.DateOffset(months=2)).date()

        # Cria o widget para o usuário selecionar ou alterar a data de fim
        fim_proj = st.date_input("**Data de Fim do Projeto**", value=fim_padrao,      
            min_value=inicio_proj,      # Garante que a data de fim não seja anterior ao início
            format="DD/MM/YYYY")

    # --- Cálculos das Métricas ---
    df["Disponibilidade"] = calculo_disponibilidade(df, pd.Timestamp(inicio_proj))
    df["Afinidade"] = calculo_afinidade(df, escopo)
    
    max_disp, min_disp = 30, df["Disponibilidade"].min()
    range_disp = max_disp - min_disp if max_disp > min_disp else 1
    df["Nota Disponibilidade"] = 10 * (df["Disponibilidade"] - min_disp) / range_disp
    df["Nota Final"] = (df["Afinidade"] * peso_afin) + (df["Nota Disponibilidade"] * peso_disp)

    # --- Filtro e Médias para Exibição ---
    if "Todos" in analistas_selecionados or not analistas_selecionados:
        df_filtrado = df
    else:
        df_filtrado = df[df["Membro"].isin(analistas_selecionados)]

    avg_disp = df_filtrado["Disponibilidade"].mean() if not df_filtrado.empty else 0
    avg_afin = df_filtrado["Afinidade"].mean() if not df_filtrado.empty else 0
    avg_nota_final = df_filtrado["Nota Final"].mean() if not df_filtrado.empty else 0

    # --- Exibição dos Cards ---
    st.markdown("---")
    st.subheader("Membros Sugeridos para o Projeto")
    st.markdown(
        """
    <div style="margin-bottom: 20px">
    <p><strong>Entendendo as pontuações:</strong></p>
    <ul>
      <li><strong>Disponibilidade</strong>: Horas estimadas disponíveis para novas atividades (Máximo: 30h)</li>
      <li><strong>Afinidade</strong>: Pontuação (0-10) baseada em satisfação com portfólio, capacidade técnica e saúde mental</li>
      <li><strong>Nota Final</strong>: Média ponderada entre disponibilidade e afinidade</li>
    </ul>
    </div>
    """, 
        unsafe_allow_html=True,)
    
    # Aviso da Média do Núcleo
    if avg_afin < 5.0 or avg_disp < 15.0:
        nome_media = "média.do.núcleo ⚠"
    else:
        nome_media = "média.do.núcleo"

    # Criação do Card Analista Médio
    dados_da_media = {
    "Membro": nome_media,
    "Disponibilidade": avg_disp,
    "Afinidade": avg_afin,
    "Nota Final": avg_nota_final
    }
    df_filtrado.loc['media'] = dados_da_media

    # Organização e exibição dos Cards da maior nota final para a menor
    display_df = df_filtrado.sort_values(by="Nota Final", ascending=False)

    for _, row in display_df.iterrows():
        card_membro(row, avg_disp, avg_afin, nucleo_cores.get(st.session_state.nucleo))
        