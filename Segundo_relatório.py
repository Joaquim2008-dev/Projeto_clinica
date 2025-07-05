import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import numpy as np


def carregar_dados():
    df = pd.read_excel('paciente_por_data.xlsx')
    df['Valor R$'] = [f'{v}'.replace(',', '.').replace(
        '.', '').replace('R$\xa0', '') for v in df['Valor R$']]
    df['Valor R$'] = df['Valor R$'].astype('float')/100

    df['Valor Final'] = [f'{v}'.replace(',', '.').replace(
        '.', '').replace('R$\xa0', '') for v in df['Valor Final']]
    df['Valor Final'] = df['Valor Final'].astype('float')/100

    df['Data Nasc.'] = pd.to_datetime(df['Data Nasc.'], errors='coerce')
    df['Data Cad.'] = pd.to_datetime(df['Data Cad.'], errors='coerce')

    df['Idade'] = (
        ((df['Data Cad.'] - df['Data Nasc.'])/365).dt.days).round().astype('Int64')

    return df


st.set_page_config(layout='wide')
dados = carregar_dados()

dados['ano_mes'] = dados['Data Cad.'].dt.to_period(
    'M').astype('datetime64[ns]')

bins = [0, 17, 25, 35, 45, 60, 100]  # limites das faixas
labels = ['0-17', '18-25', '26-35', '36-45', '46-60', '60+']
dados['Faixa_etária'] = pd.cut(
    x=dados['Idade'],
    labels=labels,
    bins=bins
)


dados.drop(3956, axis='index', inplace=True)

contagem = dados['Sexo'].value_counts()
porcento = (dados['Sexo'].value_counts(normalize=True)*100)

with st.sidebar:
    st.title('REDE SANTA SAÚDE💊')
    selected = option_menu(
        menu_title='Menu',
        options=['Visão geral', 'Exames', 'Convênios', 'Análise por sexo',
                 'Análise por faixa de idade']
    )

if selected == 'Visão geral':
    st.subheader('Análise por Sexo')
    co1, co2 = st.columns(2)
    with co1:
        st.metric('Quantidade de mulheres', contagem[0])
        st.metric('Quantidade de homens', contagem[1])

    with co2:
        st.metric('Porcentagem de mulheres', f'{porcento[0]:.1f}%')
        st.metric('Porcentagem de homens', f'{porcento[1]:.1f}%')

    st.subheader('Análise por Faixa Etária')
    contagem_faixa = dados['Faixa_etária'].value_counts()
    porcentagem_faixa = dados['Faixa_etária'].value_counts(normalize=True)*100

    # Criar colunas para exibir as métricas de faixa etária
    cols = st.columns(3)  # 3 colunas para melhor distribuição

    for i, faixa in enumerate(contagem_faixa.index):
        with cols[i % 3]:
            st.metric(
                f'Faixa {faixa} anos',
                f'{contagem_faixa[faixa]}',
                f'{porcentagem_faixa[faixa]:.1f}%'
            )

    st.subheader('Ticket médio (R$) por mês📊')
    conta_simples = dados.groupby(['ano_mes'])['Valor Final'].mean()
    fig = px.bar(conta_simples, x=conta_simples.index,
                 y=conta_simples.values, text=conta_simples.values)

    fig.update_layout(
        yaxis_title='',
        xaxis_title='Período',
        yaxis=dict(showticklabels=False)  # Remove os valores do eixo Y

    )

    fig.update_traces(
        texttemplate='%{text:.1f}'
    )
    st.plotly_chart(fig)

if selected == 'Exames':
    st.subheader('10 exames mais frequentes no conjunto de dados')
    lista_exames = []
    for lista in dados['Exames']:
        for valor in lista.split(','):
            lista_exames.append(valor.strip())

    lista_exames = pd.Series(lista_exames)
    exames_gerais = pd.DataFrame({
        'Exame': lista_exames.value_counts().index[:10],
        'Quantidade': lista_exames.value_counts().values[:10]
    }).set_index('Exame')
    st.dataframe(exames_gerais)
    st.divider()

    st.subheader('Exames mais frequentes para cada sexo')
    df_exames = dados.copy()
    df_exames['Exames_Lista'] = df_exames['Exames'].str.split(',')
    df_exames = df_exames.explode('Exames_Lista')
    df_exames['Exames_Lista'] = df_exames['Exames_Lista'].str.strip()

    f = df_exames.query('Sexo == "F"')
    m = df_exames.query('Sexo == "M"')

    co1, co2 = st.columns(2)
    with co1:
        st.write("**Feminino**")
        feminino = f.groupby(['Exames_Lista']).size(
        ).sort_values(ascending=False).head(10)
        tabela_feminino = pd.DataFrame({
            'Exame': feminino.index,
            'Quantidade': feminino.values
        }).set_index('Exame')
        st.dataframe(tabela_feminino)

    with co2:
        st.write("**Masculino**")
        masculino = m.groupby(['Exames_Lista']).size(
        ).sort_values(ascending=False).head(10)
        tabela_masculino = pd.DataFrame({
            'Exame': masculino.index,
            'Quantidade': masculino.values
        }).set_index('Exame')
        st.dataframe(tabela_masculino)

    st.divider()
    st.subheader('5 exames mais frequentes por faixa etária')

    # Lista das faixas etárias
    faixas_etarias = ['0-17', '18-25', '26-35', '36-45', '46-60', '60+']

    # Criar colunas para exibir as tabelas lado a lado
    cols = st.columns(3)  # 3 colunas para melhor visualização

    for i, faixa in enumerate(faixas_etarias):
        # Filtrar dados por faixa etária
        dados_faixa = df_exames.query(f'Faixa_etária == "{faixa}"')

        # Agrupar e contar os exames mais frequentes
        exames_frequentes = dados_faixa.groupby(
            'Exames_Lista').size().sort_values(ascending=False).head(5)

        # Criar DataFrame com nomes de colunas apropriados
        tabela_faixa = pd.DataFrame({
            'Exame': exames_frequentes.index,
            'Quantidade': exames_frequentes.values
        }).set_index('Exame')

        # Exibir em colunas
        with cols[i % 3]:
            st.write(f"**Faixa {faixa} anos**")
            st.dataframe(tabela_faixa)

if selected == 'Convênios':
    st.subheader('Ticket Médio por mês por convênio')
    conta_complexa = dados.groupby(['ano_mes', 'Convênio'])[
        'Valor Final'].mean().reset_index()
    fig = px.bar(conta_complexa, x='ano_mes',
                 y='Valor Final', text='Valor Final', color='Convênio')

    fig.update_layout(
        yaxis_title='',
        xaxis_title='Período',
        yaxis=dict(showticklabels=False)  # Remove os valores do eixo Y

    )

    fig.update_traces(
        texttemplate='%{text:.1f}'
    )
    st.plotly_chart(fig)

    st.divider()

    st.subheader('Proporção dos convênios no valor total por mês')

    valor_conv = dados.groupby(['ano_mes', 'Convênio'])[
        'Valor Final'].sum().reset_index().set_index('ano_mes')
    valor_mensal = dados.groupby(
        'ano_mes')['Valor Final'].sum().reset_index().set_index('ano_mes')

    valor_conv['Porcentagem'] = (valor_conv['Valor Final'].div(
        valor_mensal['Valor Final'], axis=0)*100)
    valor_conv['Porcentagem'] = [
        f'{v:.1f}%' for v in valor_conv['Porcentagem']]

    fig = px.bar(valor_conv, x=valor_conv.index,
                 y='Porcentagem', color='Convênio', text_auto=True)
    st.plotly_chart(fig)

if selected == 'Análise por sexo':

    ticket_medio = dados.groupby('Sexo').agg(
        ticket_medio=('Valor Final', 'mean')
    )
    co1, co2 = st.columns(2)
    with co1:
        st.metric('Ticket médio das mulheres',
                  f'R${ticket_medio["ticket_medio"][0]:.1f}')

    with co2:
        st.metric('Ticket médio dos homens',
                  f'R${ticket_medio["ticket_medio"][1]:.1f}')

    st.subheader('Ticket médio (R$) por convênio por sexo📊')
    ticket_medio_conv = pd.crosstab(
        index=dados['Convênio'], columns=dados['Sexo'], values=dados['Valor Final'], aggfunc='mean').fillna(0).sort_values(by='F', ascending=False).reset_index()

    fig = px.bar(ticket_medio_conv, x='Convênio',
                 y=['F', 'M'], text_auto='.2f')

    fig.update_layout(
        yaxis_title='',
        xaxis_title='Período',
        yaxis=dict(showticklabels=False)  # Remove os valores do eixo Y

    )

    st.plotly_chart(fig)

    st.divider()
    st.subheader('Evolução mensal do valor total por sexo')

    sexo_valor = dados.groupby(['ano_mes', 'Sexo'])[
        'Valor Final'].sum().reset_index()

    fig = px.line(sexo_valor, x='ano_mes', y='Valor Final', color='Sexo')
    st.plotly_chart(fig)

if selected == 'Análise por faixa de idade':

    st.subheader('Ticket médio (R$) por faixa etária📊')
    ticket_medio_idade = dados.groupby('Faixa_etária').agg(
        ticket_medio=('Valor Final', 'mean')
    ).reset_index()

    fig = px.bar(ticket_medio_idade, x='Faixa_etária',
                 y='ticket_medio', text='ticket_medio')

    fig.update_layout(
        yaxis_title='',
        xaxis_title='Período',
        yaxis=dict(showticklabels=False)  # Remove os valores do eixo Y

    )
    fig.update_traces(
        texttemplate='%{text:.2f}'
    )

    st.plotly_chart(fig)

    st.subheader('Ticket médio (R$) por convênio por faixa etária📊')
    ticket_medio_conv_idade = pd.crosstab(
        index=dados['Convênio'], columns=dados['Faixa_etária'], values=dados['Valor Final'], aggfunc='mean').fillna(0)

    fig = px.bar(ticket_medio_conv_idade, x=ticket_medio_conv_idade.index,
                 y=ticket_medio_conv_idade.columns, text_auto='.2f')

    fig.update_layout(
        yaxis_title='',
        xaxis_title='Período',
        yaxis=dict(showticklabels=False)
    )

    st.plotly_chart(fig)

    st.subheader('Análise da faixa etária por sexo📊')
    faixa_por_sexo = pd.crosstab(
        index=dados['Faixa_etária'], columns=dados['Sexo']
    )
    fig = px.bar(faixa_por_sexo, x=faixa_por_sexo.index,
                 y=faixa_por_sexo.columns, text_auto=True)
    fig.update_layout(
        yaxis_title='',
        xaxis_title='Período',
        yaxis=dict(showticklabels=False)
    )
    st.plotly_chart(fig)

    st.divider()

    st.subheader('Evolução mensal do valor total por faixa etária')
    grupo_faixa = dados.groupby(['ano_mes', 'Faixa_etária'])[
        'Valor Final'].sum().reset_index()

    line = px.line(grupo_faixa, x='ano_mes',
                   y='Valor Final', color='Faixa_etária')
    st.plotly_chart(line)
