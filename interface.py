import streamlit as st
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Ambiente de Projetos", layout="wide", initial_sidebar_state="expanded")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of positions to exclude
cargos_excluidos = [
    'Líder de Outbound', 
    'Coordenador de Negócios', 
    'Coordenador de Inovação Comercial', 
    'Gerente Comercial',
    'Coordenador de Projetos', 
    'Coordenador de Inovação de Projetos', 
    'Gerente de Projetos'
]

page = st.sidebar.selectbox(
    "Escolha uma página",
    ("Base Consolidada", "PCP")
)

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
    </style>
    <div class="fullscreen-div">
    </div>
    """, 
    unsafe_allow_html=True
)

# O título agora aparecerá sobre o 'div'
if page == "Base Consolidada":
    st.title("Base Consolidada")
if page == "PCP":
    st.title("PCP")

# Improved data loading function
@st.cache_data
def load_pcp_data():
    """
    Load the PCP data from the Excel file and cache it to improve performance.
    
    Returns:
        dict: Dictionary with sheet names as keys and DataFrames as values
    """
    try:
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        file_path = os.path.join(downloads_path, "PCP Auto.xlsx")
        return pd.read_excel(file_path, sheet_name=None)
    except FileNotFoundError:
        st.error("Arquivo PCP Auto.xlsx não encontrado na pasta de downloads. Verifique se o arquivo existe lá.", icon="🚨")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}", icon="🚨")
        st.stop()

# Carregando os dados
if 'pcp' not in st.session_state:
    with st.spinner('Carregando dados...'):
        st.session_state.pcp = load_pcp_data()
        # Precompute lookup dictionary for faster sheet access
        st.session_state.sheet_lookup = {
            sheet.replace(" ", "").lower(): sheet 
            for sheet in st.session_state.pcp.keys()
        }

# Function to get and filter data from a specific nucleus
def nucleo_func(nucleo_digitado):
    """
    Retrieve and filter data for the specified nucleus.
    
    Args:
        nucleo_digitado (str): Name of the nucleus to retrieve
        
    Returns:
        pd.DataFrame: Filtered DataFrame for the specified nucleus
    """
    # Normalize input
    nucleo_digitado = nucleo_digitado.replace(" ", "").lower()
    
    # Get original sheet name if it exists
    sheet_name = st.session_state.sheet_lookup.get(nucleo_digitado)
    
    if not sheet_name:
        return None
    
    # Get the DataFrame
    df = st.session_state.pcp[sheet_name].copy()
    
    # Filter out excluded positions
    try:
        if 'Cargo no núcleo' in df.columns:
            return df[~df['Cargo no núcleo'].isin(cargos_excluidos)]
        return df
    except Exception as e:
        logging.error(f"Error filtering positions for nucleus {nucleo_digitado}: {e}")
        return df

# Inicializando session_state para manter os valores dos filtros
if 'nucleo' not in st.session_state:
    st.session_state.nucleo = None
if 'escopo' not in st.session_state:
    st.session_state.escopo = None
if 'nome' not in st.session_state:
    st.session_state.nome = ''
if 'cargo' not in st.session_state:
    st.session_state.cargo = ''
if 'aloc' not in st.session_state:
    st.session_state.aloc = None

# Layout dos botões de seleção de núcleo
colnan, colciv, colcon, coldados, colni, coltec = st.columns([1, 2, 2, 2, 2, 2])
with colciv:
    if st.button("NCiv"):
        st.session_state.nucleo = 'NCiv'
with colcon:
    if st.button("NCon"):
        st.session_state.nucleo = 'NCon'
with coldados:
    if st.button("NDados"):
        st.session_state.nucleo = 'NDados'
with colni:
    if st.button("NI"):
        st.session_state.nucleo = 'NI'
with coltec:
    if st.button("NTec"):
        st.session_state.nucleo = 'NTec'

if page == "Base Consolidada":
    # Carregar o núcleo selecionado
    with st.spinner('Carregando...'):
        if st.session_state.nucleo != None:
            pcp = nucleo_func(st.session_state.nucleo)
            if pcp is None:
                st.warning(f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️")
                st.stop()
            pcp.replace('-', np.nan, inplace=True)
            cronograma = pcp

            date_columns = [
                'Início previsto Projeto 1', 'Início previsto Projeto 2',
                'Início Real Projeto 1', 'Início Real Projeto 2',
                'Fim previsto do Projeto 1 (sem atraso)', 'Fim previsto do Projeto 2 (sem atraso)',
                'Fim estimado do Projeto 1 (com atraso)', 'Fim estimado do Projeto 2 (com atraso)'
            ]

            def convert_and_format_date(pcp, column):
                try:
                    converted_dates = pd.to_datetime(pcp[column], format='%d/%m/%Y', errors='coerce')
                    pcp[column] = converted_dates.dt.strftime('%d/%m/%Y')
                except Exception as e:
                    st.error(f"Erro ao converter a coluna '{column}': {e}", icon="🚨")
                return pcp[column]
            for col in date_columns:
                pcp[col] = convert_and_format_date(pcp, col)
            
            # Filtros
            colcargo, colnome, colaloc = st.columns(3)
            with colnome:
                nome = st.text_input("", placeholder='Membro', value=st.session_state.nome if st.session_state.nome else None)
                st.session_state.nome = nome
            with colcargo:
                cargo = st.text_input("", placeholder='Cargo', value=st.session_state.cargo if st.session_state.cargo else None)
                st.session_state.cargo = cargo
            with colaloc:
                opcoes = ['Desalocado', '1 Alocação', '2 Alocações', '3 Alocações', '4+ Alocações']
                
                # Garantir que o índice padrão seja válido
                if st.session_state.aloc and st.session_state.aloc in opcoes:
                    default_index = [opcoes.index(st.session_state.aloc)]  # Se o valor de aloc está presente, use o índice
                else:
                    default_index = []  # Se não, inicie com uma lista vazia
                
                # O multiselect pode retornar uma lista de opções selecionadas
                aloc = st.multiselect(
                    "",
                    placeholder="Alocações",
                    options=opcoes,
                    default=default_index  # Usando o valor de default_index como uma lista de índices
                )
                # Filtragem dos dados
                if nome:
                    pcp = pcp[pcp['Membro'] == nome]
                    
                    def count_alocations(analista):
                        relevant_columns = [
                            'Projeto 1', 'Projeto 2', 'Projeto 3',
                            'Projeto Interno 1', 'Projeto Interno 2', 'Projeto Interno 3',
                            'Cargo WI', 'Cargo MKT', 'Assessoria/Liderança', 'Equipe de PS'
                        ]
                        alocacoes = analista[relevant_columns].notna().sum()
                        try:
                            alocacoes += analista.get('N° Aprendizagens', 0) if pd.notna(analista.get('N° Aprendizagens', None)) else 0
                            return min(alocacoes, 4)
                        except Exception as e:
                            st.warning(f"Erro ao calcular alocações: {e}", icon="⚠️")
                            return 0
                        
                    pcp['N° Alocações'] = pcp.apply(count_alocations, axis=1)

                    # Converter as opções selecionadas para inteiros correspondentes ao número de alocações
                    aloc_indices = [opcoes.index(opt) for opt in aloc]

                    # Filtrar o DataFrame com base nos índices de alocação selecionados
                    pcp = pcp[pcp['N° Alocações'].isin(aloc_indices)]

                    pcp = pcp.drop('N° Alocações', axis=1, errors='ignore')

            if pcp.empty:
                st.write("Sem informações para os dados filtrados")
            else:
                pcp = pcp.dropna(axis=1, how='all')
                pcp

            if nome and nome in cronograma['Membro'].values:
                st.write('---')
                cronograma = cronograma[cronograma['Membro'] == nome]

                date_columns_gantt = [
                    "Início Real Projeto 1", "Fim previsto do Projeto 1 (sem atraso)", "Fim estimado do Projeto 1 (com atraso)",
                    "Início Real Projeto 2", "Fim previsto do Projeto 2 (sem atraso)", "Fim estimado do Projeto 2 (com atraso)",
                    "Início Real Projeto 3", "Fim previsto do Projeto 3 (sem atraso)", "Fim estimado do Projeto 3 (com atraso)",
                    "Início do Projeto Interno 1", "Início do Projeto Interno 2", "Fim do Projeto Interno 1", "Fim do Projeto Interno 2"
                ]

                for col in date_columns_gantt:
                    try:
                        cronograma[col] = pd.to_datetime(cronograma[col], format='%d/%m/%Y', errors='coerce')
                    except Exception as e:
                        st.error(f"Erro ao converter a coluna '{col}' para datetime: {e}", icon="🚨")

                mes = datetime.today().month
                for col in date_columns_gantt:
                    try:
                        cronograma[col] = pd.to_datetime(cronograma[col], format='%d/%m/%Y', errors='coerce')
                    except Exception as e:
                        st.error(f"Erro ao converter a coluna '{col}' para datetime: {e}", icon="🚨")
                cronograma["Fim trimestre"] = datetime(datetime.today().year, 6, 30)
         
                cronograma = cronograma.dropna(axis=1, how='all')
                nome_formatado = ' '.join([part.capitalize() for part in nome.split('.')])
                st.subheader(nome_formatado)
                colunas = cronograma.columns
                pontos = []
                yaxis = []
                axis = 0

                # Function to add traces to the Gantt chart
                def add_gantt_trace(fig, start_col, end_col, name, color, axis):
                    fig.add_trace(go.Scatter(
                        x=[cronograma[start_col].iloc[0], cronograma[end_col].iloc[0]],
                        y=[axis, axis],
                        mode='lines',
                        name=name,
                        line=dict(color=color, width=4)
                    ))

                # Plotando o gráfico
                fig = go.Figure()

                # Dicionário de projetos e cores
                projects = {
                    'Projeto 1': {'start': "Início Real Projeto 1", 'end': "Fim Projeto 1", 'color': '#b4944c'},
                    'Projeto 2': {'start': "Início Real Projeto 2", 'end': "Fim Projeto 2", 'color': '#9a845c'},
                    'Projeto 3': {'start': "Início Real Projeto 3", 'end': "Fim Projeto 3", 'color': '#847c64'},
                }

                # Iterando sobre os projetos
                for projeto, config in projects.items():
                    if projeto in colunas:
                        pontos.append(cronograma[projeto])
                        axis += 1
                        yaxis.append(axis)
                        try:
                            cronograma["Fim " + projeto.split(' ')[1]] = cronograma["Fim estimado do Projeto " + projeto.split(' ')[1] + " (com atraso)"]
                        except KeyError as e:
                            st.warning(f"Coluna ausente para determinar o fim do projeto {projeto}: {e}", icon="⚠️")
                            cronograma["Fim " + projeto.split(' ')[1]] = None
                        except Exception as e:
                            st.error(f"Erro inesperado ao determinar o fim do projeto {projeto}: {e}", icon="🚨")
                            cronograma["Fim " + projeto.split(' ')[1]] = None
                        add_gantt_trace(fig, config['start'], config['end'], cronograma[projeto].iloc[0], config['color'], axis)

                if 'Assessoria/Liderança' in colunas:
                    pontos.append(cronograma['Assessoria/Liderança'])
                    axis +=1
                    yaxis.append(axis)
                    # Adicionando o cargo
                    fig.add_trace(go.Scatter(x=[cronograma["Inicio trimestre"].iloc[0], cronograma["Fim trimestre"].iloc[0]],
                                            y=[axis, axis],
                                            mode='lines',
                                            name=cronograma['Assessoria/Liderança'].iloc[0],
                                            line=dict(color='#244c8c', width=4)))
                
                internal_projects = {
                    'Projeto Interno 1': {'start': "Início do Projeto Interno 1", 'end': "Fim do Projeto Interno 1", 'color': '#405094'},
                    'Projeto Interno 2': {'start': "Início do Projeto Interno 2", 'end': "Fim do Projeto Interno 2", 'color': '#405094'}
                }

                for projeto, config in internal_projects.items():
                    if projeto in colunas:
                        if config['end'] in colunas:
                            pontos.append(cronograma[projeto])
                            axis += 1
                            yaxis.append(axis)
                            add_gantt_trace(fig, config['start'], config['end'], cronograma[projeto].iloc[0], config['color'], axis)
                        else:
                            st.error(f'Não foi possível determinar o fim do projeto interno {cronograma[projeto].iloc[0]}', icon="⚠")

                if 'N° Aprendizagens' in colunas:
                    # if cronograma['N° Aprendizagens'].iloc[0] != 0:
                    aprendizagens = cronograma['N° Aprendizagens'].iloc[0]
                    for quantidade in range(aprendizagens):
                        pontos.append(f'Aprendizagem {quantidade+1}')
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando aprendizagens
                        fig.add_trace(go.Scatter(x=[cronograma["Inicio trimestre"].iloc[0], cronograma["Fim trimestre"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=f'Aprendizagem {quantidade+1}',
                                                line=dict(color='#e4ab34', width=4)))
                # Configurando o layout
                fig.update_layout(
                    title="Cronograma das Alocações",
                    xaxis_title=None,
                    yaxis_title="Alocações",
                    xaxis=dict(tickformat="%m/%Y"),
                    yaxis=dict(tickvals=yaxis, ticktext=pontos),
                    showlegend=True
                )
                if axis != 0:
                    # Exibindo o gráfico no Streamlit
                    st.plotly_chart(fig)
                if 'Projeto 1' in colunas:
                    if 'Projeto 2' in colunas:
                        if 'Projeto 3' in colunas:
                            colrole, colpro1, colpro2, colpro3 = st.columns(4)
                            if 'Satisfação com o Projeto 3' not in colunas:
                                cronograma['Satisfação com o Projeto 3'] = 'não mapeada'
                            with colpro3:
                                st.markdown(
                                    """
                                    <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                                        <h3>"""f'Portfólio de {cronograma['Projeto 3'].iloc[0]}'"""</h3>
                                        <p>"""f'{cronograma['Portfólio do Projeto 3'].iloc[0]}'""", """f'Satisfação {cronograma['Satisfação com o Projeto 3'].iloc[0]}'"""</p>
                                    </div>
                                    """, unsafe_allow_html=True
                                )
                        else: colrole, colpro1, colpro2 = st.columns(3)
                        if 'Satisfação com o Projeto 2' not in colunas:
                                cronograma['Satisfação com o Projeto 2'] = 'não mapeada'
                        with colpro2:
                            st.markdown(
                                """
                                <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                                    <h3>"""f'Portfólio de {cronograma['Projeto 2'].iloc[0]}'"""</h3>
                                    <p>"""f'{cronograma['Portfólio do Projeto 2'].iloc[0]}'""", """f'Satisfação {cronograma["Satisfação com o Projeto 2"].iloc[0]}'"""</p>
                                </div>
                                """, unsafe_allow_html=True
                            )
                    else: colrole, colpro1 = st.columns(2)
                    if 'Satisfação com o Projeto 1' not in colunas:
                        cronograma['Satisfação com o Projeto 1'] = 'não mapeada'
                    with colpro1:
                        st.markdown(
                            """
                            <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                                <h3>"""f'Portfólio de {cronograma['Projeto 1'].iloc[0]}'"""</h3>
                                <p>"""f'{cronograma['Portfólio do Projeto 1'].iloc[0]}'""", """f'Satisfação {cronograma['Satisfação com o Projeto 1'].iloc[0]}'"""</p>
                            </div>
                            """, unsafe_allow_html=True
                        )
                else: 
                    colrole, blank = st.columns(2)
                if 'Cargo no núcleo' not in colunas:
                    cronograma['Cargo no núcleo'] = 'Cargo não mapeado'
                if 'Área de atuação' not in colunas:
                    cronograma['Área de atuação'] = 'Área de atuação não mapeada'
                with colrole:
                    st.markdown(
                        """
                        <div style="border: 1px solid #fbac04; padding: 10px; border-radius: 0px; width: 250px; color:#064381";>
                            <h3>"""f'Cargo de {nome_formatado}'"""</h3>
                            <p>"""f'{cronograma["Cargo no núcleo"].iloc[0]}'""" - """f'{cronograma['Área de atuação'].iloc[0]}'"""</p>
                        </div>
                        """, unsafe_allow_html=True
                    )

if page == 'PCP':
    # Backend Functions
    def calcular_disponibilidade(analista, inicio_novo_projeto):
        horas_disponiveis = 30  # Começamos com 30h disponíveis

        # Subtrai horas conforme aprendizados e assessorias
        horas_disponiveis -= analista.get('N° Aprendizagens', 0) * 5
        horas_disponiveis -= analista.get('N° Assessoria', 0) * 10

        # Subtrai horas conforme projetos ativos (cada projeto reduz 10h)
        for i in range(1, 5):  # Projetos 1 a 4
            if pd.notnull(analista.get(f'Fim previsto do Projeto {i}', None)):
                horas_disponiveis -= 10

        # Subtrai horas conforme projetos internos ativos (cada um reduz 5h)
        for i in range(1, 5):  # Projetos Internos 1 a 4
            if pd.notnull(analista.get(f'Início do Projeto Interno {i}', None)):
                horas_disponiveis -= 5

        # Ajusta conforme cargo no núcleo
        cargo = str(analista.get('Cargo no núcleo', '')).strip().upper()
        if cargo in ['SDR', 'HUNTER']:
            horas_disponiveis -= 10
        elif cargo == 'ANALISTA SÊNIOR':
            horas_disponiveis -= 5

        # Ajusta conforme proximidade da data de fim de um projeto
        for i in range(1, 5):  # Projetos 1 a 4
            fim_estimado = analista.get(f'Fim estimado do Projeto {i}', None)
            fim_previsto = analista.get(f'Fim previsto do Projeto {i}', None)

            fim_projeto = fim_estimado if pd.notnull(fim_estimado) else fim_previsto

            if pd.notnull(fim_projeto):
                days_left = (fim_projeto - inicio_novo_projeto).days
                if 7 < days_left <= 14:
                    horas_disponiveis += 6
                elif days_left <= 7:
                    horas_disponiveis += 10
        return horas_disponiveis

    def calcular_afinidade(analista):
        # Satisfação esperada = Satisfação Média com o Portfólio * 2
        satisfacao_portfolio = analista.get('Satisfação Média com o Portfólio', 0) * 2

        # Capacidade esperada = Validação média do Projeto * 2
        capacidade = analista.get('Validação média do Projeto', 0) * 2

        # Saúde mental = Média entre percepção da carga e saúde mental na PJ
        # NEUTRO É 5
        sentimento_carga = analista.get('Como se sente em relação à carga', '').strip().upper()
        sentimento_map = {'SUBALOCADO': 10, 'ESTOU SATISFEITO': 5, 'SUPERALOCADO': 1}
        sentimento_nota = sentimento_map.get(sentimento_carga, 5)  # Se não estiver mapeado, assume 5
        saude_mental = analista.get('Saúde mental na PJ', 5)

        saude_final = (sentimento_nota + saude_mental) / 2

        # Nota final de afinidade é a média dos três critérios
        afinidade = (satisfacao_portfolio + capacidade + saude_final) / 3
        return afinidade
    
    # Check if a nucleus is selected
    if not st.session_state.nucleo:
        st.warning("Por favor, selecione um núcleo primeiro.", icon="⚠️")
        st.stop()
    
    # Get the dataframe for the selected nucleus
    pcp = nucleo_func(st.session_state.nucleo)
    
    if pcp is None:
        st.warning(f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️")
        st.stop()
        
    # Replace '-' with NaN
    pcp.replace('-', np.nan, inplace=True)
    
    # Define portfolios based on selected nucleus
    match st.session_state.nucleo:
        case 'NCiv':
            escopos = ['Arquitetônico', 'Design de Interiores', 'Elétrico/Fotovoltaico', 'Estrutural', 'Hidrossanitário', 'Real State', 'Não mapeado']
        case "NCon":
            escopos = ['Gestão de Processos', 'Pesquisa de Mercado', 'Planejamento Estratégico', 'Modelagem e Projeção','Não mapeado']
        case 'NDados':
            escopos = ['Ciência de Dados', 'DSaaS', 'Engenharia de Dados', 'Inteligência Artificial', 'Inteligência de Negócios', 'Não mapeado']
        case "NI":
            escopos = ['Inovacamp', 'VBaaS', 'Não mapeado']
        case 'NTec':
            escopos = ['Delivery', 'Descoberta de Produto', 'Discovery', 'Escopo Aberto', 'Não mapeado']
        case _:
            escopos = ['Não mapeado']

    # Create a 3-column layout for filters
    col_escopo, col_analista, col_data = st.columns(3)
    
    with col_escopo:
        escopo = st.selectbox(
            "Portfólio",
            options=escopos,
            index=0
        )
        
    with col_analista:
        analistas = sorted(pcp['Membro'].astype(str).unique().tolist())
        analista_selecionado = st.selectbox(
            "Analista", 
            options=analistas,
            index=0
        )
    
    with col_data:
        inicio = st.date_input(
            "Data de Início do Projeto", 
            min_value=datetime(datetime.today().year - 1, 1, 1).date(), 
            max_value=datetime(datetime.today().year + 1, 12, 31).date(), 
            value=datetime.today().date(), 
            format="DD/MM/YYYY"
        )
    
    # Second row for end date
    col_empty1, col_empty2, col_fim = st.columns(3)
    with col_fim:
        fim = st.date_input(
            "Data de Fim do Projeto", 
            min_value=inicio, 
            max_value=datetime(datetime.today().year + 1, 12, 31).date(), 
            value=inicio + pd.Timedelta(days=56),  # Default to 8 semanas after start 
            format="DD/MM/YYYY"
        )
    
    # Convert to timestamp for calculations
    inicio_novo_projeto = pd.Timestamp(inicio)

    # Converte datas para datetime
    date_cols = [f'Fim previsto do Projeto {i}' for i in range(1, 5)] + \
                [f'Fim estimado do Projeto {i}' for i in range(1, 5)] + \
                [f'Fim do Projeto Interno {i}' for i in range(1, 5)]
    for col in date_cols:
        try:
            pcp[col] = pd.to_datetime(pcp[col], errors='coerce')
        except Exception as e:
            logging.error(f"Error converting column '{col}' to datetime: {e}")

    # Filter by analyst if one is selected
    if analista_selecionado != "Todos":
        pcp = pcp[pcp['Membro'] == analista_selecionado]
        
    if len(pcp) == 0:
        st.warning("Nenhum analista encontrado com os filtros selecionados.", icon="⚠️")
        st.stop()

    # Calculate all metrics at once
    pcp['Disponibilidade'] = pcp.apply(lambda row: calcular_disponibilidade(row, inicio_novo_projeto), axis=1)
    
    # Calculate Nota Disponibilidade
    max_disponibilidade = 30
    min_disponibilidade = pcp['Disponibilidade'].min()
    
    if max_disponibilidade != min_disponibilidade:
        pcp['Nota Disponibilidade'] = 10 * (pcp['Disponibilidade'] - min_disponibilidade) / (max_disponibilidade - min_disponibilidade)
    else:
        pcp['Nota Disponibilidade'] = 10
    
    # Calculate Afinidade
    pcp['Afinidade'] = pcp.apply(calcular_afinidade, axis=1)
    
    # Calculate Nota Final directly
    pcp['Nota Final'] = (pcp['Afinidade'] + pcp['Nota Disponibilidade']) / 2
    
    # Sort by the final score
    pcp = pcp.sort_values(by='Nota Final', ascending=False)

    # Create a divider
    st.markdown("---")
    
    # Exibe as colunas principais
    if analista_selecionado == "Todos":
        st.subheader("Membros sugeridos para o projeto")
    else:
        st.subheader(f"Análise de disponibilidade para {analista_selecionado}")
        
    st.markdown("""
    <div style="margin-bottom: 20px">
    <p><strong>Entendendo as pontuações:</strong></p>
    <ul>
      <li><strong>Disponibilidade</strong>: Horas estimadas disponíveis para novas atividades (máximo 30h)</li>
      <li><strong>Afinidade</strong>: Pontuação (0-10) baseada em satisfação com portfólio, capacidade técnica e saúde mental</li>
      <li><strong>Nota Final</strong>: Média ponderada entre disponibilidade e afinidade</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Format the columns for better display
    display_df = pcp[['Membro', 'Disponibilidade', 'Afinidade', 'Nota Final']].copy()
    
    # Format numeric columns to 1 decimal place
    display_df['Disponibilidade'] = display_df['Disponibilidade'].apply(lambda x: f"{x:.1f}h")
    display_df['Afinidade'] = display_df['Afinidade'].apply(lambda x: f"{x:.1f}/10")
    display_df['Nota Final'] = display_df['Nota Final'].apply(lambda x: f"{x:.1f}/10") 
    
    # Display the table
    st.table(display_df)