import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="Ambiente de Projetos", layout="wide")

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
        height: 2px;  /* Garantindo que a altura será 2px para hr sem atributo size */
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

# O título agora aparecerá sobre o 'div' sem ser coberto
if page == "Base Consolidada":
    st.title("Base Consolidada")
if page == "PCP":
    st.title("PCP")

# Carregando os dados
if 'pcp' not in st.session_state:
    with st.spinner('Carregando...'):
        st.session_state.pcp = pd.read_excel(r"Ambiente-Modelo\Include\PCP Auto.xlsx", sheet_name=None)
    
# Acesso aos dados armazenados
pcp = st.session_state.pcp

def nucleo_func(nucleo_digitado):
    nucleo_digitado = nucleo_digitado.replace(" ", "").lower()
    for pcp_sheet in pcp.keys():
        if nucleo_digitado == pcp_sheet.replace(" ", "").lower():
            pcp_nucleo = pcp[pcp_sheet]
            return pcp_nucleo
    return None
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
            df = nucleo_func(st.session_state.nucleo)
            df.replace('-', np.nan, inplace=True)
            cronograma = df
            df['Início previsto Projeto 1'] = (pd.to_datetime(df['Início previsto Projeto 1'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início previsto Projeto 2'] = (pd.to_datetime(df['Início previsto Projeto 2'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            # df['Início previsto Projeto 3'] = (pd.to_datetime(df['Início previsto Projeto 3'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início Real Projeto 1'] = (pd.to_datetime(df['Início Real Projeto 1'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Início Real Projeto 2'] = (pd.to_datetime(df['Início Real Projeto 2'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            # df['Início Real Projeto 3'] = (pd.to_datetime(df['Início Real Projeto 3'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim previsto do Projeto 1 (sem atraso)'] = (pd.to_datetime(df['Fim previsto do Projeto 1 (sem atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim previsto do Projeto 2 (sem atraso)'] = (pd.to_datetime(df['Fim previsto do Projeto 2 (sem atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            # df['Fim previsto do Projeto 3 (sem atraso)'] = (pd.to_datetime(df['Fim previsto Projeto 3 (sem atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim estimado do Projeto 1 (com atraso)'] = (pd.to_datetime(df['Fim estimado do Projeto 1 (com atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            df['Fim estimado do Projeto 2 (com atraso)'] = (pd.to_datetime(df['Fim estimado do Projeto 2 (com atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')
            # df['Fim estimado do Projeto 3 (com atraso)'] = (pd.to_datetime(df['Fim estimado do Projeto 3 (com atraso)'], format='%d/%m/%Y', errors='coerce')).dt.strftime('%d/%m/%Y')

            
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
                            if row['N° Aprendizagens'].iloc[0] != 0: alocacoes += row['N° Aprendizagens'].iloc[0]
                        except: pass
                        try:
                            if pd.notna(row['Assessoria/Liderança']): alocacoes += 1
                        except: pass
                        try:
                            if pd.notna(row['Equipe de PS']): alocacoes += 1
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

                # Plotando o gráfico
                fig = go.Figure()
                if 'Projeto 1' in colunas:
                    pontos.append(cronograma['Projeto 1'])
                    axis +=1
                    yaxis.append(axis)
                    try:
                        cronograma["Fim Projeto 1"] = cronograma["Fim estimado do Projeto 1 (com atraso)"]
                    except:
                        cronograma["Fim Projeto 1"] = cronograma["Fim previsto do Projeto 1 (sem atraso)"]

                    # Adicionando o Projeto 1
                    fig.add_trace(go.Scatter(x=[cronograma["Início Real Projeto 1"].iloc[0], cronograma["Fim Projeto 1"].iloc[0]],
                                            y=[axis, axis],
                                            mode='lines',
                                            name=cronograma['Projeto 1'].iloc[0],
                                            line=dict(color='#b4944c', width=4)))
                if 'Projeto 2' in colunas:
                    pontos.append(cronograma['Projeto 2'])
                    axis +=1
                    yaxis.append(axis)
                    try:
                        cronograma["Fim Projeto 2"] = cronograma["Fim estimado do Projeto 2 (com atraso)"]
                    except:
                        cronograma["Fim Projeto 2"] = cronograma["Fim previsto do Projeto 2 (sem atraso)"]
                    # Adicionando o Projeto 2
                    fig.add_trace(go.Scatter(x=[cronograma["Início Real Projeto 2"].iloc[0], cronograma["Fim Projeto 2"].iloc[0]],
                                            y=[axis, axis],
                                            mode='lines',
                                            name=cronograma['Projeto 2'].iloc[0],
                                            line=dict(color='#9a845c', width=4)))
                if 'Projeto 3' in colunas:
                    pontos.append(cronograma['Projeto 3'])
                    axis +=1
                    yaxis.append(axis)
                    try:
                        cronograma["Fim Projeto 3"] = cronograma["Fim estimado do Projeto 3 (com atraso)"]
                    except:
                        cronograma["Fim Projeto 3"] = cronograma["Fim previsto do Projeto 3 (sem atraso)"]
                    # Adicionando o Projeto 3
                    fig.add_trace(go.Scatter(x=[cronograma["Início Real Projeto 3"].iloc[0], cronograma["Fim Projeto 3"].iloc[0]],
                                            y=[axis, axis],
                                            mode='lines',
                                            name=cronograma['Projeto 3'].iloc[0],
                                            line=dict(color='#847c64', width=4)))
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

    colescopo, colinicio, colfim = st.columns(3)
    with colescopo:
        escopo = st.selectbox(
            "",
            placeholder="Portfolio",
            options=escopos,
            index=opcoes.index(st.session_state.escopo) if st.session_state.escopo else None  # Certifique-se que o índice inicial seja 0
        )
    with colinicio:
        inicio = st.date_input("*Início*", min_value=datetime(datetime.today().year - 1, 1, 1).date(), max_value=datetime(datetime.today().year + 1, 12, 31).date(), value=datetime.today().date(), format="DD/MM/YYYY")
    with colfim:
        fim = st.date_input("*Fim*", min_value=inicio, max_value=datetime(datetime.today().year + 1, 12, 31).date(), value=inicio, format="DD/MM/YYYY")





#mudanças: adição da seleção de escopo (separada por nucleo), embelezamento das datas, alteração de Alocações pra multiselect, adição da seleção de datas, separação das páginas