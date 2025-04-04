import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Ambiente de Projetos", layout="wide", initial_sidebar_state="expanded"
)

# Configurando o logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Lista de cargos a serem excluídos
cargos_excluidos = [
    "Líder de Outbound",
    "Coordenador de Negócios",
    "Coordenador de Inovação Comercial",
    "Gerente Comercial",
    "Coordenador de Projetos",
    "Coordenador de Inovação de Projetos",
    "Gerente de Projetos",
]

page = st.sidebar.selectbox("Escolha uma página", ("Base Consolidada", "PCP"))

# Definindo o estilo CSS para o div
st.markdown(
    """
    <style>
    * {
        font-family: 'Poppins', sans-serif !important;
    }

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
    hr {
        border: 0;
        background-color: #064381;  /* Cor do tracinho */
        height: 2px;  /* Definindo diretamente a altura */
    }

    hr:not([size]) {
        height: 2px;  /* Garantindo que a altura será 2px para hr sem atributo size para manter a consistência */
    }
    .st-emotion-cache-10d29ip hr {

        background-color: #064381;
        border-bottom: 2px solid #064381;
    }
    #MainMenu {visibility: hidden;}
    footer {visivility: hidden;}
    </style>
    <div class="fullscreen-div">
    </div>
    """,
    unsafe_allow_html=True,
)

# O título agora aparecerá sobre o 'div'
if page == "Base Consolidada":
    st.title("Base Consolidada")
if page == "PCP":
    st.title("PCP")

date_columns = [
    "Início Real Projeto 1",
    "Fim previsto do Projeto 1 (sem atraso)",
    "Fim estimado do Projeto 1 (com atraso)",
    "Início Real Projeto 2",
    "Fim previsto do Projeto 2 (sem atraso)",
    "Fim estimado do Projeto 2 (com atraso)",
    "Início Real Projeto 3",
    "Fim previsto do Projeto 3 (sem atraso)",
    "Fim estimado do Projeto 3 (com atraso)",
    "Início Real Projeto 4",
    "Fim previsto do Projeto 4 (sem atraso)",
    "Fim estimado do Projeto 4 (com atraso)",
    "Início do Projeto Interno 1",
    "Início do Projeto Interno 2",
    "Início do Projeto Interno 3",
    "Fim do Projeto Interno 1",
    "Fim do Projeto Interno 2",
    "Fim do Projeto Interno 3",
]


# Função para carregar os dados do Google Sheets e armazená-los em cache para otimizar o desempenho.
# O cache é limpo a cada 24 horas (86400 segundos) para garantir que os dados sejam atualizados periodicamente.
# Add a button to clear the cache manually
if st.sidebar.button("Atualizar Dados"):
    st.cache_data.clear()


@st.cache_data(ttl=86400)
def load_pcp_data():
    """
    Carrega os dados do Google Sheets, aplicando transformações e otimizações para uso na aplicação.

    Operações realizadas:
    - Autentica-se no Google Sheets API usando credenciais armazenadas no arquivo secrets.toml.
    - Abre a planilha especificada pelo nome.
    - Carrega as planilhas especificadas na lista sheet_names.
    - Converte colunas de data para o formato correto.
    - Converte colunas categóricas para otimizar o uso de memória.
    - Remove cargos excluídos da base de dados.
    - Retorna um dicionário contendo os DataFrames carregados.

    Em caso de erros, logs são registrados e mensagens de erro são exibidas na interface.

    Returns:
        dict: Um dicionário onde as chaves são os nomes das planilhas e os valores são os DataFrames correspondentes.
              Retorna um dicionário vazio em caso de falha ao carregar os dados.
    """
    try:
        # Define o escopo de autenticação para acessar o Google Sheets API.
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # Recupera as credenciais da conta de serviço do arquivo secrets.toml.
        try:
            creds_info = st.secrets["gcp_service_account"]
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                creds_info, scope
            )
        except KeyError:
            st.error(
                "Erro: Credenciais de serviço não encontradas no arquivo secrets.toml.",
                icon="🚨",
            )
            st.stop()

        # Conecta-se ao Google Sheets API usando as credenciais autorizadas.
        client = gspread.authorize(credentials)

        # Abre a planilha pelo nome.
        spreadsheet_name = "PCP Auto"
        try:
            spreadsheet = client.open(spreadsheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            st.error(
                f"Planilha '{spreadsheet_name}' não encontrada no Google Sheets.",
                icon="🚨",
            )
            st.stop()
        except gspread.exceptions.APIError as e:
            st.error(f"Erro na API do Google Sheets: {e}", icon="🚨")
            st.stop()

        # Especifica quais planilhas devem ser carregadas.
        sheet_names = ["NDados", "NTec", "NCiv", "NI", "NCon"]

        # Define os tipos de dados das colunas para otimizar o uso de memória.
        dtype_dict = {
            "Membro": "category",
            "Cargo no núcleo": "category",
            "Área de atuação": "category",
            "Como se sente em relação à carga": "category",
        }

        # Dicionário para armazenar todos os DataFrames.
        all_sheets = {}

        # Processa cada planilha.
        for sheet_name in sheet_names:
            try:
                # Obtém a planilha.
                worksheet = spreadsheet.worksheet(sheet_name)

                # Obtém todos os valores.
                data = worksheet.get_all_values()

                # Se não houver dados na planilha, registra um aviso e continua.
                if not data:
                    logging.warning(f"Nenhum dado encontrado na planilha: {sheet_name}")
                    all_sheets[sheet_name] = pd.DataFrame()
                    continue

                # Extrai os cabeçalhos e os valores.
                headers = data[0]
                values = data[1:]

                # Cria o DataFrame.
                pcp_df = pd.DataFrame(values, columns=headers)

                # Processa as colunas de data.
                for date_col in date_columns:
                    if date_col in pcp_df.columns:
                        try:
                            # Converte para datetime e formata consistentemente.
                            pcp_df[date_col] = pd.to_datetime(
                                pcp_df[date_col], format="%d/%m/%Y", errors="coerce"
                            )
                            # Formata apenas valores não NaT.
                            pcp_df[date_col] = pcp_df[date_col].apply(
                                lambda x: (
                                    x.strftime("%d/%m/%Y") if pd.notna(x) else None
                                )
                            )
                        except Exception as e:
                            logging.warning(
                                f"Erro ao converter coluna de data '{date_col}' na aba {sheet_name}: {e}"
                            )

                # Converte as colunas categóricas para otimizar o uso de memória.
                for col, dtype in dtype_dict.items():
                    if col in pcp_df.columns:
                        pcp_df[col] = pcp_df[col].astype(dtype)

                # Remove os cargos excluídos.
                if "Cargo no núcleo" in pcp_df.columns:
                    pcp_df = pcp_df[~pcp_df["Cargo no núcleo"].isin(cargos_excluidos)]

                # Armazena o DataFrame processado.
                all_sheets[sheet_name] = pcp_df

            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Planilha '{sheet_name}' não encontrada no documento.")
                all_sheets[sheet_name] = pd.DataFrame()
            except Exception as e:
                st.warning(f"Erro ao carregar planilha '{sheet_name}': {str(e)}")
                logging.error(
                    f"Erro ao carregar planilha '{sheet_name}': {str(e)}", exc_info=True
                )
                all_sheets[sheet_name] = pd.DataFrame()

        # Se nenhuma planilha foi carregada com sucesso, exibe um aviso.
        if not all_sheets:
            st.warning("Nenhuma planilha foi carregada com sucesso.")

        return all_sheets

    except Exception as e:
        logging.error(f"Erro ao conectar com Google Sheets: {str(e)}", exc_info=True)
        st.error(f"Erro ao conectar com Google Sheets: {str(e)}", icon="🚨")
        st.stop()


def nucleo_func(nucleo_digitado):
    """
    Função para obter o DataFrame correspondente ao núcleo digitado.

    Args:
        nucleo_digitado (str): Nome do núcleo digitado pelo usuário.

    Returns:
        pd.DataFrame: DataFrame correspondente ao núcleo, com colunas e valores processados.
    """
    # Normaliza a entrada para evitar problemas com espaços e maiúsculas/minúsculas
    nucleo_digitado = nucleo_digitado.replace(" ", "").lower()

    # Mapeamento de nomes normalizados para nomes de abas
    nucleos_map = {
        "nciv": "NCiv",
        "ncon": "NCon",
        "ndados": "NDados",
        "ni": "NI",
        "ntec": "NTec",
    }

    # Verifica se os dados do PCP já estão carregados no session_state
    if "pcp" not in st.session_state:
        st.session_state.pcp = load_pcp_data()

    # Obtém o nome da aba usando o mapeamento
    sheet_name = nucleos_map.get(nucleo_digitado)

    # Retorna None se o núcleo não for encontrado ou não existir na planilha
    if not sheet_name or sheet_name not in st.session_state.pcp:
        return None

    # Retorna uma cópia do DataFrame já pré-processado
    df = st.session_state.pcp[sheet_name].copy()

    # Substitui valores "None" e "-" por NaN para facilitar o processamento
    df = df.replace("None", None).replace("-", None)

    # Remove colunas que estão completamente vazias
    df = df.dropna(axis=1, how="all")

    # Identifica e remove colunas que contêm apenas strings vazias ou "None"
    cols_to_drop = []
    for col in df.columns:
        non_na_values = df[col].dropna()
        if len(non_na_values) == 0 or (
            non_na_values.astype(str)
            .str.strip()
            .str.lower()
            .isin(["", "none", "nan"])
            .all()
        ):
            cols_to_drop.append(col)

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    return df


# Inicializa session_state para manter os valores dos filtros
if "nucleo" not in st.session_state:
    st.session_state.nucleo = None
if "escopo" not in st.session_state:
    st.session_state.escopo = None
if "nome" not in st.session_state:
    st.session_state.nome = ""
if "cargo" not in st.session_state:
    st.session_state.cargo = ""
if "aloc" not in st.session_state:
    st.session_state.aloc = None

# Layout dos botões de seleção de núcleo
colnan, colciv, colcon, coldados, colni, coltec = st.columns([1, 2, 2, 2, 2, 2])
with colciv:
    if st.button("NCiv"):
        st.session_state.nucleo = "NCiv"
with colcon:
    if st.button("NCon"):
        st.session_state.nucleo = "NCon"
with coldados:
    if st.button("NDados"):
        st.session_state.nucleo = "NDados"
with colni:
    if st.button("NI"):
        st.session_state.nucleo = "NI"
with coltec:
    if st.button("NTec"):
        st.session_state.nucleo = "NTec"


def converte_data(df, date_columns):
    """
    Converte colunas de data em um DataFrame para o formato datetime.

    Args:
        df (pd.DataFrame): DataFrame contendo as colunas de data.
        date_columns (list): Lista de nomes das colunas que devem ser convertidas.

    Returns:
        pd.DataFrame: DataFrame com as colunas de data convertidas.
    """
    df_copy = df.copy()
    for col in date_columns:
        if col in df_copy.columns:
            try:
                # Converte para string antes de aplicar a conversão para datetime
                df_copy[col] = df_copy[col].astype(str)
                pd.set_option("future.no_silent_downcasting", True)
                result = df_copy[col].replace("nan", np.nan)
                pd.set_option("future.no_silent_downcasting", False)
                df_copy[col] = result.infer_objects(copy=False)
                df_copy[col] = pd.to_datetime(
                    df_copy[col], errors="coerce", format="%d/%m/%Y"
                )
            except Exception as e:
                logging.error(f"Erro ao converter coluna '{col}': {e}")
    return df_copy


if page == "Base Consolidada":
    # Carregar o núcleo selecionado
    with st.spinner("Carregando..."):
        if st.session_state.nucleo != None:
            df = nucleo_func(st.session_state.nucleo)

            def batch_convert_dates(df, columns, date_format="%d/%m/%Y"):
                for col in columns:
                    if col in df.columns:
                        # Converte para datetime e mantém como datetime (sem converter para string)
                        df[col] = pd.to_datetime(
                            df[col], format=date_format, errors="coerce"
                        )
                return df

            # Lista de colunas de datas para conversão
            date_columns_to_convert = [
                "Início previsto Projeto 1",
                "Início Real Projeto 1",
                "Fim previsto do Projeto 1 (sem atraso)",
                "Fim estimado do Projeto 1 (com atraso)",
                "Início previsto Projeto 2",
                "Início Real Projeto 2",
                "Fim previsto do Projeto 2 (sem atraso)",
                "Fim estimado do Projeto 2 (com atraso)",
                "Início Real Projeto 4",
                "Fim previsto do Projeto 4 (sem atraso)",
                "Fim estimado do Projeto 4 (com atraso)",
                "Início previsto Projeto 3",
                "Início Real Projeto 3",
                "Fim previsto do Projeto 3 (sem atraso)",
                "Fim estimado do Projeto 3 (com atraso)",
                "Início previsto Projeto 4",
                "Início Real Projeto 4",
                "Fim previsto do Projeto 4 (sem atraso)",
                "Fim estimado do Projeto 4 (com atraso)",
                "Início do Projeto Interno 1",
                "Fim do Projeto Interno 1",
                "Início do Projeto Interno 2",
                "Fim do Projeto Interno 2",
                "Início do Projeto Interno 3",
                "Fim do Projeto Interno 3",
            ]
            # Converte as colunas de data para o formato datetime
            df = batch_convert_dates(df, date_columns_to_convert)

            # Definição de filtros em três colunas (cargo, nome, alocação)
            colcargo, colnome, colaloc = st.columns(3)

            # Função para atualizar o estado do nome do membro
            def update_nome():
                st.session_state.nome = st.session_state.nome_input

            # Campo para filtrar por nome do membro
            with colnome:
                nome = st.text_input(
                    "Nome do Membro",
                    placeholder="Membro",
                    value=st.session_state.nome if st.session_state.nome else None,
                    key="nome_input",
                    on_change=update_nome,
                )

            # Opções de filtro de alocação
            opcoes = [
                "Desalocado",
                "1 Alocação",
                "2 Alocações",
                "3 Alocações",
                "4+ Alocações",
            ]

            # Função para atualizar o estado do cargo
            def update_cargo():
                st.session_state.cargo = st.session_state.cargo_input

            # Campo para filtrar por cargo
            with colcargo:
                cargo = st.text_input(
                    "Cargo",
                    placeholder="Cargo",
                    value=st.session_state.cargo if st.session_state.cargo else None,
                    key="cargo_input",
                    on_change=update_cargo,
                )

            # Função para atualizar o estado das alocações
            def update_aloc():
                # Define como None se nada for selecionado, ou o valor único se apenas um for selecionado
                if st.session_state.aloc_input:
                    st.session_state.aloc = (
                        st.session_state.aloc_input[0]
                        if len(st.session_state.aloc_input) == 1
                        else None
                    )
                else:
                    st.session_state.aloc = None

            # Campo para filtrar por nível de alocação
            with colaloc:
                # Prepara valores padrão com base no session state
                default_values = (
                    [st.session_state.aloc]
                    if st.session_state.aloc and st.session_state.aloc in opcoes
                    else []
                )

                aloc = st.multiselect(
                    "Alocações",
                    placeholder="Alocações",
                    options=opcoes,
                    default=default_values,
                    key="aloc_input",
                    on_change=update_aloc,
                )

                # Atualiza o session state com a primeira opção selecionada ou None
                if aloc:
                    st.session_state.aloc = aloc[0] if len(aloc) == 1 else None

                # Aplica filtros ao DataFrame
                if nome:
                    df = df[
                        df["Membro"].str.strip().str.lower() == nome.strip().lower()
                    ]
                if cargo:
                    df = df[df["Cargo no núcleo"] == cargo]

            # Processamento adicional se filtro de alocação estiver ativo
            if aloc:
                # Mapeamento de texto para valores numéricos de alocação
                opcoes_valor_map = {
                    "Desalocado": 0,
                    "1 Alocação": 1,
                    "2 Alocações": 2,
                    "3 Alocações": 3,
                    "4+ Alocações": 4,
                }

                # Data atual para comparar com datas de fim
                data_atual = datetime.today()

                # Verifica se um projeto está ativo (não finalizado)
                def projeto_ativo(row, col_projeto, col_fim_estimado, col_fim_previsto):
                    if pd.isna(row[col_projeto]):
                        return False

                    fim_estimado = row.get(col_fim_estimado)
                    fim_previsto = row.get(col_fim_previsto)
                    fim_projeto = (
                        fim_estimado if pd.notna(fim_estimado) else fim_previsto
                    )

                    return pd.notna(fim_projeto) and fim_projeto > data_atual

                # Conta alocações ativas de cada membro
                projeto_cols = []
                for i in range(1, 4):  # Projetos 1 a 3
                    col_projeto = f"Projeto {i}"
                    col_fim_estimado = f"Fim estimado do Projeto {i} (com atraso)"
                    col_fim_previsto = f"Fim previsto do Projeto {i} (sem atraso)"

                    if col_projeto in df.columns:
                        projeto_cols.append(
                            (col_projeto, col_fim_estimado, col_fim_previsto)
                        )

                # Inicializa contador de alocações para cada membro
                alocacoes = pd.Series(0, index=df.index)

                # Contabiliza projetos externos ativos
                for col_projeto, col_fim_estimado, col_fim_previsto in projeto_cols:
                    alocacoes += df.apply(
                        lambda row: (
                            1
                            if projeto_ativo(
                                row, col_projeto, col_fim_estimado, col_fim_previsto
                            )
                            else 0
                        ),
                        axis=1,
                    )

                # Contabiliza projetos internos ativos
                for i in range(1, 3):
                    col_projeto = f"Projeto Interno {i}"
                    col_fim = f"Fim do Projeto Interno {i}"
                    col_inicio = f"Início do Projeto Interno {i}"

                    if col_projeto in df.columns:
                        if col_fim in df.columns:
                            # Considera ativo se tem data fim posterior à data atual
                            alocacoes += df.apply(
                                lambda row: (
                                    1
                                    if (
                                        pd.notna(row[col_projeto])
                                        and pd.notna(row[col_fim])
                                        and row[col_fim] > data_atual
                                    )
                                    else 0
                                ),
                                axis=1,
                            )
                        elif col_inicio in df.columns:
                            # Se não tem data fim, considera ativo se tem data início
                            alocacoes += df.apply(
                                lambda row: (
                                    1
                                    if (
                                        pd.notna(row[col_projeto])
                                        and pd.notna(row[col_inicio])
                                    )
                                    else 0
                                ),
                                axis=1,
                            )

                # Contabiliza cargos adicionais como alocações
                if "Cargo WI" in df.columns:
                    alocacoes += df["Cargo WI"].notna().astype(int)

                if "Cargo MKT" in df.columns:
                    alocacoes += df["Cargo MKT"].notna().astype(int)

                # Contabiliza atividades de desenvolvimento como alocações
                if "N° Aprendizagens" in df.columns:
                    alocacoes += df["N° Aprendizagens"].fillna(0)

                if "N° Assessorias" in df.columns:
                    alocacoes += df["N° Assessorias"].fillna(0)

                # Limita o número máximo de alocações a 4
                alocacoes = alocacoes.clip(upper=4)

                # Filtra o DataFrame conforme os valores selecionados no filtro
                valores_filtro = [opcoes_valor_map[opt] for opt in aloc]
                df = df[alocacoes.isin(valores_filtro)]

                if df.empty:
                    st.write("Sem informações para os dados filtrados")
                else:
                    try:
                        # Prepara DataFrame para exibição
                        df_display = df.copy().reset_index(drop=True)
                        df_display = df_display.replace(["None", "-"], None)

                        # Exibe o DataFrame sem índice
                        st.dataframe(df_display, hide_index=True)
                    except Exception as e:
                        st.error(f"Erro ao exibir dados: {e}")

                st.write("---")

                # Obtém datas de início e fim do trimestre atual
                def get_quarter_dates():
                    current_year = datetime.today().year
                    current_month = datetime.today().month
                    quarter_start_month = ((current_month - 1) // 3) * 3 + 1
                    quarter_end_month = quarter_start_month + 2

                    # Calcula último dia do mês final do trimestre
                    ultimo_dia = (
                        datetime(current_year, quarter_end_month, 1)
                        + pd.Timedelta(days=31)
                        - pd.Timedelta(
                            days=datetime(current_year, quarter_end_month, 1).day
                        )
                    )

                    return (datetime(current_year, quarter_start_month, 1), ultimo_dia)

                if nome:
                    # Adiciona as datas do trimestre ao DataFrame
                    df["Inicio trimestre"], df["Fim trimestre"] = get_quarter_dates()

                    # Remove colunas vazias para simplificar a visualização
                    df = df.dropna(axis=1, how="all")

                    # Formata o nome para exibição (capitaliza cada parte)
                    nome_formatado = " ".join(
                        [part.capitalize() for part in nome.split(".")] if nome else []
                    )

                    st.subheader(nome_formatado)
                    colunas = df.columns
                    pontos = []
                    yaxis = []
                    axis = 0

                    # Inicia criação do gráfico de linha do tempo
                    fig = go.Figure()

                def adicionar_projeto_ao_grafico(
                    df, tipo, numero, cor, axis, pontos, yaxis, fig
                ):
                    """
                    Adiciona um projeto ao gráfico de linha do tempo.

                    Args:
                        df: DataFrame contendo os dados do projeto
                        tipo: Tipo de projeto ('externo' ou 'interno')
                        numero: Número do projeto
                        cor: Cor para o traço (não utilizado - pode ser removido)
                        axis, pontos, yaxis: Parâmetros de controle do eixo Y
                        fig: Objeto figura do Plotly

                    Returns:
                        Tupla (axis, pontos, yaxis) atualizada
                    """
                    col_projeto = (
                        f"Projeto {numero}"
                        if tipo == "externo"
                        else f"Projeto Interno {numero}"
                    )

                    # Verifica se o projeto existe e não é NaN
                    if col_projeto not in df.columns or pd.isna(
                        df[col_projeto].iloc[0]
                    ):
                        return axis, pontos, yaxis

                    # Define coluna de início e fim baseado no tipo
                    if tipo == "externo":
                        # Determina a data de fim (prioriza estimado com atraso)
                        funcionando = True
                        try:
                            fim_col = f"Fim estimado do Projeto {numero} (com atraso)"
                            df[f"Fim Projeto {numero}"] = df[fim_col]
                        except:
                            try:
                                fim_col = (
                                    f"Fim previsto do Projeto {numero} (sem atraso)"
                                )
                                df[f"Fim Projeto {numero}"] = df[fim_col]
                            except:
                                st.error(
                                    f"Não foi possível determinar o fim do projeto {df[col_projeto].iloc[0]}",
                                    icon="⚠",
                                )
                                funcionando = False

                        if funcionando:
                            inicio_col = f"Início Real Projeto {numero}"
                            fim_col = f"Fim Projeto {numero}"
                            # Paleta de cores para projetos externos
                            cores_projetos = [
                                "#b4944c",
                                "#9a845c",
                                "#847c64",
                                "#847c64",
                            ]
                            cor_linha = cores_projetos[min(numero - 1, 3)]
                        else:
                            return axis, pontos, yaxis
                    else:
                        # Projetos internos
                        inicio_col = f"Início do Projeto Interno {numero}"
                        fim_col = f"Fim do Projeto Interno {numero}"

                        # Verifica se a coluna de fim existe
                        if fim_col not in df.columns:
                            st.error(
                                f"Não foi possível determinar o fim do projeto interno {df[col_projeto].iloc[0]}",
                                icon="⚠",
                            )
                            return axis, pontos, yaxis

                        cor_linha = "#405094"  # Cor para projetos internos

                    # Verifica se as datas de início e fim são válidas
                    if pd.isna(df[inicio_col].iloc[0]) or pd.isna(df[fim_col].iloc[0]):
                        return axis, pontos, yaxis

                    # Adiciona ao gráfico
                    pontos.append(df[col_projeto].iloc[0])
                    axis += 1
                    yaxis.append(axis)

                    fig.add_trace(
                        go.Scatter(
                            x=[df[inicio_col].iloc[0], df[fim_col].iloc[0]],
                            y=[axis, axis],
                            mode="lines",
                            name=df[col_projeto].iloc[0],
                            line=dict(color=cor_linha, width=4),
                        )
                    )

                    return axis, pontos, yaxis

                def adicionar_atividades(
                    df, tipo, quantidade, axis, pontos, yaxis, fig
                ):
                    """
                    Adiciona atividades como aprendizagens e assessorias ao gráfico.

                    Args:
                        df: DataFrame contendo os dados
                        tipo: Tipo de atividade ('Aprendizagem' ou 'Assessoria')
                        quantidade: Número de atividades a adicionar
                        axis, pontos, yaxis: Parâmetros de controle do eixo Y
                        fig: Objeto figura do Plotly

                    Returns:
                        Tupla (axis, pontos, yaxis) atualizada
                    """
                    for i in range(quantidade):
                        pontos.append(f"{tipo} {i+1}")
                        axis += 1
                        yaxis.append(axis)

                        fig.add_trace(
                            go.Scatter(
                                x=[
                                    df["Inicio trimestre"].iloc[0],
                                    df["Fim trimestre"].iloc[0],
                                ],
                                y=[axis, axis],
                                mode="lines",
                                name=f"{tipo} {i+1}",
                                line=dict(color="#e4ab34", width=4),
                            )
                        )
                    return axis, pontos, yaxis

                # Bloco principal - construção do gráfico de linha do tempo
                if not df.empty:
                    # Projetos externos (1-4)
                    for i in range(1, 5):
                        axis, pontos, yaxis = adicionar_projeto_ao_grafico(
                            df, "externo", i, None, axis, pontos, yaxis, fig
                        )

                    # Projetos internos (1-2)
                    for i in range(1, 3):
                        axis, pontos, yaxis = adicionar_projeto_ao_grafico(
                            df, "interno", i, None, axis, pontos, yaxis, fig
                        )

                    # Aprendizagens
                    if "N° Aprendizagens" in colunas and pd.notna(
                        df["N° Aprendizagens"].iloc[0]
                    ):
                        try:
                            aprendizagens = int(
                                float(
                                    str(df["N° Aprendizagens"].iloc[0]).replace(
                                        ",", "."
                                    )
                                )
                            )
                            axis, pontos, yaxis = adicionar_atividades(
                                df,
                                "Aprendizagem",
                                aprendizagens,
                                axis,
                                pontos,
                                yaxis,
                                fig,
                            )
                        except ValueError:
                            st.warning(
                                f"Valor inválido para N° Aprendizagens: {df['N° Aprendizagens'].iloc[0]}"
                            )

                    # Assessorias
                    if "N° Assessorias" in colunas and pd.notna(
                        df["N° Assessorias"].iloc[0]
                    ):
                        try:
                            assessorias = int(
                                float(
                                    str(df["N° Assessorias"].iloc[0]).replace(",", ".")
                                )
                            )
                            axis, pontos, yaxis = adicionar_atividades(
                                df, "Assessoria", assessorias, axis, pontos, yaxis, fig
                            )
                        except ValueError:
                            st.warning(
                                f"Valor inválido para N° Assessorias: {df['N° Assessorias'].iloc[0]}"
                            )

                    # Configurando o layout
                    fig.update_layout(
                        title="Linha do Tempo de Alocações",
                        xaxis_title=None,
                        yaxis_title="Alocações",
                        xaxis=dict(tickformat="%m/%Y"),
                        yaxis=dict(tickvals=yaxis, ticktext=pontos),
                        showlegend=True,
                    )

                    # Exibindo o gráfico apenas se tiver dados
                    if axis != 0:
                        st.plotly_chart(fig)
                    st.write("")

                    def display_portfolio_card(df, project_number, column_obj):
                        """
                        Exibe um card com informações do portfólio de um projeto.

                        Args:
                            df: DataFrame contendo os dados
                            project_number: Número do projeto
                            column_obj: Objeto de coluna do Streamlit para exibição
                        """
                        # Verifica se o projeto existe
                        if f"Projeto {project_number}" not in df.columns or pd.isna(
                            df[f"Projeto {project_number}"].iloc[0]
                        ):
                            return

                        # Define valores padrão para colunas ausentes
                        satisfacao_col = f"Satisfação com o Projeto {project_number}"
                        portfolio_col = f"Portfólio do Projeto {project_number}"
                        satisfacao = (
                            df[satisfacao_col].iloc[0]
                            if satisfacao_col in df.columns
                            else "não mapeada"
                        )
                        portfolio = (
                            df[portfolio_col].iloc[0]
                            if portfolio_col in df.columns
                            else "não mapeado"
                        )

                        # Exibe o card
                        with column_obj:
                            st.markdown(
                                f"""
                                <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                                    <h3>Portfólio de {df[f'Projeto {project_number}'].iloc[0]}</h3>
                                    <p>{portfolio}, Satisfação com o projeto: {satisfacao}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    # Exibição dos cards de portfólio
                    if not df.empty:
                        # Conta projetos existentes
                        num_projects = sum(
                            1
                            for i in range(1, 4)
                            if f"Projeto {i}" in df.columns
                            and pd.notna(df[f"Projeto {i}"].iloc[0])
                        )

                        # Cria colunas adequadas
                        columns = st.columns(
                            max(1, num_projects + 1)
                        )  # +1 para info do cargo

                        # Exibe cards de projetos
                        for i in range(1, num_projects + 1):
                            display_portfolio_card(df, i, columns[i])

                        # Exibe informações do cargo
                        with columns[0]:
                            cargo = (
                                df["Cargo no núcleo"].iloc[0]
                                if "Cargo no núcleo" in df.columns
                                else "Cargo não mapeado"
                            )
                            area = (
                                df["Área de atuação"].iloc[0]
                                if "Área de atuação" in df.columns
                                else "Área de atuação não mapeada"
                            )

                            st.markdown(
                                f"""
                                <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                                    <h3>Cargo de {nome_formatado}</h3>
                                    <p>{cargo} - {area}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

if page == "PCP":

    def calcular_disponibilidade(analista, inicio_novo_projeto):
        """
        Calcula as horas disponíveis para um analista com base em suas atividades atuais.

        Args:
            analista: Série do pandas com dados do analista
            inicio_novo_projeto: Data de início do novo projeto

        Returns:
            float: Quantidade de horas disponíveis
        """
        horas_disponiveis = 30  # Base inicial de horas semanais

        # Subtrai horas de aprendizagens (5h cada)
        try:
            n_aprendizagens = analista.get("N° Aprendizagens", 0)
            if pd.notna(n_aprendizagens):
                val_aprendizagens = str(n_aprendizagens).replace(",", ".")
                horas_disponiveis -= float(val_aprendizagens) * 5
        except ValueError:
            pass

        # Subtrai horas de assessorias (10h cada)
        try:
            n_assessorias = analista.get("N° Assessorias", 0)
            if pd.notna(n_assessorias):
                val_assessorias = str(n_assessorias).replace(",", ".")
                horas_disponiveis -= float(val_assessorias) * 10
        except ValueError:
            pass

        # Projetos internos (5h cada)
        for i in range(1, 5):
            if pd.notnull(analista.get(f"Início do Projeto Interno {i}", None)):
                horas_disponiveis -= 5

        # Ajuste por cargo
        cargo = str(analista.get("Cargo no núcleo", "")).strip().upper()
        if cargo in ["SDR OU HUNTER", "ANALISTA SÊNIOR"]:
            horas_disponiveis -= 10

        # Ajuste por proximidade de término de projetos
        for i in range(1, 5):
            fim_estimado = analista.get(
                f"Fim estimado do Projeto {i} (com atraso)", None
            )
            fim_previsto = analista.get(
                f"Fim previsto do Projeto {i} (sem atraso)", None
            )
            fim_projeto = fim_estimado if pd.notnull(fim_estimado) else fim_previsto

            if pd.notnull(fim_projeto):
                days_left = (fim_projeto - inicio_novo_projeto).days
                if days_left > 14:
                    horas_disponiveis -= 10
                elif 7 < days_left <= 14:
                    horas_disponiveis -= 4
                elif days_left <= 7:
                    horas_disponiveis -= 1

        return horas_disponiveis

    def calcular_afinidade(analista, escopo_selecionado):
        """
        Calcula a afinidade de um analista com um escopo de projeto específico.

        Args:
            analista: Série do pandas com dados do analista
            escopo_selecionado: Nome do escopo/portfólio selecionado

        Returns:
            float: Nota de afinidade (0-10)
        """
        # Satisfação com o portfólio (peso 2x)
        satisfacao_col = f"Satisfação com o Portfólio: {escopo_selecionado}"
        if satisfacao_col in analista and pd.notna(analista[satisfacao_col]):
            val = str(analista[satisfacao_col]).replace(",", ".")
            satisfacao_portfolio = float(val)
        else:
            satisfacao_portfolio = 3  # Valor neutro caso não exista
        satisfacao_portfolio *= 2

        # Capacidade técnica (média das validações de projeto, peso 2x)
        capacidade = 0
        num_validations = 0
        for i in range(1, 5):
            try:
                val_capacidade = str(
                    analista.get(f"Validação média do Projeto {i}")
                ).replace(",", ".")
                capacidade += float(val_capacidade)
                num_validations += 1
            except ValueError:
                continue

        capacidade = capacidade / num_validations if num_validations > 0 else 3
        capacidade *= 2

        # Saúde mental (média entre percepção da carga e saúde mental)
        sentimento_carga = (
            str(analista.get("Como se sente em relação à carga", "")).strip().upper()
        )
        sentimento_map = {"SUBALOCADO": 10, "ESTOU SATISFEITO": 5, "SUPERALOCADO": 1}
        sentimento_nota = sentimento_map.get(sentimento_carga, 5)

        try:
            val_saude = str(analista.get("Saúde mental na PJ", "5")).replace(",", ".")
            saude_mental = float(val_saude)
        except ValueError:
            saude_mental = 5

        saude_final = (sentimento_nota + saude_mental) / 2

        # Nota final (média ponderada dos critérios)
        afinidade = (satisfacao_portfolio + capacidade + saude_final) / 3
        return afinidade

    # Verificação de seleção de núcleo
    if not st.session_state.nucleo:
        st.warning("Por favor, selecione um núcleo primeiro.", icon="⚠️")
        st.stop()

    # Carrega dados do núcleo selecionado
    df = nucleo_func(st.session_state.nucleo)

    if df is None:
        st.warning(
            f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️"
        )
        st.stop()

    # Tratamento inicial dos dados
    df.replace("-", np.nan, inplace=True)

    def obter_portfolio_opcoes():
        """
        Obtém as opções de portfólios disponíveis para o núcleo selecionado.

        Returns:
            list: Lista de portfólios ordenados alfabeticamente
        """
        nucleos_map = {
            "nciv": "NCiv",
            "ncon": "NCon",
            "ndados": "NDados",
            "ni": "NI",
            "ntec": "NTec",
        }

        if "pcp" not in st.session_state:
            st.session_state.pcp = load_pcp_data()

        nucleo_sheet = nucleos_map.get(st.session_state.nucleo.lower().replace(" ", ""))
        if not nucleo_sheet or nucleo_sheet not in st.session_state.pcp:
            return ["Não mapeado"]

        df = st.session_state.pcp[nucleo_sheet]

        # Busca portfólios nas colunas de satisfação
        portfolio_cols = [
            col for col in df.columns if col.startswith("Satisfação com o Portfólio: ")
        ]
        portfolios = [
            col.replace("Satisfação com o Portfólio: ", "") for col in portfolio_cols
        ]

        # Se não encontrou, busca nos portfólios de projetos
        if not portfolios:
            portfolios = []
            for i in range(1, 5):
                col_name = f"Portfólio do Projeto {i}"
                if col_name in df.columns:
                    portfolios.extend(df[col_name].dropna().unique().tolist())
            portfolios = list(set(portfolios))

        # Adiciona opção padrão se necessário
        if portfolios:
            if "Não mapeado" not in portfolios:
                portfolios.append("Não mapeado")
        else:
            portfolios = ["Não mapeado"]

        return sorted(portfolios)

    # Carrega opções de portfólios
    escopos = obter_portfolio_opcoes()

    # Inicialização do session_state
    if "escopo_selecionado" not in st.session_state:
        st.session_state.escopo_selecionado = escopos[0]
    if "analista_selecionado" not in st.session_state:
        st.session_state.analista_selecionado = "Todos"
    if "inicio_projeto" not in st.session_state:
        st.session_state.inicio_projeto = datetime.today().date()
    if "fim_projeto" not in st.session_state:
        st.session_state.fim_projeto = (datetime.today() + pd.Timedelta(days=56)).date()
    if "afinidade_weight" not in st.session_state:
        st.session_state.afinidade_weight = 0.5
    if "disponibilidade_weight" not in st.session_state:
        st.session_state.disponibilidade_weight = 0.5

    def round_to_nearest(value):
        """Arredonda para o décimo mais próximo"""
        return round(value * 10) / 10

    # Layout da interface - 3 colunas para filtros
    col_escopo, col_analista, col_data = st.columns(3)

    with col_escopo:
        escopo = st.selectbox(
            "**Portfólio**",
            options=escopos,
            index=0,
            key="escopo_select",
        )
        st.session_state.escopo_selecionado = escopo

    with col_analista:
        analistas = sorted(df["Membro"].astype(str).unique().tolist(), key=str.lower)
        analistas_selecionados = st.multiselect(
            "**Analista**",
            options=analistas,
            default=None,
            key="analista_select",
            placeholder="Selecione os analistas",
        )
        st.session_state.analista_selecionado = analistas_selecionados

    with col_data:
        inicio = st.date_input(
            "**Data de Início do Projeto**",
            min_value=datetime(datetime.today().year - 1, 1, 1).date(),
            max_value=datetime(datetime.today().year + 1, 12, 31).date(),
            value=datetime.today().date(),
            format="DD/MM/YYYY",
        )
    inicio_novo_projeto = pd.Timestamp(inicio)

    # Conversão de datas para formato correto
    df = converte_data(df, date_columns)

    # Cálculo de métricas para todos os analistas
    df["Disponibilidade"] = df.apply(
        lambda row: calcular_disponibilidade(row, inicio_novo_projeto), axis=1
    )

    # Normalização da disponibilidade para escala 0-10
    max_disponibilidade = 30
    min_disponibilidade = df["Disponibilidade"].min()
    range_disponibilidade = max_disponibilidade - min_disponibilidade

    if range_disponibilidade != 0:
        scaling_factor = 10 / range_disponibilidade
        df["Nota Disponibilidade"] = (
            df["Disponibilidade"] - min_disponibilidade
        ) * scaling_factor
    else:
        df["Nota Disponibilidade"] = 10

    # Cálculo da afinidade com o escopo selecionado
    df["Afinidade"] = df.apply(lambda row: calcular_afinidade(row, escopo), axis=1)

    # Segunda linha de configurações
    col_disp, col_afin, col_fim = st.columns(3)

    with col_disp:
        disponibilidade_weight = st.number_input(
            "**Peso da Disponibilidade (0.3 - 0.7)**",
            min_value=0.3,
            max_value=0.7,
            value=st.session_state.disponibilidade_weight,
            step=0.1,
            key="disponibilidade_weight_input",
        )
        disponibilidade_weight = round_to_nearest(disponibilidade_weight)
        if disponibilidade_weight != st.session_state.disponibilidade_weight:
            st.session_state.disponibilidade_weight = disponibilidade_weight
            st.session_state.afinidade_weight = round(
                1 - st.session_state.disponibilidade_weight, 1
            )
            st.rerun()

    with col_afin:
        afinidade_weight = st.number_input(
            "**Peso da Afinidade (0.3 - 0.7)**",
            min_value=0.3,
            max_value=0.7,
            value=st.session_state.afinidade_weight,
            step=0.1,
            key="afinidade_weight_input",
        )
    afinidade_weight = round_to_nearest(afinidade_weight)
    if afinidade_weight != st.session_state.afinidade_weight:
        st.session_state.afinidade_weight = afinidade_weight
        st.session_state.disponibilidade_weight = round(
            1 - st.session_state.afinidade_weight, 1
        )
        st.rerun()

    with col_fim:
        default_fim_date = (pd.Timestamp(inicio) + pd.DateOffset(months=2)).date()
        fim = st.date_input(
            "**Data de Fim do Projeto**",
            min_value=inicio,
            max_value=datetime(datetime.today().year + 1, 12, 31).date(),
            value=default_fim_date,
            format="DD/MM/YYYY",
        )

    # Validação de pesos
    if afinidade_weight + disponibilidade_weight != 1.0:
        st.warning("A soma dos pesos deve ser igual a 1. Ajustando os valores.")
        afinidade_weight = round(afinidade_weight, 1)
        disponibilidade_weight = round(1 - afinidade_weight, 1)
        st.session_state.afinidade_weight = afinidade_weight
        st.session_state.disponibilidade_weight = disponibilidade_weight
        st.write(f"Peso da Afinidade ajustado para: {afinidade_weight}")
        st.write(f"Peso da Disponibilidade ajustado para: {disponibilidade_weight}")

    # Cálculo da nota final
    df["Nota Final"] = (
        df["Afinidade"] * afinidade_weight
        + df["Nota Disponibilidade"] * disponibilidade_weight
    )

    # Filtragem e cálculo de médias
    df = df.dropna(subset=["Membro"])
    dispo_media = df["Disponibilidade"].mean()
    afini_media = df["Afinidade"].mean()
    nota_media = df["Nota Final"].mean()

    # Aplica filtro de analistas se necessário
    if analistas_selecionados:
        df = df[df["Membro"].isin(analistas_selecionados)]

    st.markdown("---")
    st.subheader("Membros sugeridos para o projeto")

    # Explica as métricas usadas
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
        unsafe_allow_html=True,
    )

    def format_display_df(df):
        """
        Formata o DataFrame para exibição, incluindo linha com médias.

        Args:
            df: DataFrame com os dados dos analistas

        Returns:
            DataFrame formatado para exibição
        """
        formatted_df = df[
            ["Membro", "Disponibilidade", "Afinidade", "Nota Final"]
        ].copy()

        # Converte colunas para tipos consistentes
        formatted_df["Disponibilidade"] = formatted_df["Disponibilidade"].astype(float)
        formatted_df["Afinidade"] = formatted_df["Afinidade"].astype(float)
        formatted_df["Nota Final"] = formatted_df["Nota Final"].astype(float)
        formatted_df["Membro"] = formatted_df["Membro"].astype(str)

        # Adiciona linha com médias
        formatted_df.loc[len(formatted_df)] = [
            "media.núcleo ⚠",
            dispo_media,
            afini_media,
            nota_media,
        ]

        # Ordena por nota final
        formatted_df = formatted_df.sort_values(by="Nota Final", ascending=False)

        # Formata nomes dos membros
        formatted_df["Membro"] = formatted_df["Membro"].apply(
            lambda x: " ".join([part.capitalize() for part in x.split(".")])
        )

        return formatted_df

    # Formata e exibe os resultados
    display_df = format_display_df(df)

    # Exibe cards para cada analista
    for index, row in display_df.iterrows():
        # Define cores conforme o tipo de linha (analista ou média)
        if row["Membro"] != "Media Núcleo ⚠":
            prim_color = "064381"
            sec_color = "fbac04"  # Não utilizado, pode ser removido
            back_color = "decda9"
        else:
            # Cores específicas para núcleos
            match st.session_state.nucleo:
                case "NCiv":
                    prim_color = "805e01"
                    back_color = "e0d19b"
                case "NCon":
                    prim_color = "054f20"
                    back_color = "91cfa7"
                case "NDados":
                    prim_color = "461073"
                    back_color = "c19be0"
                case "NI":
                    prim_color = "3d0202"
                    back_color = "c27a7a"
                case "NTec":
                    prim_color = "04064a"
                    back_color = "9a9cd9"

        # Renderiza o card do analista com barras de progresso
        st.markdown(
            f"""
            <div style="border: 3px solid #a1a1a1; padding: 10px; border-radius: 10px; width: 700px; color:#{prim_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-wrap: nowrap;">
                    <div style="flex: 1; min-width: 0; padding-right: 10px;">
                        <h3>{row['Membro']}</h3>
                        <p style="margin-bottom: 0px;">Disponibilidade</p>
                        <div style="width: 80%; background-color: #{back_color}; border-radius: 5px; height: 20px; overflow: hidden; margin-bottom: 5px; position: relative;">
                            <div style="width: {min(100, (row['Disponibilidade'] / 30.0) * 100)}%; background-color: 
                                {'#2fa83b' if (row['Disponibilidade'] / 30.0) * 100 > 70 else '#fbac04' if (row['Disponibilidade'] / 30.0) * 100 >= 40 else '#c93220'}; 
                                height: 100%;"></div>
                            <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {min(100, (dispo_media / 30.0) * 100)}%;"></div>
                        </div>
                        <p style="margin-bottom: 10px;">{row['Disponibilidade']:.2f}h / {30.0}h</p>
                        <p style="margin-bottom: 0px;">Afinidade</p>
                        <div style="width: 80%; background-color: #{back_color}; border-radius: 5px; height: 20px; overflow: hidden; margin-bottom: 5px; position: relative;">
                            <div style="width: {min(100, (row['Afinidade'] / 10.0) * 100)}%; background-color: 
                                {'#2fa83b' if (row['Afinidade'] / 10.0) * 100 > 70 else '#fbac04' if (row['Afinidade'] / 10.0) * 100 >= 40 else '#c93220'}; 
                                height: 100%;"></div>
                            <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {min(100, (afini_media / 10.0) * 100)}%;"></div>
                        </div>
                        <p style="margin-bottom: 0px;">{row['Afinidade']:.2f} / {10.0}</p>
                    </div>
                    <div style="text-align: right; flex-shrink: 0; padding-left: 10px;">
                        <h3>{row['Nota Final']:.2f}</h3>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
