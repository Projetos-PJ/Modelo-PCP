import streamlit as st
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Ambiente de Projetos", layout="wide", initial_sidebar_state="expanded")

# Configurando o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lista de cargos a serem excluídos
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

# Função aprimorada para carregar dados
@st.cache_data
def load_pcp_data():
    try:
        return new_func()
    
    except FileNotFoundError:
        st.error("Arquivo PCP Auto.xlsx não encontrado na pasta de downloads. Verifique se o arquivo existe lá.", icon="🚨")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}", icon="🚨")
        st.stop()

def new_func():
    try:
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        file_path = os.path.join(downloads_path, "PCP Auto.xlsx")
        
        # Especifica quais abas carregar
        sheet_names = ['NDados', 'NTec', 'NCiv', 'NI', 'NCon']
        
        # Carrega todas as abas especificadas
        all_sheets = {}
        
        # Define os tipos de colunas para otimizar a memória
        dtype_dict = {
            'Membro': 'category',
            'Cargo no núcleo': 'category',
            'Área de atuação': 'category',
            'Como se sente em relação à carga': 'category'
        }
        
        # Colunas de data que serão convertidas ao carregar
        date_columns = [
            'Início previsto Projeto 1', 'Início previsto Projeto 2',
            'Início Real Projeto 1', 'Início Real Projeto 2',
            'Fim previsto do Projeto 1 (sem atraso)', 'Fim previsto do Projeto 2 (sem atraso)',
            'Fim estimado do Projeto 1 (com atraso)', 'Fim estimado do Projeto 2 (com atraso)'
        ]
        parse_dates = date_columns
        
        # Carrega cada aba e pré-processa
        for sheet in sheet_names:
            # Carrega a aba
            pcp_df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl', 
                              dtype=dtype_dict, parse_dates=parse_dates)
            
            # Substitui '-' por NaN
            pcp_df.replace('-', np.nan, inplace=True)
            
            # Remove cargos excluídos
            if 'Cargo no núcleo' in pcp_df.columns:
                pcp_df = pcp_df[~pcp_df['Cargo no núcleo'].isin(cargos_excluidos)]
            
            # Armazena no dicionário
            all_sheets[sheet] = pcp_df
        
        return all_sheets
    
    except FileNotFoundError:
        st.error("Arquivo PCP Auto.xlsx não encontrado na pasta de downloads. Verifique se o arquivo existe lá.", icon="🚨")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}", icon="🚨")
        st.stop()

# Função para obter e filtrar dados de um núcleo específico
def nucleo_func(nucleo_digitado):
    # Normaliza a entrada
    nucleo_digitado = nucleo_digitado.replace(" ", "").lower()
    
    # Mapeamento de nomes normalizados para nomes de abas
    nucleos_map = {
        'nciv': 'NCiv',
        'ncon': 'NCon',
        'ndados': 'NDados',
        'ni': 'NI',
        'ntec': 'NTec'
    }
    
    # Check if PCP data is loaded in session_state
    if 'pcp' not in st.session_state:
        st.session_state.pcp = load_pcp_data()
    
    # Obtém o nome da aba usando o mapeamento
    sheet_name = nucleos_map.get(nucleo_digitado)
    
    if not sheet_name or sheet_name not in st.session_state.pcp:
        return None
    
    # Retorna uma cópia do DataFrame já pré-processado
    return st.session_state.pcp[sheet_name].copy()

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

# Função para converter colunas de data
def converte_data(df, date_columns):
    df_copy = df.copy()
    for col in date_columns:
        if col in df_copy.columns:
            try:
                df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
            except Exception as e:
                logging.error(f"Erro ao converter coluna '{col}': {e}")
    return df_copy

if page == "Base Consolidada":
    # Carregar o núcleo selecionado
    with st.spinner('Carregando...'):
        if st.session_state.nucleo != None:
            pcp_df = nucleo_func(st.session_state.nucleo)
            if pcp_df is None:
                st.warning(f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️")
                st.stop()
            pcp_df.replace('-', np.nan, inplace=True)
            cronograma = pcp_df

            date_columns = [
                'Início previsto Projeto 1', 'Início previsto Projeto 2',
                'Início Real Projeto 1', 'Início Real Projeto 2',
                'Fim previsto do Projeto 1 (sem atraso)', 'Fim previsto do Projeto 2 (sem atraso)',
                'Fim estimado do Projeto 1 (com atraso)', 'Fim estimado do Projeto 2 (com atraso)'
            ]
            
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
                    default_index = []
                    aloc = st.multiselect(
                        "",
                        placeholder="Alocações",
                        options=opcoes,
                        default=[opcoes[i] for i in default_index]  # Convertendo índices para opções correspondentes
                    )
                # Filtragem dos dados
                if nome:
                    pcp_df = pcp_df[pcp_df['Membro'] == nome]
                    
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
                        
                    pcp_df['N° Alocações'] = pcp_df.apply(count_alocations, axis=1)

                    # Converter as opções selecionadas para inteiros correspondentes ao número de alocações
                    aloc_indices = [opcoes.index(opt) for opt in aloc]

                    # Filtrar o DataFrame com base nos índices de alocação selecionados
                    pcp_df = pcp_df[pcp_df['N° Alocações'].isin(aloc_indices)]

                    pcp_df = pcp_df.drop('N° Alocações', axis=1, errors='ignore')

            if pcp_df.empty:
                st.write("Sem informações para os dados filtrados")
            else:
                pcp_df = pcp_df.dropna(axis=1, how='all')
                pcp_df

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

                # Função para adicionar traces ao gráfico de Gantt
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
    # Funções de Backend
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
        sentimento_carga = str(analista.get('Como se sente em relação à carga', '')).strip().upper()
        sentimento_map = {'SUBALOCADO': 10, 'ESTOU SATISFEITO': 5, 'SUPERALOCADO': 1}
        sentimento_nota = sentimento_map.get(sentimento_carga, 5)  # Se não estiver mapeado, assume 5
        saude_mental = analista.get('Saúde mental na PJ', 5)

        saude_final = (sentimento_nota + saude_mental) / 2

        # Nota final de afinidade é a média dos três critérios
        afinidade = (satisfacao_portfolio + capacidade + saude_final) / 3
        return afinidade
    
    # Verifica se um núcleo foi selecionado
    if not st.session_state.nucleo:
        st.warning("Por favor, selecione um núcleo primeiro.", icon="⚠️")
        st.stop()
    
    # Obtém o dataframe para o núcleo selecionado
    pcp_df = nucleo_func(st.session_state.nucleo)
    
    if pcp_df is None:
        st.warning(f"Nenhum dado encontrado para o núcleo: {st.session_state.nucleo}", icon="⚠️")
        st.stop()
        
    # Substitui '-' por NaN
    pcp_df.replace('-', np.nan, inplace=True)
    
    # Define os portfólios com base no núcleo selecionado
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

    # Cria um layout de 3 colunas para os filtros
    col_escopo, col_analista, col_data = st.columns(3)
    
    with col_escopo:
        escopo = st.selectbox(
            "Portfólio",
            options=escopos,
            index=0
        )
        
    with col_analista:
        analistas = sorted(pcp_df['Membro'].astype(str).unique().tolist())
        analista_selecionado = st.selectbox(
            "Analista",
            options=["Todos"] + analistas, 
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
    
    # Segunda linha para a data de fim
    col_empty1, col_empty2, col_fim = st.columns(3)
    with col_fim:
        fim = st.date_input(
            "Data de Fim do Projeto", 
            min_value=inicio, 
            max_value=datetime(datetime.today().year + 1, 12, 31).date(), 
            value=inicio + pd.Timedelta(days=56),  # Padrão para 8 semanas após o início
            format="DD/MM/YYYY"
        )
    
    # Converte para timestamp para cálculos
    inicio_novo_projeto = pd.Timestamp(inicio)
    
    # Converte datas para datetime
    date_cols = [f'Fim previsto do Projeto {i}' for i in range(1, 5)] + \
                [f'Fim estimado do Projeto {i}' for i in range(1, 5)] + \
                [f'Fim do Projeto Interno {i}' for i in range(1, 5)]

    pcp_df = converte_data(pcp_df, date_cols)

    # Filtra por analista se um for selecionado
    if analista_selecionado != "Todos":
        pcp_df = pcp_df[pcp_df['Membro'] == analista_selecionado]
        
    if len(pcp_df) == 0:
        st.warning("Nenhum analista encontrado com os filtros selecionados.", icon="⚠️")
        st.stop()

    # Calcula todas as métricas de uma vez
    pcp_df['Disponibilidade'] = pcp_df.apply(lambda row: calcular_disponibilidade(row, inicio_novo_projeto), axis=1)
    
    # Calcula Nota Disponibilidade
    max_disponibilidade = 30
    min_disponibilidade = pcp_df['Disponibilidade'].min()
    range_disponibilidade = max_disponibilidade - min_disponibilidade
    
    if range_disponibilidade != 0:
        scaling_factor = 10 / range_disponibilidade
        pcp_df['Nota Disponibilidade'] = (pcp_df['Disponibilidade'] - min_disponibilidade) * scaling_factor
    else:
        pcp_df['Nota Disponibilidade'] = 10
    
    # Calcula Afinidade
    # Calcula Nota Final como média ponderada
    # Inputs para pesos
    afinidade_weight = st.number_input("Peso da Afinidade (0.0 - 1.0)", min_value=0.3, max_value=0.7, value=0.5, step=0.1)
    disponibilidade_weight = st.number_input("Peso da Disponibilidade (0.0 - 1.0)", min_value=0.3, max_value=0.7, value=0.5, step=0.1)
    
    # Garante que os pesos somem 1
    if afinidade_weight + disponibilidade_weight != 1.0:
        st.warning("A soma dos pesos deve ser igual a 1. Ajustando os valores.")
        
        # Ajusta os pesos para que somem 1
        afinidade_weight = round(afinidade_weight, 1)
        disponibilidade_weight = round(1 - afinidade_weight, 1)
        
        st.write(f"Peso da Afinidade ajustado para: {afinidade_weight}")
        st.write(f"Peso da Disponibilidade ajustado para: {disponibilidade_weight}")
    
    pcp_df['Afinidade'] = pcp_df.apply(calcular_afinidade, axis=1)
    
    # Calcula Nota Final diretamente
    pcp_df['Nota Final'] = (pcp_df['Afinidade'] * afinidade_weight + pcp_df['Nota Disponibilidade'] * disponibilidade_weight)
    # Calcula Nota Final diretamente
    pcp_df['Nota Final'] = (pcp_df['Afinidade'] + pcp_df['Nota Disponibilidade']) / 2
    
    # Ordena pela nota final
    pcp_df = pcp_df.sort_values(by='Nota Final', ascending=False)

    # Cria um divisor
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
    # Função para formatar o DataFrame para exibição
    def format_display_df(pcp_df):
        formatted_df = pcp_df[['Membro', 'Disponibilidade', 'Afinidade', 'Nota Final']].copy()
        formatted_df['Disponibilidade'] = formatted_df['Disponibilidade'].apply(lambda x: f"{x:.1f}h")
        formatted_df['Afinidade'] = formatted_df['Afinidade'].apply(lambda x: f"{x:.1f}/10")
        formatted_df['Nota Final'] = formatted_df['Nota Final'].apply(lambda x: f"{x:.1f}/10")
        return formatted_df

    # Formata as colunas para melhor exibição
    display_df = format_display_df(pcp_df)

    # Exibe a tabela
    st.table(display_df)