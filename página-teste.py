# ==============================================================================
# 1. IMPORTAÇÕES DE BIBLIOTECAS
# ==============================================================================
import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==============================================================================
# 2. CONFIGURAÇÕES GLOBAIS E ESTILO DA PÁGINA
# ==============================================================================

# --- Configuração da Página do Streamlit ---
st.set_page_config(
    page_title="Ambiente de Projetos", layout="wide", initial_sidebar_state="expanded"
)

# --- Configuração do Sistema de Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Variáveis Globais e Constantes ---
CARGOS_EXCLUIDOS = [
    "Líder de Outbound",
    "Coordenador de Negócios",
    "Coordenador de Inovação Comercial",
    "Gerente Comercial",
    "Coordenador de Projetos",
    "Coordenador de Inovação de Projetos",
    "Gerente de Projetos",
]

DATE_COLUMNS = [
    "Início Real Projeto 1", "Fim previsto do Projeto 1 (sem atraso)", "Fim estimado do Projeto 1 (com atraso)",
    "Início Real Projeto 2", "Fim previsto do Projeto 2 (sem atraso)", "Fim estimado do Projeto 2 (com atraso)",
    "Início Real Projeto 3", "Fim previsto do Projeto 3 (sem atraso)", "Fim estimado do Projeto 3 (com atraso)",
    "Início Real Projeto 4", "Fim previsto do Projeto 4 (sem atraso)", "Fim estimado do Projeto 4 (com atraso)",
    "Início do Projeto Interno 1", "Fim do Projeto Interno 1",
    "Início do Projeto Interno 2", "Fim do Projeto Interno 2",
    "Início do Projeto Interno 3", "Fim do Projeto Interno 3",
]

# --- Estilo CSS Customizado ---
st.markdown(
    """
    <style>
    * {
        font-family: 'Poppins', sans-serif !important;
    }
    /* Estilo para a barra de cabeçalho superior */
    .st-emotion-cache-ttupiz {
        position: fixed;
        top: 0px;
        left: 0px;
        right: 0px;
        height: 4.5rem;
        background: #064381;
        outline: none;
        z-index: 999990;
        display: block;
    }
    /* Estilo para as linhas divisórias */
    hr {
        border: 0;
        background-color: #064381;
        height: 2px;
    }
    hr:not([size]) {
        height: 2px;
    }
    .st-emotion-cache-10d29ip hr {
        background-color: #064381;
        border-bottom: 2px solid #064381;
    }
    /* Oculta o menu padrão e o rodapé do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    <div class="fullscreen-div"></div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. CARREGAMENTO E PREPARAÇÃO DE DADOS (BACKEND)
# ==============================================================================

@st.cache_data(ttl=86400)  # Cache expira em 1 dia (86400 segundos)
def load_pcp_data():
    """Função principal que tenta carregar os dados do Google Sheets."""
    try:
        return load_from_gsheets()
    except Exception as e:
        st.warning(f"Falha ao carregar do Google Sheets: {e}. Verifique a conexão e as credenciais.")
        st.exit()


def load_from_gsheets():
    """Conecta ao Google Sheets, baixa e pré-processa os dados de cada aba."""
    try:
        # --- Autenticação com Google Sheets API ---
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(credentials)

        # --- Conexão com a Planilha ---
        spreadsheet = client.open("PCP Auto")
        sheet_names = ["NDados", "NTec", "NCiv", "NI", "NCon"]
        all_sheets = {}

        # --- Processamento de Cada Aba ---
        for sheet_name in sheet_names:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get_all_values()

                if not data:
                    logging.warning(f"Nenhum dado encontrado na planilha: {sheet_name}")
                    all_sheets[sheet_name] = pd.DataFrame()
                    continue

                headers = data[0]
                values = data[1:]

                # Remove a coluna "Email PJ" por segurança, se existir
                if "Email PJ" in headers:
                    email_index = headers.index("Email PJ")
                    headers = [h for i, h in enumerate(headers) if i != email_index]
                    values = [[v for i, v in enumerate(row) if i != email_index] for row in values]

                pcp_df = pd.DataFrame(values, columns=headers)

                # LIMPEZA INICIAL: Remove linhas sem um membro definido
                if 'Membro' in pcp_df.columns:
                    pcp_df['Membro'].replace(['', 'None', '-'], np.nan, inplace=True)
                    pcp_df.dropna(subset=['Membro'], inplace=True)

                # Converte colunas de data para o formato correto
                for date_col in DATE_COLUMNS:
                    if date_col in pcp_df.columns:
                        pcp_df[date_col] = pd.to_datetime(pcp_df[date_col], format="%d/%m/%Y", errors="coerce").dt.strftime("%d/%m/%Y")

                # Remove cargos de liderança que não devem aparecer na análise
                if "Cargo no núcleo" in pcp_df.columns:
                    pcp_df = pcp_df[~pcp_df["Cargo no núcleo"].isin(CARGOS_EXCLUIDOS)]

                all_sheets[sheet_name] = pcp_df

            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Aba '{sheet_name}' não encontrada no documento.")
                all_sheets[sheet_name] = pd.DataFrame()
            except Exception as e:
                st.warning(f"Erro ao carregar a aba '{sheet_name}': {str(e)}")
                logging.error(f"Erro detalhado na aba '{sheet_name}': {str(e)}", exc_info=True)
                all_sheets[sheet_name] = pd.DataFrame()

        return all_sheets

    except Exception as e:
        logging.error(f"Erro ao conectar com Google Sheets: {str(e)}", exc_info=True)
        st.error(f"Erro fatal ao conectar com Google Sheets: {str(e)}", icon="🚨")
        st.stop()


# ==============================================================================
# 4. FUNÇÕES DE LÓGICA DE NEGÓCIO (BACKEND)
# ==============================================================================

def nucleo_func(nucleo_digitado):
    """Retorna o DataFrame de um núcleo específico, já limpo."""
    nucleo_digitado = nucleo_digitado.replace(" ", "").lower()
    nucleos_map = {"nciv": "NCiv", "ncon": "NCon", "ndados": "NDados", "ni": "NI", "ntec": "NTec"}

    if "pcp" not in st.session_state:
        st.session_state.pcp = load_pcp_data()

    sheet_name = nucleos_map.get(nucleo_digitado)
    if not sheet_name or sheet_name not in st.session_state.pcp:
        return None

    df = st.session_state.pcp[sheet_name].copy()
    
    # Limpeza final do DataFrame específico do núcleo
    df.replace(["None", "-", ""], np.nan, inplace=True)
    df.dropna(axis=1, how="all", inplace=True) # Remove colunas totalmente vazias
    df.dropna(subset=[df.columns[0]], inplace=True) # Garante que a primeira coluna não seja nula

    return df


def calcular_disponibilidade(analista, inicio_novo_projeto):
    """Calcula as horas de disponibilidade de um analista."""
    horas_disponiveis = 30.0

    # Descontos fixos por atividades
    try:
        n_aprendizagens = pd.to_numeric(analista.get("N° Aprendizagens", 0), errors='coerce')
        horas_disponiveis -= n_aprendizagens * 5
    except (ValueError, TypeError): pass

    try:
        n_assessorias = pd.to_numeric(analista.get("N° Assessorias", 0), errors='coerce')
        horas_disponiveis -= n_assessorias * 10
    except (ValueError, TypeError): pass

    for i in range(1, 5):
        if pd.notnull(analista.get(f"Início do Projeto Interno {i}")):
            horas_disponiveis -= 5

    if str(analista.get("Cargo no núcleo", "")).strip().upper() in ["SDR OU HUNTER", "ANALISTA SÊNIOR"]:
        horas_disponiveis -= 10

    # Desconto variável por projetos externos
    for i in range(1, 5):
        fim_estimado = analista.get(f"Fim estimado do Projeto {i} (com atraso)")
        fim_previsto = analista.get(f"Fim previsto do Projeto {i} (sem atraso)")
        fim_projeto = fim_estimado if pd.notnull(fim_estimado) else fim_previsto

        if pd.notnull(fim_projeto):
            days_left = (fim_projeto - inicio_novo_projeto).days
            if days_left > 14:
                horas_disponiveis -= 10
            elif 7 < days_left <= 14:
                horas_disponiveis -= 4
            elif days_left <= 7:
                horas_disponiveis -= 1
        else:
            # Se o projeto existe mas não tem data de fim, desconta 10h
            if pd.notnull(analista.get(f"Projeto {i}")):
                horas_disponiveis -= 10

    return horas_disponiveis


def calcular_afinidade(analista, escopo_selecionado):
    """Calcula a nota de afinidade de um analista com um projeto."""
    # Critério 1: Satisfação com o Portfólio
    satisfacao_col = f"Satisfação com o Portfólio: {escopo_selecionado}"
    satisfacao_portfolio = 3.0 # Valor padrão
    if satisfacao_col in analista and pd.notna(analista[satisfacao_col]):
        try:
            satisfacao_portfolio = float(str(analista[satisfacao_col]).replace(",", "."))
        except (ValueError, TypeError): pass
    satisfacao_portfolio *= 2

    # Critério 2: Capacidade Técnica (Validação média)
    capacidade_vals = []
    for i in range(1, 5):
        try:
            val = float(str(analista.get(f"Validação média do Projeto {i}")).replace(",", "."))
            capacidade_vals.append(val)
        except (ValueError, TypeError, AttributeError): continue
    capacidade = np.mean(capacidade_vals) if capacidade_vals else 3.0
    capacidade *= 2

    # Critério 3: Saúde Mental
    sentimento_map = {"SUBALOCADO": 10, "ESTOU SATISFEITO": 5, "SUPERALOCADO": 1}
    sentimento_nota = sentimento_map.get(str(analista.get("Como se sente em relação à carga", "")).strip().upper(), 5)
    try:
        saude_mental = float(str(analista.get("Saúde mental na PJ", "5")).replace(",", "."))
    except (ValueError, TypeError): saude_mental = 5.0
    saude_final = (sentimento_nota + saude_mental) / 2

    return (satisfacao_portfolio + capacidade + saude_final) / 3


def converte_data(df, date_cols):
    """Converte múltiplas colunas de um DataFrame para o tipo datetime."""
    df_copy = df.copy()
    for col in date_cols:
        if col in df_copy.columns:
            df_copy[col] = pd.to_datetime(df_copy[col], errors="coerce", format="%d/%m/%Y")
    return df_copy

def calcular_contagem_alocacoes(df_para_calcular):
    """Calcula o número de projetos e atividades para cada membro."""
    contagem = pd.Series(0, index=df_para_calcular.index)
    data_atual = pd.Timestamp.now()

    # 1. Conta projetos externos ativos
    for i in range(1, 5):
        col_projeto = f"Projeto {i}"
        if col_projeto in df_para_calcular.columns:
            fim_estimado = pd.to_datetime(df_para_calcular.get(f"Fim estimado do Projeto {i} (com atraso)"), errors='coerce')
            fim_previsto = pd.to_datetime(df_para_calcular.get(f"Fim previsto do Projeto {i} (sem atraso)"), errors='coerce')
            fim_final = fim_estimado.fillna(fim_previsto)
            
            condicao_ativo = df_para_calcular[col_projeto].notna() & ((fim_final.isna()) | (fim_final > data_atual))
            contagem += condicao_ativo.astype(int)

    # 2. Adiciona outras atividades que contam como alocação
    for col in ["Projeto Interno 1", "Projeto Interno 2", "Projeto Interno 3", "Cargo WI", "Cargo MKT", "N° Aprendizagens", "N° Assessorias"]:
        if col in df_para_calcular.columns:
            contagem += df_para_calcular[col].notna().astype(int)
            
    return contagem


# ==============================================================================
# 5. INTERFACE DO USUÁRIO (FRONTEND)
# ==============================================================================

# --- Barra Lateral e Navegação ---
page = st.sidebar.selectbox("Escolha uma página", ("Base Consolidada", "PCP"))
st.title(page)

# --- Inicialização do Estado da Sessão ---
if "nucleo" not in st.session_state: st.session_state.nucleo = None
if "nome" not in st.session_state: st.session_state.nome = ""
if "cargo" not in st.session_state: st.session_state.cargo = ""
if "aloc" not in st.session_state: st.session_state.aloc = None

# --- Layout dos Botões de Seleção de Núcleo ---
colnan, colciv, colcon, coldados, colni, coltec = st.columns([1, 2, 2, 2, 2, 2])
if colciv.button("NCiv"): st.session_state.nucleo = "NCiv"
if colcon.button("NCon"): st.session_state.nucleo = "NCon"
if coldados.button("NDados"): st.session_state.nucleo = "NDados"
if colni.button("NI"): st.session_state.nucleo = "NI"
if coltec.button("NTec"): st.session_state.nucleo = "NTec"


# ------------------------------------------------------------------------------
# PÁGINA: BASE CONSOLIDADA
# ------------------------------------------------------------------------------
if page == "Base Consolidada":
    if st.session_state.nucleo:
        with st.spinner("Carregando..."):
            df = nucleo_func(st.session_state.nucleo)
            df = converte_data(df, DATE_COLUMNS)

            # --- Filtros da Base Consolidada ---
            colcargo, colnome, colaloc = st.columns(3)
            nome = colnome.text_input("Nome do Membro", key="nome_input_base")
            cargo = colcargo.text_input("Cargo", key="cargo_input_base")
            alocações = colaloc.selectbox("Filtrar por Alocações", options=["Desalocado", "1 Alocação", "2 Alocações", "3 Alocações", "4+ Alocações"], key="aloc_input_base")
            
            # --- Aplicação dos Filtros ---
            if nome:
                df = df[df["Membro"].str.strip().str.lower() == nome.strip().lower()]
            if cargo:
                df = df[df["Cargo no núcleo"].str.strip().str.lower() == cargo.strip().lower()]

            if alocações == "Desalocado":
                df = df[df['Contagem_Alocacoes'] == 0]
            elif alocações == "1 Alocação":
                df = df[df['Contagem_Alocacoes'] == 1]
            elif alocações == "2 Alocações":
                df = df[df['Contagem_Alocacoes'] == 2]
            elif alocações == "3 Alocações":
                df = df[df['Contagem_Alocacoes'] == 3]
            elif alocações == "4+ Alocações":
                df = df[df['Contagem_Alocacoes'] >= 4]

            # --- Exibição dos Dados ---
            if df.empty:
                st.write("Sem informações para os dados filtrados.")
            else:
                st.dataframe(df.reset_index(drop=True), hide_index=True)
            
            # (Lógica de exibição de gráficos e cards individuais pode ser adicionada aqui)

    else:
        st.info("Por favor, selecione um núcleo para começar.")


# ------------------------------------------------------------------------------
# PÁGINA: PCP (Planejamento, Controle e Produção)
# ------------------------------------------------------------------------------
if page == "PCP":
    if not st.session_state.nucleo:
        st.warning("Por favor, selecione um núcleo primeiro.", icon="⚠️")
        st.stop()

    df = nucleo_func(st.session_state.nucleo)
    if df is None or df.empty:
        st.warning(f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️")
        st.stop()

    df = converte_data(df, DATE_COLUMNS)

    # --- Filtros da Página PCP ---
    col_escopo, col_analista, col_data = st.columns(3)
    
    # Filtro de Portfólio/Escopo
    with col_escopo:
        # Lógica para obter escopos dinamicamente (simplificada)
        escopos = ["Gestão de Processos", "Não mapeado"] # Exemplo, pode ser tornado dinâmico
        escopo = st.selectbox("**Portfólio**", options=escopos)

    # Filtro de Analistas
    with col_analista:
        analistas = sorted(df["Membro"].astype(str).unique().tolist(), key=str.lower)
        analistas_selecionados = st.multiselect("**Analista**", options=analistas, placeholder="Todos")

    # Filtro de Data de Início
    with col_data:
        inicio = st.date_input("**Data de Início do Projeto**", value=datetime.today().date(), format="DD/MM/YYYY")
    inicio_novo_projeto = pd.Timestamp(inicio)

    # Filtros de Peso e Data de Fim
    col_disp, col_afin, col_fim = st.columns(3)
    with col_disp:
        disponibilidade_weight = st.number_input("**Peso da Disponibilidade (0.3-0.7)**", 0.3, 0.7, 0.5, 0.1)
    with col_afin:
        afinidade_weight = st.number_input("**Peso da Afinidade (0.3-0.7)**", 0.3, 0.7, 0.5, 0.1)
    with col_fim:
        default_fim = (pd.Timestamp(inicio) + pd.DateOffset(months=2)).date()
        fim = st.date_input("**Data de Fim do Projeto**", value=default_fim, min_value=inicio, format="DD/MM/YYYY")

    # --- Cálculos das Métricas ---
    df["Disponibilidade"] = df.apply(lambda row: calcular_disponibilidade(row, inicio_novo_projeto), axis=1)
    df["Afinidade"] = df.apply(lambda row: calcular_afinidade(row, escopo), axis=1)
    
    # Normalização da Nota de Disponibilidade
    max_disp, min_disp = 30, df["Disponibilidade"].min()
    range_disp = max_disp - min_disp
    df["Nota Disponibilidade"] = 10 * (df["Disponibilidade"] - min_disp) / range_disp if range_disp != 0 else 10

    # Cálculo da Nota Final com pesos
    df["Nota Final"] = (df["Afinidade"] * afinidade_weight) + (df["Nota Disponibilidade"] * disponibilidade_weight)

    # --- Filtragem e Médias ---
    df_filtrado = df[df["Membro"].isin(analistas_selecionados)] if analistas_selecionados else df
    
    if not df_filtrado.empty:
        dispo_media = df_filtrado["Disponibilidade"].mean()
        afini_media = df_filtrado["Afinidade"].mean()
    else:
        dispo_media, afini_media = 0, 0
    
    # --- Exibição dos Resultados ---
    st.markdown("---")
    st.subheader("Membros Sugeridos para o Projeto")
    st.markdown("""
    <div style="margin-bottom: 20px">
    <p><strong>Entendendo as pontuações:</strong></p>
    <ul>
      <li><strong>Disponibilidade</strong>: Horas estimadas disponíveis para novas atividades (Máximo: 30h)</li>
      <li><strong>Afinidade</strong>: Pontuação (0-10) baseada em satisfação, capacidade e saúde mental</li>
      <li><strong>Nota Final</strong>: Média ponderada entre disponibilidade e afinidade</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- Geração dos Cards de Resultado ---
    display_df = df_filtrado.sort_values(by="Nota Final", ascending=False)

    for index, row in display_df.iterrows():
        membro_nome = " ".join([part.capitalize() for part in row['Membro'].split(".")])
        
        st.markdown(f"""
        <div style="border: 2px solid #a1a1a1; padding: 15px; border-radius: 10px; width: 700px; color:#064381; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <h3>{membro_nome}</h3>
                    
                    <p style="margin-bottom: 0px;">Disponibilidade</p>
                    <div style="width: 80%; background-color: #decda9; border-radius: 5px; height: 20px; position: relative; margin-bottom: 5px;">
                        <div style="width: {min(100, (row['Disponibilidade'] / 30.0) * 100)}%; background-color: {'#2fa83b' if row['Disponibilidade'] > 20 else '#fbac04' if row['Disponibilidade'] >= 10 else '#c93220'}; height: 100%;"></div>
                        <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {min(100, (dispo_media / 30.0) * 100)}%;"></div>
                    </div>
                    <p style="margin-bottom: 10px;">{row['Disponibilidade']:.2f}h / 30.0h</p>

                    <p style="margin-bottom: 0px;">Afinidade</p>
                    <div style="width: 80%; background-color: #decda9; border-radius: 5px; height: 20px; position: relative; margin-bottom: 5px;">
                        <div style="width: {min(100, (row['Afinidade'] / 10.0) * 100)}%; background-color: {'#2fa83b' if row['Afinidade'] > 7 else '#fbac04' if row['Afinidade'] >= 4 else '#c93220'}; height: 100%;"></div>
                        <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {min(100, (afini_media / 10.0) * 100)}%;"></div>
                    </div>
                    <p>{row['Afinidade']:.2f} / 10.0</p>
                </div>
                <div style="text-align: right;">
                    <h3>{row['Nota Final']:.2f}</h3>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)