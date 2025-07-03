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


# Função aprimorada para carregar dados
@st.cache_data(ttl=86400)  # Cache expira em 1 dia
def load_pcp_data():
    try:
        # Try to load from Google Sheets first
        return load_from_gsheets()
    except Exception as e:
        st.warning(
            f"Failed to load from Google Sheets: {e}. Falling back to local Excel file."
        )
        st.exit()


def load_from_gsheets():
    try:
        # Set up authentication scope for Google Sheets API
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # Get credentials from secrets.toml file
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

        # Connect to Google Sheets API
        client = gspread.authorize(credentials)

        # Open the spreadsheet by name
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

        # Specify which sheets to load
        sheet_names = ["NDados", "NTec", "NCiv", "NI", "NCon"]

        # Define column types to optimize memory
        dtype_dict = {
            "Membro": "category",
            "Cargo no núcleo": "category",
            "Área de atuação": "category",
            "Como se sente em relação à carga": "category",
        }

        # Dictionary to store all DataFrames
        all_sheets = {}

        # Process each sheet
        for sheet_name in sheet_names:
            try:
                # Get worksheet
                worksheet = spreadsheet.worksheet(sheet_name)

                # Get all values (more efficient than cell-by-cell access)
                data = worksheet.get_all_values()

                if not data:
                    logging.warning(f"Nenhum dado encontrado na planilha: {sheet_name}")
                    all_sheets[sheet_name] = pd.DataFrame()
                    continue

                # Extract headers and values
                headers = data[0]
                values = data[1:]

                # Filter out "Email PJ" column for privacy/security if it exist                

                if "Email PJ" in headers:
                    email_index = headers.index("Email PJ")
                    headers = [h for i, h in enumerate(headers) if i != email_index]
                    values = [
                        [v for i, v in enumerate(row) if i != email_index]
                        for row in values
                    ]

                # Create DataFrame
                pcp_df = pd.DataFrame(values, columns=headers)

                # --- INÍCIO DA ALTERAÇÃO ---
                # Garante que a coluna 'Membro' exista antes de tentar limpá-la
                if 'Membro' in pcp_df.columns:
                    # Substitui textos vazios por um valor nulo que o pandas entende (NaN)
                    pcp_df['Membro'].replace(['', 'None', '-'], np.nan, inplace=True)
                    
                    # Apaga as linhas onde a coluna 'Membro' é nula
                    pcp_df.dropna(subset=['Membro'], inplace=True)
                # --- FIM DA ALTERAÇÃO ---

                # Process date columns
                for date_col in date_columns:
                    if date_col in pcp_df.columns:
                        try:
                            # Convert to datetime and format consistently
                            pcp_df[date_col] = pd.to_datetime(
                                pcp_df[date_col], format="%d/%m/%Y", errors="coerce"
                            ).dt.strftime("%d/%m/%Y")
                        except Exception as e:
                            logging.warning(
                                f"Erro ao converter coluna de data '{date_col}' na aba {sheet_name}: {e}"
                            )

                # Convert categorical columns to optimize memory
                for col, dtype in dtype_dict.items():
                    if col in pcp_df.columns:
                        pcp_df[col] = pcp_df[col].astype(dtype)

                # Remove excluded roles
                if "Cargo no núcleo" in pcp_df.columns:
                    pcp_df = pcp_df[~pcp_df["Cargo no núcleo"].isin(cargos_excluidos)]

                # Store processed DataFrame
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

        if not all_sheets:
            st.warning("Nenhuma planilha foi carregada com sucesso.")

        return all_sheets

    except Exception as e:
        logging.error(f"Erro ao conectar com Google Sheets: {str(e)}", exc_info=True)
        st.error(f"Erro ao conectar com Google Sheets: {str(e)}", icon="🚨")
        st.stop()


def nucleo_func(nucleo_digitado):
    # Normaliza a entrada
    nucleo_digitado = nucleo_digitado.replace(" ", "").lower()

    # Mapeamento de nomes normalizados para nomes de abas
    nucleos_map = {
        "nciv": "NCiv",
        "ncon": "NCon",
        "ndados": "NDados",
        "ni": "NI",
        "ntec": "NTec",
    }

    # Check if PCP data is loaded in session_state
    if "pcp" not in st.session_state:
        st.session_state.pcp = load_pcp_data()

    # Obtém o nome da aba usando o mapeamento
    sheet_name = nucleos_map.get(nucleo_digitado)

    if not sheet_name or sheet_name not in st.session_state.pcp:
        return None

    # Retorna uma cópia do DataFrame já pré-processado
    df = st.session_state.pcp[sheet_name].copy()

    # Drop columns with all NaN/None values for this specific sheet
    # Convert 'None' strings to None
    df = df.replace("None", None)
    df = df.replace("-", None)

    # Drop columns that are completely empty (all NaN/None)
    df = df.dropna(axis=1, how="all")
    df = df.dropna(subset=[df.columns[0]])

    # Identify and drop columns that contain only empty strings or 'None'/'none' strings
    cols_to_drop = []
    for col in df.columns:
        # Check if all non-NaN values in column are empty strings, 'None', or 'none'
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


# Inicializando session_state para manter os valores dos filtros
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


# Função para converter colunas de data
def converte_data(df, date_columns):
    df_copy = df.copy()
    for col in date_columns:
        if col in df_copy.columns:
            try:
                # Converte para string primeiro antes de converter para datetime
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
            df = batch_convert_dates(df, date_columns_to_convert)

            # Filtros
            colcargo, colnome, colaloc = st.columns(3)

            # For the Name input
            def update_nome():
                st.session_state.nome = st.session_state.nome_input

            with colnome:
                nome = st.text_input(
                    "Nome do Membro",
                    placeholder="Membro",
                    value=st.session_state.nome if st.session_state.nome else None,
                    key="nome_input",
                    on_change=update_nome,
                )

            opcoes = [
                "Desalocado",
                "1 Alocação",
                "2 Alocações",
                "3 Alocações",
                "4+ Alocações",
            ]

            # For the Cargo input
            def update_cargo():
                st.session_state.cargo = st.session_state.cargo_input

            with colcargo:
                cargo = st.text_input(
                    "Cargo",
                    placeholder="Cargo",
                    value=st.session_state.cargo if st.session_state.cargo else None,
                    key="cargo_input",
                    on_change=update_cargo,
                )

            # For the Alocações multiselect
            def update_aloc():
                # If nothing selected, set to None rather than empty list
                if st.session_state.aloc_input:
                    st.session_state.aloc = (
                        st.session_state.aloc_input[0]
                        if len(st.session_state.aloc_input) == 1
                        else None
                    )
                else:
                    st.session_state.aloc = None

            with colaloc:
                # Prepare default values only from session state
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

                # O multiselect pode retornar uma lista de opções selecionadas
                if st.session_state.aloc and st.session_state.aloc in opcoes:
                    default_values = [st.session_state.aloc]
                else:
                    default_values = []  # Lista vazia se não houver valor padrão

                # Update the session state
                if aloc:
                    st.session_state.aloc = aloc[0] if len(aloc) == 1 else None

                # Filtragem dos dados
                if nome:
                    df = df[
                        df["Membro"].str.strip().str.lower() == nome.strip().lower()
                    ]
                    df = df.dropna()
                if cargo:
                    df = df[df["Cargo no núcleo"] == cargo]

            if aloc:
                # Mapping de opção de texto para o valor numérico correspondente
                opcoes_valor_map = {
                    "Desalocado": 0,
                    "1 Alocação": 1,
                    "2 Alocações": 2,
                    "3 Alocações": 3,
                    "4+ Alocações": 4,
                }

                # Data atual para comparar com datas de fim
                data_atual = datetime.today()

                # Função para verificar se projeto está ativo
                def projeto_ativo(row, col_projeto, col_fim_estimado, col_fim_previsto):
                    if pd.isna(row[col_projeto]):
                        return False

                    fim_estimado = row.get(col_fim_estimado)
                    fim_previsto = row.get(col_fim_previsto)

                    fim_projeto = (
                        fim_estimado if pd.notna(fim_estimado) else fim_previsto
                    )

                    # Projeto ativo se tem data de fim e essa data é posterior à data atual
                    return pd.notna(fim_projeto) and fim_projeto > data_atual

                # Conta projetos ativos para cada linha
                projeto_cols = []
                for i in range(1, 4):  # Projetos 1 a 3
                    col_projeto = f"Projeto {i}"
                    col_fim_estimado = f"Fim estimado do Projeto {i} (com atraso)"
                    col_fim_previsto = f"Fim previsto do Projeto {i} (sem atraso)"

                    # Adiciona à lista apenas se a coluna existir
                    if col_projeto in df.columns:
                        projeto_cols.append(
                            (col_projeto, col_fim_estimado, col_fim_previsto)
                        )

                # Inicia contador de alocações
                alocacoes = pd.Series(0, index=df.index)

                # Conta projetos ativos
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

                # Adiciona projetos internos ativos
                for i in range(1, 3):  # Projetos internos 1 a 2
                    col_projeto = f"Projeto Interno {i}"
                    col_fim = f"Fim do Projeto Interno {i}"
                    col_inicio = f"Início do Projeto Interno {i}"

                    if col_projeto in df.columns:
                        # Primeiro verifica se o fim está definido
                        if col_fim in df.columns:
                            alocacoes += df.apply(
                                lambda row: (
                                    1
                                    if pd.notna(row[col_projeto])
                                    and pd.notna(row[col_fim])
                                    and row[col_fim] > data_atual
                                    else 0
                                ),
                                axis=1,
                            )
                        # Se não, verifica se o início está definido
                        elif col_inicio in df.columns:
                            alocacoes += df.apply(
                                lambda row: (
                                    1
                                    if pd.notna(row[col_projeto])
                                    and pd.notna(row[col_inicio])
                                    else 0
                                ),
                                axis=1,
                            )

                # Adiciona cargos que contam como alocação
                if "Cargo WI" in df.columns:
                    alocacoes += df["Cargo WI"].notna().astype(int)

                if "Cargo MKT" in df.columns:
                    alocacoes += df["Cargo MKT"].notna().astype(int)

                # Adiciona aprendizagens e assessorias (contabiliza como alocações)
                if "N° Aprendizagens" in df.columns:
                    alocacoes += df["N° Aprendizagens"].fillna(0)

                if "N° Assessorias" in df.columns:
                    alocacoes += df["N° Assessorias"].fillna(0)

                # Limita o número de alocações para no máximo 4
                alocacoes = alocacoes.clip(upper=4)

                # Filtra o DataFrame usando os valores mapeados
                valores_filtro = [opcoes_valor_map[opt] for opt in aloc]
                df = df[alocacoes.isin(valores_filtro)]
            if df.empty:
                st.write("Sem informações para os dados filtrados")
            else:
                try:
                    # Reset index and drop it from the display
                    df_display = df.copy().reset_index(drop=True)

                    # Additional cleanup for empty columns
                    df_display = df_display.replace("None", None)
                    df_display = df_display.replace("-", None)

                    # Display dataframe without index
                    st.dataframe(df_display, hide_index=True)
                except Exception as e:
                    st.error(f"Erro ao exibir dados: {e}")
            st.write("---")

            def get_quarter_dates():
                current_year = datetime.today().year
                current_month = datetime.today().month
                quarter_start_month = ((current_month - 1) // 3) * 3 + 1
                quarter_end_month = quarter_start_month + 2
                return (
                    datetime(current_year, quarter_start_month, 1),
                    datetime(current_year, quarter_end_month, 1)
                    + pd.Timedelta(days=31)
                    - pd.Timedelta(
                        days=datetime(current_year, quarter_end_month, 1).day
                    ),
                )

            if nome:
                df["Inicio trimestre"], df["Fim trimestre"] = get_quarter_dates()

                df = df.dropna(axis=1, how="all")
                nome_formatado = " ".join(
                    [part.capitalize() for part in nome.split(".")] if nome else []
                )

                st.subheader(nome_formatado)
                colunas = df.columns
                pontos = []
                yaxis = []
                axis = 0

                fig = go.Figure()

                # Função auxiliar para verificar valores de projeto e adicionar traço no gráfico
                def adicionar_projeto_ao_grafico(
                    df, tipo, numero, cor, axis, pontos, yaxis, fig
                ):
                    col_projeto = (
                        f"Projeto {numero}"
                        if tipo == "externo"
                        else f"Projeto Interno {numero}"
                    )

                    # Verifica se o projeto existe no dataframe E não é NaN
                    if col_projeto in df.columns and pd.notna(df[col_projeto].iloc[0]):
                        # Define coluna de início e fim baseado no tipo
                        if tipo == "externo":
                            # Tenta determinar a data de fim
                            funcionando = True
                            try:
                                fim_col = (
                                    f"Fim estimado do Projeto {numero} (com atraso)"
                                )
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
                                cor_linha = [
                                    "#b4944c",
                                    "#9a845c",
                                    "#847c64",
                                    "#847c64",
                                ][
                                    min(numero - 1, 3)
                                ]  # Cores para projetos 1-4
                            else:
                                return (
                                    axis,
                                    pontos,
                                    yaxis,
                                )  # Não adiciona se não tem data fim
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
                        if pd.notna(df[inicio_col].iloc[0]) and pd.notna(
                            df[fim_col].iloc[0]
                        ):
                            # Adiciona ao gráfico
                            pontos.append(df[col_projeto])
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

                # Função para adicionar atividades como aprendizagens e assessorias
                def adicionar_atividades(
                    df, tipo, quantidade, axis, pontos, yaxis, fig
                ):
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

                # Dentro do bloco principal
                if not df.empty:
                    # Projetos externos (1-4)
                    for i in range(1, 5):
                        axis, pontos, yaxis = adicionar_projeto_ao_grafico(
                            df, "externo", i, "", axis, pontos, yaxis, fig
                        )

                    # Projetos internos (1-2)
                    for i in range(1, 3):
                        axis, pontos, yaxis = adicionar_projeto_ao_grafico(
                            df, "interno", i, "", axis, pontos, yaxis, fig
                        )

                    # Aprendizagens
                    if "N° Aprendizagens" in colunas and pd.notna(
                        df["N° Aprendizagens"].iloc[0]
                    ):
                        aprendizagens = int(df["N° Aprendizagens"].iloc[0])
                        axis, pontos, yaxis = adicionar_atividades(
                            df, "Aprendizagem", aprendizagens, axis, pontos, yaxis, fig
                        )

                    # Assessorias
                    if "N° Assessorias" in colunas and pd.notna(
                        df["N° Assessorias"].iloc[0]
                    ):
                        assessorias = int(df["N° Assessorias"].iloc[0])
                        axis, pontos, yaxis = adicionar_atividades(
                            df, "Assessoria", assessorias, axis, pontos, yaxis, fig
                        )

                    # Configurando o layout
                    fig.update_layout(
                        title="df das Alocações",
                        xaxis_title=None,
                        yaxis_title="Alocações",
                        xaxis=dict(tickformat="%m/%Y"),
                        yaxis=dict(tickvals=yaxis, ticktext=pontos),
                        showlegend=True,
                    )
                    if axis != 0:
                        # Exibindo o gráfico no Streamlit
                        st.plotly_chart(fig)
                    st.write("")

                    def display_portfolio_card(df, project_number, column_obj):
                        # Check if project exists
                        if f"Projeto {project_number}" not in df.columns or pd.isna(
                            df[f"Projeto {project_number}"].iloc[0]
                        ):
                            return

                        # Set default values for missing columns
                        if (
                            f"Satisfação com o Projeto {project_number}"
                            not in df.columns
                        ):
                            df[f"Satisfação com o Projeto {project_number}"] = (
                                "não mapeada"
                            )

                        if f"Portfólio do Projeto {project_number}" not in df.columns:
                            df[f"Portfólio do Projeto {project_number}"] = "não mapeado"

                        # Display the card
                        with column_obj:
                            st.markdown(
                                f"""
                                <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                                    <h3>Portfólio de {df[f'Projeto {project_number}'].iloc[0]}</h3>
                                    <p>{df[f'Portfólio do Projeto {project_number}'].iloc[0]}, 
                                    Satisfação com o projeto: {df[f'Satisfação com o Projeto {project_number}'].iloc[0]}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    # Usage in main code
                    if not df.empty:
                        columns = []

                        # Determine number of columns needed
                        num_projects = 0
                        for i in range(1, 4):  # Check for projects 1-3
                            if f"Projeto {i}" in df.columns and pd.notna(
                                df[f"Projeto {i}"].iloc[0]
                            ):
                                num_projects += 1

                        # Create appropriate number of columns
                        columns = st.columns(num_projects + 1)  # +1 for role info

                        # Display project cards
                        for i in range(1, num_projects + 1):
                            display_portfolio_card(df, i, columns[i])

                        # Display role info
                        with columns[0]:
                            # Role info card display
                            if "Cargo no núcleo" not in df.columns:
                                df["Cargo no núcleo"] = "Cargo não mapeado"
                            if "Área de atuação" not in df.columns:
                                df["Área de atuação"] = "Área de atuação não mapeada"

                            st.markdown(
                                f"""
                                <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                                    <h3>Cargo de {nome_formatado}</h3>
                                    <p>{df["Cargo no núcleo"].iloc[0]} - {df['Área de atuação'].iloc[0]}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

if page == "PCP":
    # Funções de Backend
    def calcular_disponibilidade(analista, inicio_novo_projeto):
        horas_disponiveis = 30  # Começamos com 30h disponíveis

        # Subtrai horas conforme aprendizados e assessorias (com tratamento de strings)
        try:
            n_aprendizagens = analista.get("N° Aprendizagens", 0)
            if pd.notna(n_aprendizagens):
                val_aprendizagens = str(n_aprendizagens).replace(",", ".")
                horas_disponiveis -= float(val_aprendizagens) * 5
        except ValueError:
            pass

        try:
            n_assessorias = analista.get("N° Assessorias", 0)
            if pd.notna(n_assessorias):
                val_assessorias = str(n_assessorias).replace(",", ".")
                horas_disponiveis -= float(val_assessorias) * 10
        except ValueError:
            pass

        # Subtrai horas conforme projetos internos ativos (cada um reduz 5h)
        for i in range(1, 5):  # Projetos Internos 1 a 4
            if pd.notnull(analista.get(f"Início do Projeto Interno {i}", None)):
                horas_disponiveis -= 5

        # Ajusta conforme cargo no núcleo
        cargo = str(analista.get("Cargo no núcleo", "")).strip().upper()
        if cargo in ["SDR OU HUNTER", "ANALISTA SÊNIOR"]:
            horas_disponiveis -= 10

        # Ajusta conforme proximidade da data de fim de um projeto
        for i in range(1, 5):  # Projetos 1 a 4
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
                if 7 < days_left <= 14:
                    horas_disponiveis -= 4
                elif days_left <= 7:
                    horas_disponiveis -= 1

        return horas_disponiveis

    def calcular_afinidade(analista, escopo_selecionado):
        # Verifica se existe coluna específica de satisfação para o portfólio selecionado
        satisfacao_col = f"Satisfação com o Portfólio: {escopo_selecionado}"

        # Tenta obter o valor da coluna específica do portfólio
        if satisfacao_col in analista and pd.notna(analista[satisfacao_col]):
            val = str(analista[satisfacao_col]).replace(",", ".")
            satisfacao_portfolio = float(val)
        else:
            # Se não encontrar satisfação específica, usa valor neutro
            satisfacao_portfolio = 3

        satisfacao_portfolio *= 2

        # Capacidade esperada = Validação média do Projeto * 2
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

        if num_validations > 0:
            capacidade = capacidade / num_validations
        else:
            capacidade = 3

        capacidade *= 2

        # Saúde mental = Média entre percepção da carga e saúde mental na PJ
        # NEUTRO É 5
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

        # Nota final de afinidade é a média dos três critérios
        afinidade = (satisfacao_portfolio + capacidade + saude_final) / 3
        return afinidade

    # Verifica se um núcleo foi selecionado
    if not st.session_state.nucleo:
        st.warning("Por favor, selecione um núcleo primeiro.", icon="⚠️")
        st.stop()

    # Obtém o dataframe para o núcleo selecionado
    df = nucleo_func(st.session_state.nucleo)

    if df is None:
        st.warning(
            f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️"
        )
        st.stop()

    # Substitui '-' por NaN
    df.replace("-", np.nan, inplace=True)

    # Define os portfólios dinamicamente com base nas colunas da planilha
    def obter_portfolio_opcoes():
        # Mapeamento de abreviações para nomes completos de núcleos
        nucleos_map = {
            "nciv": "NCiv",
            "ncon": "NCon",
            "ndados": "NDados",
            "ni": "NI",
            "ntec": "NTec",
        }

        # Verifica se os dados estão carregados
        if "pcp" not in st.session_state:
            st.session_state.pcp = load_pcp_data()

        # Obtém o nome da planilha do núcleo selecionado
        nucleo_sheet = nucleos_map.get(st.session_state.nucleo.lower().replace(" ", ""))

        if not nucleo_sheet or nucleo_sheet not in st.session_state.pcp:
            return ["Não mapeado"]

        # Pega o DataFrame do núcleo atual
        df = st.session_state.pcp[nucleo_sheet]

        # Procura por colunas que começam com "Satisfação com o Portfólio: "
        portfolio_cols = [
            col for col in df.columns if col.startswith("Satisfação com o Portfólio: ")
        ]

        # Extrai os nomes dos portfólios das colunas
        portfolios = [
            col.replace("Satisfação com o Portfólio: ", "") for col in portfolio_cols
        ]

        # Se não encontrou portfólios específicos, tenta buscar de outra forma
        if not portfolios:
            # Tenta buscar dos portfólios de projetos existentes
            portfolios = []
            for i in range(1, 5):  # Projetos 1 a 4
                col_name = f"Portfólio do Projeto {i}"
                if col_name in df.columns:
                    portfolios.extend(df[col_name].dropna().unique().tolist())

            portfolios = list(set(portfolios))  # Remove duplicados

        # Adiciona "Não mapeado" se não for vazio
        if portfolios:
            if "Não mapeado" not in portfolios:
                portfolios.append("Não mapeado")
        else:
            portfolios = ["Não mapeado"]

        return sorted(portfolios)

    # Utiliza a função para obter os portfólios dinamicamente
    escopos = obter_portfolio_opcoes()

    # Inicializa session_state para os campos de filtro
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

    # Callbacks para atualizar os estados quando os valores mudam
    def on_escopo_change(escopo):
        st.session_state.escopo_selecionado = escopo

    def on_analista_change(analista):
        st.session_state.analista_selecionado = analista

    def on_inicio_change(data):
        st.session_state.inicio_projeto = data
        # Atualiza fim se necessário
        if st.session_state.fim_projeto < data:
            st.session_state.fim_projeto = data + pd.Timedelta(days=56)

    def on_fim_change(data):
        st.session_state.fim_projeto = data

    def on_afinidade_weight_change(valor):
        st.session_state.afinidade_weight = valor
        st.session_state.disponibilidade_weight = round(1 - valor, 1)

    def on_disponibilidade_weight_change(valor):
        st.session_state.disponibilidade_weight = valor
        st.session_state.afinidade_weight = round(1 - valor, 1)

    # Cria um layout de 3 colunas para os filtros
    col_escopo, col_analista, col_data = st.columns(3)

    with col_escopo:
        escopo = st.selectbox(
            "**Portfólio**",
            options=escopos,
            index=0,
            args=(st.session_state.escopo_selecionado,),
            key="escopo_select",
        )
        st.session_state.escopo_selecionado = escopo

    with col_analista:
        analistas = sorted(df["Membro"].astype(str).unique().tolist(), key=str.lower)

        # Usando o multiselect
        analistas_selecionados = st.multiselect(
            "**Analista**",
            options=analistas,
            default=None,
            key="analista_select",
            placeholder="Selecione os analistas",
        )

        # Salva a seleção no session_state para persistência
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

    df = converte_data(df, date_columns)

    # Filtra por analista se um for selecionado
    # Calcula todas as métricas de uma vez
    df["Disponibilidade"] = df.apply(
        lambda row: calcular_disponibilidade(row, inicio_novo_projeto), axis=1
    )

    # Calcula Nota Disponibilidade
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

    # Calcula Afinidade com base no escopo selecionado
    df["Afinidade"] = df.apply(lambda row: calcular_afinidade(row, escopo), axis=1)

    def round_to_nearest(value):
        return round(value * 10) / 10

    # Segunda linha para a data de fim
    col_disp, col_afin, col_fim = st.columns(3)
    with col_disp:
        # A entrada de disponibilidade
        disponibilidade_weight = st.number_input(
            "**Peso da Disponibilidade (0.3 - 0.7)**",
            min_value=0.3,
            max_value=0.7,
            value=st.session_state.disponibilidade_weight,
            step=0.1,
            key="disponibilidade_weight_input",
        )
        disponibilidade_weight = round_to_nearest(disponibilidade_weight)
        # Se o valor de disponibilidade mudar, ajustar afinidade
        if disponibilidade_weight != st.session_state.disponibilidade_weight:
            st.session_state.disponibilidade_weight = disponibilidade_weight
            st.session_state.afinidade_weight = round(
                1 - st.session_state.disponibilidade_weight, 1
            )
            st.rerun()

    # Caixa de entrada para afinidade
    with col_afin:
        # A entrada de afinidade
        afinidade_weight = st.number_input(
            "**Peso da Afinidade (0.3 - 0.7)**",
            min_value=0.3,
            max_value=0.7,
            value=st.session_state.afinidade_weight,
            step=0.1,
            key="afinidade_weight_input",
        )
    afinidade_weight = round_to_nearest(afinidade_weight)
    # Se o valor de afinidade mudar, ajustar disponibilidade
    if afinidade_weight != st.session_state.afinidade_weight:
        st.session_state.afinidade_weight = afinidade_weight
        st.session_state.disponibilidade_weight = round(
            1 - st.session_state.afinidade_weight, 1
        )
        st.rerun()

    with col_fim:
        # Calcula a data de fim como início + 2 meses
        default_fim_date = (pd.Timestamp(inicio) + pd.DateOffset(months=2)).date()

        fim = st.date_input(
            "**Data de Fim do Projeto**",
            min_value=inicio,
            max_value=datetime(datetime.today().year + 1, 12, 31).date(),
            value=default_fim_date,  # Usa a data padrão calculada
            format="DD/MM/YYYY",
        )

    # Garante que os pesos somem 1
    if afinidade_weight + disponibilidade_weight != 1.0:
        st.warning("A soma dos pesos deve ser igual a 1. Ajustando os valores.")

        # Ajusta os pesos para que somem 1
        afinidade_weight = round(afinidade_weight, 1)
        disponibilidade_weight = round(1 - afinidade_weight, 1)

        # Atualiza session_state
        st.session_state.afinidade_weight = afinidade_weight
        st.session_state.disponibilidade_weight = disponibilidade_weight

        st.write(f"Peso da Afinidade ajustado para: {afinidade_weight}")
        st.write(f"Peso da Disponibilidade ajustado para: {disponibilidade_weight}")

    # Calcula Nota Final com os pesos atualizados
    df["Nota Final"] = (
        df["Afinidade"] * afinidade_weight
        + df["Nota Disponibilidade"] * disponibilidade_weight
    )

    df = df.dropna(subset=["Membro"])
    dispo_media = df["Disponibilidade"].mean()
    afini_media = df["Afinidade"].mean()
    nota_media = df["Nota Final"].mean()
    if analistas_selecionados != []:
        df = df[df["Membro"].isin(analistas_selecionados)]
    # Cria um divisor
    st.markdown("---")

    # Exibe as colunas principais
    st.subheader("Membros sugeridos para o projeto")

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

    # Função para formatar o DataFrame para exibição
    def format_display_df(df):
        formatted_df = df[
            ["Membro", "Disponibilidade", "Afinidade", "Nota Final"]
        ].copy()
        # Ensure all numeric columns are float64 to avoid dtype incompatibility
        formatted_df["Disponibilidade"] = formatted_df["Disponibilidade"].astype(float)
        formatted_df["Afinidade"] = formatted_df["Afinidade"].astype(float)
        formatted_df["Nota Final"] = formatted_df["Nota Final"].astype(float)
        formatted_df["Membro"] = formatted_df["Membro"].astype(str)
        formatted_df.loc[len(formatted_df)] = [
            "media.núcleo ⚠",
            dispo_media,
            afini_media,
            nota_media,
        ]
        formatted_df = formatted_df.sort_values(by="Nota Final", ascending=False)
        # Capitalize member names
        formatted_df["Membro"] = formatted_df["Membro"].apply(
            lambda x: " ".join([part.capitalize() for part in x.split(".")])
        )
        return formatted_df

    # Formata as colunas para melhor exibição
    display_df = format_display_df(df)
    # Exibe a tabela
    for index, row in display_df.iterrows():
        if row["Membro"] != "Media Núcleo ⚠":
            prim_color = "064381"
            sec_color = "fbac04"
            back_color = "decda9"
        else:
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

        st.markdown(
            f"""
            <div style="border: 3px solid #a1a1a1; padding: 10px; border-radius: 10px; width: 700px; color:#{prim_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-wrap: nowrap;">
                    <!-- Garantir que o espaço para o 'Membro' e 'Nota Final' não afete a largura da barra -->
                    <div style="flex: 1; min-width: 0; padding-right: 10px;">  <!-- Espaço para 'Membro' -->
                        <h3>{row['Membro']}</h3>
                        <p style="margin-bottom: 0px;">Disponibilidade</p>
                        <div style="width: 80%; background-color: #{back_color}; border-radius: 5px; height: 20px; overflow: hidden; margin-bottom: 5px; position: relative;">
                            <!-- Largura da barra de progresso -->
                            <div style="width: {min(100, (row['Disponibilidade'] / 30.0) * 100)}%; background-color: 
                                {'#2fa83b' if (row['Disponibilidade'] / 30.0) * 100 > 70 else '#fbac04' if (row['Disponibilidade'] / 30.0) * 100 >= 40 else '#c93220'}; 
                                height: 100%;"></div>
                            <!-- Barrinha de demarcação visual -->
                            <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {min(100, (dispo_media / 30.0) * 100)}%;"></div>
                        </div>
                        <p style="margin-bottom: 10px;">{row['Disponibilidade']:.2f}h / {30.0}h</p>
                        <p style="margin-bottom: 0px;">Afinidade</p>
                        <div style="width: 80%; background-color: #{back_color}; border-radius: 5px; height: 20px; overflow: hidden; margin-bottom: 5px; position: relative;">
                            <!-- Largura da barra de progresso -->
                            <div style="width: {min(100, (row['Afinidade'] / 10.0) * 100)}%; background-color: 
                                {'#2fa83b' if (row['Afinidade'] / 10.0) * 100 > 70 else '#fbac04' if (row['Afinidade'] / 10.0) * 100 >= 40 else '#c93220'}; 
                                height: 100%;"></div>
                            <!-- Barrinha de demarcação visual -->
                            <div style="position: absolute; top: 0; bottom: 0; width: 3px; background-color: black; left: {min(100, (afini_media / 10.0) * 100)}%;"></div>
                        </div>
                        <p style="margin-bottom: 0px;">{row['Afinidade']:.2f} / {10.0}</p>
                    </div>
                    <!-- Garantir que 'Nota Final' tenha largura fixa e não afete a barra -->
                    <div style="text-align: right; flex-shrink: 0; padding-left: 10px;">
                        <h3>{row['Nota Final']:.2f}</h3> <!-- Exibindo com 2 casas decimais -->
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ##9bacbd
        st.write("")