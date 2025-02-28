import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Ambiente de Projetos", layout="wide")

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
        height: 3.75rem;
        background: #064381;
        outline: none;
        z-index: 999990;
        display: block;
    }

    </style>
    <div class="fullscreen-div">
    </div>
    """, 
    unsafe_allow_html=True
)

# O título agora aparecerá sobre o 'div' sem ser coberto
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

# Carregar o núcleo selecionado
with st.spinner('Carregando...'):
    if st.session_state.nucleo:
        df = nucleo_func(st.session_state.nucleo)
        df.replace('-', np.nan, inplace=True)

        
        # Filtros
        colnome, colcargo, colaloc = st.columns(3)
        with colnome:
            nome = st.text_input("", placeholder='Membro', value=st.session_state.nome if st.session_state.nome else None)
            st.session_state.nome = nome
        with colcargo:
            cargo = st.text_input("", placeholder='Cargo', value=st.session_state.cargo if st.session_state.cargo else None)
            st.session_state.cargo = cargo
        with colaloc:
            opcoes = ['', 'Desalocado', '1 Alocação', '2 Alocações', '3 Alocações', '4+ Alocações']
            aloc = st.selectbox(
                "",
                placeholder="Alocações",
                options=opcoes,
                index=opcoes.index(st.session_state.aloc) if st.session_state.aloc else None  # Certifique-se que o índice inicial seja 0
            )
            # Não alteramos diretamente o session_state.aloc aqui, pois o Streamlit gerencia isso automaticamente

        # Filtragem dos dados
        if nome:
            df = df[df['Membro'] == nome]
        if cargo:
            df = df[df['Cargo no núcleo'] == cargo]
        if aloc:
            selecionado = opcoes.index(aloc) - 1
            filtrados = []
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
                    if pd.notna(row['N° Aprendizagens']): alocacoes += 1
                except: pass
                try:
                    if pd.notna(row['Assessoria/Liderança']): alocacoes += 1
                except: pass
                try:
                    if pd.notna(row['Equipe de PS']): alocacoes += 1
                except: pass
                if alocacoes > 4: alocacoes = 4
                if alocacoes == selecionado: filtrados.append(row)
            df = pd.DataFrame(filtrados)

        if df.empty:
            st.write("Sem informações para os dados filtrados")
        else:
            st.write(df)  # Exibe o DataFrame filtrado
