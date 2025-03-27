import pandas as pd
import numpy as np
import os
from datetime import datetime

def calculate_member_scores(df, inicio_novo_projeto):
    """
    Calculates availability and affinity scores for each member in the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame containing member data.
        inicio_novo_projeto (datetime): The start date of the new project.

    Returns:
        pd.DataFrame: The DataFrame with added 'Disponibilidade' and 'Afinidade' columns,
                      sorted by 'Disponibilidade' and 'Afinidade' in descending order.
    """

    # Lista de cargos a serem removidos
    cargos_excluidos = ['Líder de Outbound', 'Coordenador de Negócios', 'Coordenador de Inovação Comercial', 'Gerente Comercial',
                        'Coordenador de Projetos', 'Coordenador de Inovação de Projetos', 'Gerente de Projetos']

    # Filtrando a tabela para remover os cargos indesejados
    df = df[~df['Cargo no núcleo'].isin(cargos_excluidos)]

    # Função para calcular a Disponibilidade (em horas)
    def calcular_disponibilidade(row, inicio_novo_projeto):
        horas_disponiveis = 30  # Começamos com 30h disponíveis

        # Subtrai horas conforme aprendizados e assessorias
        horas_disponiveis -= row.get('N° Aprendizagens', 0) * 5
        horas_disponiveis -= row.get('N° Assessoria', 0) * 10

        # Subtrai horas conforme projetos ativos (cada projeto reduz 10h)
        for i in range(1, 5):  # Projetos 1 a 4
            if pd.notnull(row.get(f'Fim previsto do Projeto {i}', None)):
                horas_disponiveis -= 10

        # Subtrai horas conforme projetos internos ativos (cada um reduz 5h)
        for i in range(1, 5):  # Projetos Internos 1 a 4
            if pd.notnull(row.get(f'Início do Projeto Interno {i}', None)):
                horas_disponiveis -= 5

        # Ajusta conforme cargo no núcleo
        cargo = str(row.get('Cargo no núcleo', '')).strip().upper()
        if cargo in ['SDR', 'HUNTER']:
            horas_disponiveis -= 10
        elif cargo == 'ANALISTA SÊNIOR':
            horas_disponiveis -= 5

        # Ajusta conforme proximidade da data de fim de um projeto
        for i in range(1, 5):  # Projetos 1 a 4
            fim_estimado = row.get(f'Fim estimado do Projeto {i}', None)
            fim_previsto = row.get(f'Fim previsto do Projeto {i}', None)

            fim_projeto = fim_estimado if pd.notnull(fim_estimado) else fim_previsto

            if pd.notnull(fim_projeto):
                days_left = (fim_projeto - inicio_novo_projeto).days
                if 7 < days_left <= 14:
                    horas_disponiveis += 6
                elif days_left <= 7:
                    horas_disponiveis += 10

        return horas_disponiveis

    # Função para calcular a Afinidade (nota de 0 a 10)
    def calcular_afinidade(row):
        # Satisfação esperada = Satisfação Média com o Portfólio * 2
        satisfacao_portfolio = row.get('Satisfação Média com o Portfólio', 0) * 2

        # Capacidade esperada = Validação média do Projeto * 2
        capacidade = row.get('Validação média do Projeto', 0) * 2

        # Saúde mental = Média entre percepção da carga e saúde mental na PJ
        # NEUTRO É 5
        sentimento_carga = row.get('Como se sente em relação à carga', '').strip().upper()
        sentimento_map = {'SUBALOCADO': 10, 'ESTOU SATISFEITO': 5, 'SUPERALOCADO': 1}
        sentimento_nota = sentimento_map.get(sentimento_carga, 5)  # Se não estiver mapeado, assume 5
        saude_mental = row.get('Saúde mental na PJ', 5)

        saude_final = (sentimento_nota + saude_mental) / 2

        # Nota final de afinidade é a média dos três critérios
        afinidade = (satisfacao_portfolio + capacidade + saude_final) / 3
        return afinidade

    # Converte datas para datetime
    date_cols = [f'Fim previsto do Projeto {i}' for i in range(1, 5)] + \
                [f'Fim estimado do Projeto {i}' for i in range(1, 5)] + \
                [f'Fim do Projeto Interno {i}' for i in range(1, 5)]
    for col in date_cols:
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        except:
            pass

    # Calcula disponibilidade
    df['Disponibilidade'] = df.apply(lambda row: calcular_disponibilidade(row, inicio_novo_projeto), axis=1)

    # Calcula afinidade
    df['Afinidade'] = df.apply(calcular_afinidade, axis=1)

    # Ordena os membros pela Disponibilidade e Afinidade (ambas igualmente importantes)
    df = df.sort_values(by=['Disponibilidade', 'Afinidade'], ascending=[False, False])

    return df