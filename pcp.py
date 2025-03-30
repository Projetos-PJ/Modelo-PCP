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

date_columns = [
                    "Início Real Projeto 1", "Fim previsto do Projeto 1 (sem atraso)", "Fim estimado do Projeto 1 (com atraso)",
                    "Início Real Projeto 2", "Fim previsto do Projeto 2 (sem atraso)", "Fim estimado do Projeto 2 (com atraso)",
                    "Início Real Projeto 3", "Fim previsto do Projeto 3 (sem atraso)", "Fim estimado do Projeto 3 (com atraso)",
                    "Início Real Projeto 4", "Fim previsto do Projeto 4 (sem atraso)", "Fim estimado do Projeto 4 (com atraso)",
                    "Início do Projeto Interno 1", "Início do Projeto Interno 2", "Início do Projeto Interno 3",
                    "Fim do Projeto Interno 1", "Fim do Projeto Interno 2", "Fim do Projeto Interno 3"
]

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
        sheet_names = ['Cópia de NDados', 'NTec', 'NCiv', 'NI', 'NCon']
        
        # Carrega todas as abas especificadas
        all_sheets = {}
        
        # Define os tipos de colunas para otimizar a memória
        dtype_dict = {
            'Membro': 'category',
            'Cargo no núcleo': 'category',
            'Área de atuação': 'category',
            'Como se sente em relação à carga': 'category'
        }
        
        parse_dates = date_columns
        
        # Carrega cada aba e pré-processa
        for sheet in sheet_names:
            # Carrega a aba sem converter categorias inicialmente
            pcp_df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl', 
                              usecols=lambda x: x != 'Email PJ')
            
            # Converte colunas de data para o formato adequado
            for date_col in date_columns:
                if date_col in pcp_df.columns:
                    try:
                        pcp_df[date_col] = pd.to_datetime(pcp_df[date_col], format='%d/%m/%Y', errors='coerce').dt.strftime('%d/%m/%Y')
                    except Exception as e:
                        logging.warning(f"Erro ao converter coluna de data '{date_col}' na aba {sheet}: {e}")
            
            # Substitui '-' por NaN antes de converter para categorias
            pd.set_option('future.no_silent_downcasting', True)
            pcp_df.replace('-', np.nan, inplace=True)
            pd.set_option('future.no_silent_downcasting', False)
            
            # Converte colunas para categoria após substituição
            for col, dtype in dtype_dict.items():
                if col in pcp_df.columns:
                    pcp_df[col] = pcp_df[col].astype(dtype)
            
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
        'ndados': 'Cópia de NDados',
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
                # Converte para string primeiro antes de converter para datetime
                df_copy[col] = df_copy[col].astype(str)
                pd.set_option('future.no_silent_downcasting', True)
                result = df_copy[col].replace('nan', np.nan)
                pd.set_option('future.no_silent_downcasting', False)
                df_copy[col] = result.infer_objects(copy=False)
                df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce', format='mixed')
            except Exception as e:
                logging.error(f"Erro ao converter coluna '{col}': {e}")
    return df_copy

if page == "Base Consolidada":
    # Carregar o núcleo selecionado
    with st.spinner('Carregando...'):
        if st.session_state.nucleo != None:
            df = nucleo_func(st.session_state.nucleo)
            df.replace('-', np.nan, inplace=True)
            cronograma = df
            df['Início previsto Projeto 1'] = (pd.to_datetime(df['Início previsto Projeto 1'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início Real Projeto 1'] = (pd.to_datetime(df['Início Real Projeto 1'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim previsto do Projeto 1 (sem atraso)'] = (pd.to_datetime(df['Fim previsto do Projeto 1 (sem atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim estimado do Projeto 1 (com atraso)'] = (pd.to_datetime(df['Fim estimado do Projeto 1 (com atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início previsto Projeto 2'] = (pd.to_datetime(df['Início previsto Projeto 2'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início Real Projeto 2'] = (pd.to_datetime(df['Início Real Projeto 2'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim previsto do Projeto 2 (sem atraso)'] = (pd.to_datetime(df['Fim previsto do Projeto 2 (sem atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim estimado do Projeto 2 (com atraso)'] = (pd.to_datetime(df['Fim estimado do Projeto 2 (com atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início previsto Projeto 3'] = (pd.to_datetime(df['Início previsto Projeto 3'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início Real Projeto 3'] = (pd.to_datetime(df['Início Real Projeto 3'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim previsto do Projeto 3 (sem atraso)'] = (pd.to_datetime(df['Fim previsto do Projeto 3 (sem atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim estimado do Projeto 3 (com atraso)'] = (pd.to_datetime(df['Fim estimado do Projeto 3 (com atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início previsto Projeto 4'] = (pd.to_datetime(df['Início previsto Projeto 4'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início Real Projeto 4'] = (pd.to_datetime(df['Início Real Projeto 4'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim previsto do Projeto 4 (sem atraso)'] = (pd.to_datetime(df['Fim previsto do Projeto 4 (sem atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim estimado do Projeto 4 (com atraso)'] = (pd.to_datetime(df['Fim estimado do Projeto 4 (com atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início do Projeto Interno 1'] = (pd.to_datetime(df['Início do Projeto Interno 1'], errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim do Projeto Interno 1'] = (pd.to_datetime(df['Fim do Projeto Interno 1'], errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início do Projeto Interno 2'] = (pd.to_datetime(df['Início do Projeto Interno 2'], errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim do Projeto Interno 2'] = (pd.to_datetime(df['Fim do Projeto Interno 2'], errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início do Projeto Interno 3'] = (pd.to_datetime(df['Início do Projeto Interno 3'], errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim do Projeto Interno 3'] = (pd.to_datetime(df['Fim do Projeto Interno 3'], errors='coerce')).dt.strftime('%d/%m/%Y')

            
            # Filtros
            colcargo, colnome, colaloc = st.columns(3)
            with colnome:
                nome = st.text_input("Nome do Membro", placeholder='Membro', value=st.session_state.nome if st.session_state.nome else None)
                st.session_state.nome = nome
            with colcargo:
                cargo = st.text_input("Cargo", placeholder='Cargo', value=st.session_state.cargo if st.session_state.cargo else None)
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
                    "Alocações",
                    placeholder="Alocações",
                    options=opcoes,
                    default=default_index  # Usando o valor de default_index como uma lista de índices
                )
                # Filtragem dos dados
                if nome:
                    df = df[df['Membro'] == nome]
                if cargo:
                    df = df[df['Cargo no núcleo'] == cargo]

                if aloc:
                    filtrados = []
                    
                    # Para cada linha no DataFrame, calcular o número de alocações
                    for _, row in df.iterrows():
                        alocacoes = 0
                        try:
                            if pd.notna(row['Projeto 1']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Projeto 2']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Projeto 3']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Projeto Interno 1']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Projeto Interno 2']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Projeto Interno 3']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Cargo WI']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Cargo MKT']): alocacoes += 1
                        except: pass
                        try:
                            if row['N° Aprendizagens'] != 0: alocacoes += row['N° Aprendizagens']
                        except: pass
                        try:
                            if row['N° Assessorias'] != 0: alocacoes += row['N° Assessorias']
                        except: pass
                        
                        # Limitar o número de alocações para no máximo 4
                        if alocacoes > 4: 
                            alocacoes = 4
                        
                        # Verifica se o número de alocações corresponde a qualquer um dos selecionados
                        if alocacoes in [opcoes.index(opt) for opt in aloc]:
                            filtrados.append(row)
                    
                    df = pd.DataFrame(filtrados)

            if df.empty:
                st.write("Sem informações para os dados filtrados")
            else:
                df = df.dropna(axis=1, how='all')
                df


            if nome and nome in cronograma['Membro'].values:
                st.write('---')
                cronograma = cronograma[cronograma['Membro'] == nome]
                cronograma["Início Real Projeto 1"] = pd.to_datetime(cronograma["Início Real Projeto 1"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim previsto do Projeto 1 (sem atraso)"] = pd.to_datetime(cronograma["Fim previsto do Projeto 1 (sem atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim estimado do Projeto 1 (com atraso)"] = pd.to_datetime(cronograma["Fim estimado do Projeto 1 (com atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Início Real Projeto 2"] = pd.to_datetime(cronograma["Início Real Projeto 2"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim previsto do Projeto 2 (sem atraso)"] = pd.to_datetime(cronograma["Fim previsto do Projeto 2 (sem atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim estimado do Projeto 2 (com atraso)"] = pd.to_datetime(cronograma["Fim estimado do Projeto 2 (com atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Início Real Projeto 3"] = pd.to_datetime(cronograma["Início Real Projeto 3"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim previsto do Projeto 3 (sem atraso)"] = pd.to_datetime(cronograma["Fim previsto do Projeto 3 (sem atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim estimado do Projeto 3 (com atraso)"] = pd.to_datetime(cronograma["Fim estimado do Projeto 3 (com atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Início Real Projeto 4"] = pd.to_datetime(cronograma["Início Real Projeto 4"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim previsto do Projeto 4 (sem atraso)"] = pd.to_datetime(cronograma["Fim previsto do Projeto 4 (sem atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim estimado do Projeto 4 (com atraso)"] = pd.to_datetime(cronograma["Fim estimado do Projeto 4 (com atraso)"], format='%d/%m/%Y', errors='coerce')
                cronograma["Início do Projeto Interno 1"] = pd.to_datetime(cronograma["Início do Projeto Interno 1"], format='%d/%m/%Y', errors='coerce')
                cronograma["Início do Projeto Interno 2"] = pd.to_datetime(cronograma["Início do Projeto Interno 2"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim do Projeto Interno 1"] = pd.to_datetime(cronograma["Fim do Projeto Interno 1"], format='%d/%m/%Y', errors='coerce')
                cronograma["Fim do Projeto Interno 2"] = pd.to_datetime(cronograma["Fim do Projeto Interno 2"], format='%d/%m/%Y', errors='coerce')
                mes = datetime.today().month
                if mes in [1, 2, 3]:
                    cronograma["Inicio trimestre"] = datetime(datetime.today().year, 1, 1)
                    cronograma["Fim trimestre"] = datetime(datetime.today().year, 3, 31)
                elif mes in [4, 5, 6]:
                    cronograma["Inicio trimestre"] = datetime(datetime.today().year, 4, 1)
                    cronograma["Fim trimestre"] = datetime(datetime.today().year, 6, 30)
                elif mes in [7, 8, 9]:
                    cronograma["Inicio trimestre"] = datetime(datetime.today().year, 7, 1)
                    cronograma["Fim trimestre"] = datetime(datetime.today().year, 9, 30)
                else:
                    cronograma["Inicio trimestre"] = datetime(datetime.today().year, 10, 1)
                    cronograma["Fim trimestre"] = datetime(datetime.today().year, 12, 31)
                
                cronograma = cronograma.dropna(axis=1, how='all')
                nome_formatado = ' '.join([part.capitalize() for part in nome.split('.')])
                st.subheader(nome_formatado)
                colunas = cronograma.columns
                pontos = []
                yaxis = []
                axis = 0

                fig = go.Figure()
                if 'Projeto 1' in colunas:
                    funcionando = True
                    try:
                        cronograma["Fim Projeto 1"] = cronograma["Fim estimado do Projeto 1 (com atraso)"]
                    except:
                        try:
                            cronograma["Fim Projeto 1"] = cronograma["Fim previsto do Projeto 1 (sem atraso)"]
                        except:
                            st.error(f'Não foi possível determinar o fim do projeto {cronograma['Projeto 1'].iloc[0]}', icon="⚠")
                            funcionando = False
                    if funcionando == True:
                        pontos.append(cronograma['Projeto 1'])
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando o Projeto 1
                        fig.add_trace(go.Scatter(x=[cronograma["Início Real Projeto 1"].iloc[0], cronograma["Fim Projeto 1"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=cronograma['Projeto 1'].iloc[0],
                                                line=dict(color='#b4944c', width=4)))
                if 'Projeto 2' in colunas:
                    funcionando = True
                    try:
                        cronograma["Fim Projeto 2"] = cronograma["Fim estimado do Projeto 2 (com atraso)"]
                    except:
                        try:
                            cronograma["Fim Projeto 2"] = cronograma["Fim previsto do Projeto 2 (sem atraso)"]
                        except:
                            st.error(f'Não foi possível determinar o fim do projeto {cronograma['Projeto 2'].iloc[0]}', icon="⚠")
                            funcionando = False
                    if funcionando == True:
                        pontos.append(cronograma['Projeto 2'])
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando o Projeto 2
                        fig.add_trace(go.Scatter(x=[cronograma["Início Real Projeto 2"].iloc[0], cronograma["Fim Projeto 2"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=cronograma['Projeto 2'].iloc[0],
                                                line=dict(color='#9a845c', width=4)))
                if 'Projeto 3' in colunas:
                    funcionando = True
                    try:
                        cronograma["Fim Projeto 3"] = cronograma["Fim estimado do Projeto 3 (com atraso)"]
                    except:
                        try:
                            cronograma["Fim Projeto 3"] = cronograma["Fim previsto do Projeto 3 (sem atraso)"]
                        except:
                            st.error(f'Não foi possível determinar o fim do projeto {cronograma['Projeto 3'].iloc[0]}', icon="⚠")
                            funcionando = False
                    if funcionando == True:
                        pontos.append(cronograma['Projeto 3'])
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando o Projeto 3
                        fig.add_trace(go.Scatter(x=[cronograma["Início Real Projeto 3"].iloc[0], cronograma["Fim Projeto 3"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=cronograma['Projeto 3'].iloc[0],
                                                line=dict(color='#847c64', width=4)))
                if 'Projeto 4' in colunas:
                    funcionando = True
                    try:
                        cronograma["Fim Projeto 4"] = cronograma["Fim estimado do Projeto 4 (com atraso)"]
                    except:
                        try:
                            cronograma["Fim Projeto 4"] = cronograma["Fim previsto do Projeto 4 (sem atraso)"]
                        except:
                            st.error(f'Não foi possível determinar o fim do projeto {cronograma['Projeto 4'].iloc[0]}', icon="⚠")
                            funcionando = False
                    if funcionando == True:
                        pontos.append(cronograma['Projeto 4'])
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando o Projeto 3
                        fig.add_trace(go.Scatter(x=[cronograma["Início Real Projeto 4"].iloc[0], cronograma["Fim Projeto 4"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=cronograma['Projeto 4'].iloc[0],
                                                line=dict(color='#847c64', width=4)))
                if 'Projeto Interno 1' in colunas:
                    if "Fim do Projeto Interno 1" in colunas:
                        pontos.append(cronograma['Projeto Interno 1'])
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando o Projeto Interno 1
                        fig.add_trace(go.Scatter(x=[cronograma["Início do Projeto Interno 1"].iloc[0], cronograma["Fim do Projeto Interno 1"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=cronograma['Projeto Interno 1'].iloc[0],
                                                line=dict(color='#405094', width=4)))
                    else: st.error(f'Não foi possível determinar o fim do projeto interno {cronograma['Projeto Interno 1'].iloc[0]}', icon="⚠")
                if 'Projeto Interno 2' in colunas:
                    if "Fim do Projeto Interno 2" in colunas:
                        pontos.append(cronograma['Projeto Interno 2'])
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando o Projeto Interno 2
                        fig.add_trace(go.Scatter(x=[cronograma["Início do Projeto Interno 2"].iloc[0], cronograma["Fim do Projeto Interno 2"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=cronograma['Projeto Interno 2'].iloc[0],
                                                line=dict(color='#405094', width=4)))
                    else: st.error(f'Não foi possível determinar o fim do projeto interno {cronograma['Projeto Interno 2'].iloc[0]}', icon="⚠")

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
                if 'N° Assessorias' in colunas:
                    aprendizagens = cronograma['N° Assessorias'].iloc[0]
                    for quantidade in range(aprendizagens):
                        pontos.append(f'Assessoria {quantidade+1}')
                        axis +=1
                        yaxis.append(axis)
                        # Adicionando aprendizagens
                        fig.add_trace(go.Scatter(x=[cronograma["Inicio trimestre"].iloc[0], cronograma["Fim trimestre"].iloc[0]],
                                                y=[axis, axis],
                                                mode='lines',
                                                name=f'Assessoria {quantidade+1}',
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
                st.write('')
                st.write('')
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
                                        <p>"""f'{cronograma['Portfólio do Projeto 3'].iloc[0]}'""", """f'Satisfação com o projeto: {cronograma['Satisfação com o Projeto 3'].iloc[0]}'"""</p>
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
                                    <p>"""f'{cronograma['Portfólio do Projeto 2'].iloc[0]}'""", """f'Satisfação com o projeto: {cronograma["Satisfação com o Projeto 2"].iloc[0]}'"""</p>
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
                                <p>"""f'{cronograma['Portfólio do Projeto 1'].iloc[0]}'""", """f'Satisfação com o projeto: {cronograma['Satisfação com o Projeto 1'].iloc[0]}'"""</p>
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
        horas_disponiveis -= analista.get('N° Assessorias', 0) * 10

        # Subtrai horas conforme projetos internos ativos (cada um reduz 5h)
        for i in range(1, 5):  # Projetos Internos 1 a 4
            if pd.notnull(analista.get(f'Início do Projeto Interno {i}', None)):
                horas_disponiveis -= 5

        # Ajusta conforme cargo no núcleo
        cargo = str(analista.get('Cargo no núcleo', '')).strip().upper()
        if cargo in ['SDR', 'HUNTER', 'ANALISTA SÊNIOR']:
            horas_disponiveis -= 10

        # Ajusta conforme proximidade da data de fim de um projeto
        for i in range(1, 5):  # Projetos 1 a 4
            fim_estimado = analista.get(f'Fim estimado do Projeto {i} (com atraso)', None)
            fim_previsto = analista.get(f'Fim previsto do Projeto {i} (sem atraso)', None)

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
        satisfacao_col = f'Satisfação com o Portfólio: {escopo_selecionado}'
        
        # Tenta obter o valor da coluna específica do portfólio
        if satisfacao_col in analista and pd.notna(analista[satisfacao_col]):
            try:
                satisfacao_portfolio = float(analista[satisfacao_col])
            except:
                # Caso não consiga converter para float, usa valor neutro
                satisfacao_portfolio = 3
        else:
            # Se não encontrar satisfação específica, usa valor neutro
            satisfacao_portfolio = 3  # Valor neutro
        
        satisfacao_portfolio *= 2

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

    # Inicializa session_state para os campos de filtro
    if 'escopo_selecionado' not in st.session_state:
        st.session_state.escopo_selecionado = escopos[0]
    if 'analista_selecionado' not in st.session_state:
        st.session_state.analista_selecionado = "Todos"
    if 'inicio_projeto' not in st.session_state:
        st.session_state.inicio_projeto = datetime.today().date()
    if 'fim_projeto' not in st.session_state:
        st.session_state.fim_projeto = (datetime.today() + pd.Timedelta(days=56)).date()
    if 'afinidade_weight' not in st.session_state:
        st.session_state.afinidade_weight = 0.5
    if 'disponibilidade_weight' not in st.session_state:
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
            key="escopo_select"
        )
        st.session_state.escopo_selecionado = escopo
        
    with col_analista:
        analistas = sorted(pcp_df['Membro'].astype(str).unique().tolist(), key=str.lower)

        # Usando o multiselect
        analistas_selecionados = st.multiselect(
            "**Analista**",
            options= analistas,
            default=None,
            key="analista_select",
            placeholder='Selecione os analistas'
        )

        # Salva a seleção no session_state para persistência
        st.session_state.analista_selecionado = analistas_selecionados
    
    with col_data:
        inicio = st.date_input("**Data de Início do Projeto**",
                                min_value=datetime(datetime.today().year - 1, 1, 1).date(),
                                  max_value=datetime(datetime.today().year + 1, 12, 31).date(),
                                    value=datetime.today().date(), format="DD/MM/YYYY")
    inicio_novo_projeto = pd.Timestamp(inicio)
    
    pcp_df = converte_data(pcp_df, date_columns)

    # Filtra por analista se um for selecionado
        
    # if len(pcp_df) == 0:
    #     st.warning("Nenhum analista encontrado com os filtros selecionados.", icon="⚠️")
    #     st.stop()
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
    
    # Calcula Afinidade com base no escopo selecionado
    pcp_df['Afinidade'] = pcp_df.apply(lambda row: calcular_afinidade(row, escopo), axis=1)
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
            key="disponibilidade_weight_input"
        )
        disponibilidade_weight = round_to_nearest(disponibilidade_weight)
        # Se o valor de disponibilidade mudar, ajustar afinidade
        if disponibilidade_weight != st.session_state.disponibilidade_weight:
            st.session_state.disponibilidade_weight = disponibilidade_weight
            st.session_state.afinidade_weight = round(1 - st.session_state.disponibilidade_weight, 1)
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
            key="afinidade_weight_input"
        )
    afinidade_weight = round_to_nearest(afinidade_weight)
    # Se o valor de afinidade mudar, ajustar disponibilidade
    if afinidade_weight != st.session_state.afinidade_weight:
        st.session_state.afinidade_weight = afinidade_weight
        st.session_state.disponibilidade_weight = round(1 - st.session_state.afinidade_weight, 1)
        st.rerun()

    with col_fim:
        fim = st.date_input("**Data de Fim do Projeto**", min_value=inicio,
                             max_value=datetime(datetime.today().year + 1, 12, 31).date(),
                             value=inicio, format="DD/MM/YYYY")
    # Converte para timestamp para cálculos


    
    # Inputs para pesos com valores do state
    
    
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
    pcp_df['Nota Final'] = (pcp_df['Afinidade'] * afinidade_weight + pcp_df['Nota Disponibilidade'] * disponibilidade_weight)
    
    pcp_df = pcp_df.dropna(subset=['Membro'])
    dispo_media = pcp_df['Disponibilidade'].mean()
    afini_media = pcp_df['Afinidade'].mean()
    nota_media = pcp_df['Nota Final'].mean()
    if analistas_selecionados != []:
        pcp_df = pcp_df[pcp_df['Membro'].isin(analistas_selecionados)]
    # Cria um divisor
    st.markdown("---")
    
    # Exibe as colunas principais
    st.subheader("Membros sugeridos para o projeto")

        
    st.markdown("""
    <div style="margin-bottom: 20px">
    <p><strong>Entendendo as pontuações:</strong></p>
    <ul>
      <li><strong>Disponibilidade</strong>: Horas estimadas disponíveis para novas atividades (Máximo: 30h)</li>
      <li><strong>Afinidade</strong>: Pontuação (0-10) baseada em satisfação com portfólio, capacidade técnica e saúde mental</li>
      <li><strong>Nota Final</strong>: Média ponderada entre disponibilidade e afinidade</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Função para formatar o DataFrame para exibição
    def format_display_df(pcp_df):
        formatted_df = pcp_df[['Membro', 'Disponibilidade', 'Afinidade', 'Nota Final']].copy()
        formatted_df['Membro'] = formatted_df['Membro'].astype(str)
        formatted_df.loc[len(formatted_df)] = ['media.núcleo ⚠', dispo_media, afini_media, nota_media]
        formatted_df = formatted_df.sort_values(by='Nota Final', ascending=False)        # formatted_df['Disponibilidade'] = formatted_df['Disponibilidade'].apply(lambda x: f"{x:.1f}h")
        # formatted_df['Afinidade'] = formatted_df['Afinidade'].apply(lambda x: f"{x:.1f}/10")
        # formatted_df['Nota Final'] = formatted_df['Nota Final'].apply(lambda x: f"{x:.1f}/10")
        for index,row in formatted_df.iterrows():
            formatted_df.at[index, 'Membro'] = ' '.join([part.capitalize() for part in row['Membro'].split('.')])
        return formatted_df
    
    # Formata as colunas para melhor exibição
    display_df = format_display_df(pcp_df)
    # Exibe a tabela
    for index, row in display_df.iterrows():
        if row['Membro'] != 'Media Núcleo ⚠':
            prim_color = "064381"
            sec_color = "fbac04"
            back_color = "decda9"
        else:
            match st.session_state.nucleo:
                case 'NCiv':
                    prim_color = "805e01"
                    back_color = "e0d19b"
                case 'NCon':
                    prim_color = "054f20"
                    back_color = "91cfa7"
                case 'NDados':
                    prim_color = "461073"
                    back_color = "c19be0"
                case 'NI':
                    prim_color = "3d0202"
                    back_color = "c27a7a"
                case 'NTec':
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
            """, unsafe_allow_html=True
        )


##9bacbd
        st.write('')
