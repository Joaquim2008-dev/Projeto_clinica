import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(layout='wide')


def formatar_valor_brasileiro(valor):
    """Formata valores no padrão brasileiro: 1.234.567,89"""
    return f"R${valor:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')


@st.cache_data
def carregar_dados():
    datas = pd.read_excel('convenio_detalhado_linha.xlsx')
    datas['Data'] = pd.to_datetime(datas['Data'])
    datas['Valor'] = [valor.replace(',', '.') for valor in datas['Valor']]
    datas['Valor'] = datas['Valor'].astype('float')
    datas['ano_mes'] = datas['Data'].dt.to_period('M').astype('datetime64[ns]')
    return datas


df = carregar_dados()

# Informações do dia de ontem:
data = df.tail(1)['Data'].reset_index(drop=True)
ontem = df[df['Data'].isin(data)].reset_index(drop=True)
numero_exames_ontem = ontem.shape[0]

# Informações dos últimos 7 dias:
ultimos_7_dias = df['Data'].drop_duplicates().reset_index(drop=True).tail(7)
ultimos_7 = df[df['Data'].isin(ultimos_7_dias)].reset_index(drop=True)

numero_exames_7 = ultimos_7.shape[0]
no_medio_7 = round(numero_exames_7/7, 1)


# Informações dos últimos 30 dias:
ultimos_30 = df[df['ano_mes'] == '2025-04-01'].reset_index(drop=True)

numero_exames_30 = ultimos_30.shape[0]

dias = ultimos_30['Data'].nunique()

no_medio_30 = f'{numero_exames_30/dias:.1f}'


# Página Streamlit:


with st.sidebar:
    st.title('REDE SANTA SAÚDE💊')
    st.subheader('Menu')
    selected = option_menu(
        menu_title=None,
        options=['Painel de acompanhamento recente',
                 'Painel de acompanhamento geral'],
        default_index=0,
        icons=['clipboard-data', 'clipboard-data'],
    )


if selected == 'Painel de acompanhamento recente':
    co1, co2, co3 = st.columns(3)
    with co1:
        st.metric('Nº de exames de ontem', numero_exames_ontem)
    with co2:
        st.metric('Nº de exames dos últimos 7 dias', numero_exames_7)
        st.metric('Nº médio de exames dos últimos 7 dias', no_medio_7)
    with co3:
        st.metric('Nº de exames dos últimos 30 dias', numero_exames_30)
        st.metric('Nº médio de exames dos últimos 30 dias', no_medio_30)

    st.subheader('Avaliação dos exames e convênio recentes:')
    option = st.radio(
        'Período de tempo',
        ['Ontem', 'Últimos 7 dias', 'Último mês']
    )

    if option == 'Ontem':
        lista_c = ['Todos']
        for valor in ontem['Convênio'].unique():
            lista_c.append(valor)

        convênio = st.selectbox(
            'Filtar por tipo de convênio',
            lista_c
        )

        if convênio == 'Todos':
            # Top 5 exames mais vendidos por quantidade
            mais_vendidos_qtde = ontem['Descrição'].value_counts()

            # Top 5 exames mais lucrativos por valor
            mais_vendidos_valor = ontem.groupby(
                'Descrição')['Valor'].sum().sort_values(ascending=False)

            # Métricas dos convênios em dataframe
            convenios_valor = ontem.groupby(
                'Convênio')['Valor'].sum().sort_values(ascending=False)
            convenios_qtde = ontem['Convênio'].value_counts()

            # Criar dataframe com convênios
            df_convenios = pd.DataFrame({
                'Convênio': convenios_valor.index,
                'Valor Total (R$)': convenios_valor.values,
                'Quantidade': [convenios_qtde[conv] for conv in convenios_valor.index]
            }).reset_index(drop=True)

            co1, co2, co3 = st.columns(3)
            with co1:
                st.write('🏆 Top 5 Exames Mais Vendidos (Quantidade)')
                st.dataframe(mais_vendidos_qtde.head(5),
                             use_container_width=True)
            with co2:
                st.write('💰 Top 5 Exames Mais Lucrativos (Valor)')
                st.dataframe(mais_vendidos_valor.head(5),
                             use_container_width=True)
            with co3:
                st.write('🏥 Todos os Convênios')
                st.dataframe(df_convenios, use_container_width=True)
        else:
            filtro_ontem = ontem[ontem['Convênio'] == convênio]

            # Top 5 exames mais vendidos por quantidade
            mais_vendidos_qtde = filtro_ontem['Descrição'].value_counts()

            # Top 5 exames mais lucrativos por valor
            mais_vendidos_valor = filtro_ontem.groupby(
                'Descrição')['Valor'].sum().sort_values(ascending=False)

            # Métricas do convênio específico
            valor_total = filtro_ontem['Valor'].sum()
            qtde_total = len(filtro_ontem)

            co1, co2, co3 = st.columns(3)
            with co1:
                st.write(
                    f'🏆 Top 5 Exames Mais Vendidos - {convênio} (Quantidade)')
                st.dataframe(mais_vendidos_qtde.head(5),
                             use_container_width=True)
            with co2:
                st.write(
                    f'💰 Top 5 Exames Mais Lucrativos - {convênio} (Valor)')
                st.dataframe(mais_vendidos_valor.head(5),
                             use_container_width=True)
            with co3:
                st.write('🏥 Métricas do Convênio')
                st.metric(
                    label=f"{convênio}",
                    value=f"R$ {valor_total:,.2f}",
                    delta=f"{qtde_total} exames"
                )
        co1, co2 = st.columns(2)

    # Início das faixas de valores:
        # Criar o dataframe mesclado com nomes de colunas corretos
        qtde_df = mais_vendidos_qtde.reset_index()
        qtde_df.columns = ['Descrição', 'Quantidade']

        valor_df = mais_vendidos_valor.reset_index()
        valor_df.columns = ['Descrição', 'Valor_Total']

        mesclado = pd.merge(qtde_df, valor_df, on='Descrição', how='outer')
        mesclado = mesclado.fillna(0)  # Preencher NaN com 0

        faixas = st.checkbox('filtre o painel por faixas de valores (ontem)')

        if faixas:
            with co1:
                # Verificar se há variação nos valores antes de criar o slider
                if mesclado['Quantidade'].min() == mesclado['Quantidade'].max():
                    st.write("⚠️ Todos os exames têm a mesma quantidade")
                else:
                    faixa_valor_qtde = st.slider(
                        'Escolha uma faixa de valor para quantidade (ontem)',
                        min_value=int(mesclado['Quantidade'].min()),
                        max_value=int(mesclado['Quantidade'].max()),
                        value=(int(mesclado['Quantidade'].min()),
                               int(mesclado['Quantidade'].max()))
                    )
                    valor1, valor2 = faixa_valor_qtde

                    filtro = (mesclado['Quantidade'] >= valor1) & (
                        mesclado['Quantidade'] <= valor2)

                # Verificar se há variação nos valores antes de criar o slider
                if mesclado['Valor_Total'].min() == mesclado['Valor_Total'].max():
                    st.write("⚠️ Todos os exames têm o mesmo valor")
                    st.dataframe(mesclado[['Descrição', 'Valor_Total']])
                else:
                    if convênio == 'LABORATORIO ASO':
                        st.write('⚠️Valores insuficientes para uma seleção')

                    else:
                        faixa_valor_valor = st.slider(
                            'Escolha uma faixa de valor monetário (ontem)',
                            min_value=float(mesclado['Valor_Total'].min()),
                            max_value=float(mesclado['Valor_Total'].max()),
                            value=(float(mesclado['Valor_Total'].min()), float(
                                mesclado['Valor_Total'].max()))
                        )
                        valor3, valor4 = faixa_valor_valor
                        filtro1 = (mesclado['Valor_Total'] >= valor3) & (
                            mesclado['Valor_Total'] <= valor4)
                        st.dataframe(mesclado[filtro][filtro1])
    # fim das faixas

    # Últimos 7 dias:

    if option == 'Últimos 7 dias':
        lista_c = ['Todos']
        for valor in ultimos_7['Convênio'].unique():
            lista_c.append(valor)

        convênio = st.selectbox(
            'Filtrar por tipo de convênio',
            lista_c
        )

        if convênio == 'Todos':
            # Top 5 exames mais vendidos por quantidade
            mais_vendidos_qtde_7 = ultimos_7['Descrição'].value_counts()

            # Top 5 exames mais lucrativos por valor
            mais_vendidos_valor_7 = ultimos_7.groupby(
                'Descrição')['Valor'].sum().sort_values(ascending=False)

            # Métricas dos convênios em dataframe
            convenios_valor = ultimos_7.groupby(
                'Convênio')['Valor'].sum().sort_values(ascending=False)
            convenios_qtde = ultimos_7['Convênio'].value_counts()

            # Criar dataframe com convênios
            df_convenios = pd.DataFrame({
                'Convênio': convenios_valor.index,
                'Valor Total (R$)': convenios_valor.values,
                'Quantidade': [convenios_qtde[conv] for conv in convenios_valor.index]
            }).reset_index(drop=True)

            co1, co2, co3 = st.columns(3)
            with co1:
                st.write('🏆 Top 5 Exames Mais Vendidos (Quantidade)')
                st.dataframe(mais_vendidos_qtde_7.head(),
                             use_container_width=True)
            with co2:
                st.write('💰 Top 5 Exames Mais Lucrativos (Valor)')
                st.dataframe(mais_vendidos_valor_7.head(),
                             use_container_width=True)
            with co3:
                st.write('🏥 Todos os Convênios')
                st.dataframe(df_convenios, use_container_width=True)
        else:
            filtro_7 = ultimos_7[ultimos_7['Convênio'] == convênio]

            # Top 5 exames mais vendidos por quantidade
            mais_vendidos_qtde_7 = filtro_7['Descrição'].value_counts()

            # Top 5 exames mais lucrativos por valor
            mais_vendidos_valor_7 = filtro_7.groupby(
                'Descrição')['Valor'].sum().sort_values(ascending=False)

            # Métricas do convênio específico
            valor_total = filtro_7['Valor'].sum()
            qtde_total = len(filtro_7)

            co1, co2, co3 = st.columns(3)
            with co1:
                st.write(
                    f'🏆 Top 5 Exames Mais Vendidos - {convênio} (Quantidade)')
                st.dataframe(mais_vendidos_qtde_7.head(5),
                             use_container_width=True)
            with co2:
                st.write(
                    f'💰 Top 5 Exames Mais Lucrativos - {convênio} (Valor)')
                st.dataframe(mais_vendidos_valor_7.head(5),
                             use_container_width=True)
            with co3:
                st.write('🏥 Métricas do Convênio')
                st.metric(
                    label=f"{convênio}",
                    value=f"R$ {valor_total:,.2f}",
                    delta=f"{qtde_total} exames"
                )

        # Início das faixas de valores para 7 dias:
        co1, co2 = st.columns(2)

        # Criar o dataframe mesclado com nomes de colunas corretos
        qtde_df_7 = mais_vendidos_qtde_7.reset_index()
        qtde_df_7.columns = ['Descrição', 'Quantidade']

        valor_df_7 = mais_vendidos_valor_7.reset_index()
        valor_df_7.columns = ['Descrição', 'Valor_Total']

        mesclado_7 = pd.merge(qtde_df_7, valor_df_7,
                              on='Descrição', how='outer')
        mesclado_7 = mesclado_7.fillna(0)  # Preencher NaN com 0

        faixas_7 = st.checkbox(
            'Filtre o painel por faixas de valores (7 dias)', key='faixas_7_dias')

        if faixas_7:
            with co1:
                # Verificar se há variação nos valores antes de criar o slider
                if mesclado_7['Quantidade'].min() == mesclado_7['Quantidade'].max():
                    st.write("⚠️ Todos os exames têm a mesma quantidade")
                else:
                    if convênio == 'LABORATORIO ASO':
                        st.write('⚠️Valores insuficientes para seleção')

                    else:
                        faixa_valor_qtde_7 = st.slider(
                            'Escolha uma faixa de valor para quantidade (7 dias)',
                            min_value=int(mesclado_7['Quantidade'].min()),
                            max_value=int(mesclado_7['Quantidade'].max()),
                            value=(int(mesclado_7['Quantidade'].min()),
                                   int(mesclado_7['Quantidade'].max())),
                            key='slider_qtde_7_dias'
                        )
                        valor1_7, valor2_7 = faixa_valor_qtde_7

                        filtro_7_qtde = (mesclado_7['Quantidade'] >= valor1_7) & (
                            mesclado_7['Quantidade'] <= valor2_7)

                # Verificar se há variação nos valores antes de criar o slider
                if mesclado_7['Valor_Total'].min() == mesclado_7['Valor_Total'].max():
                    st.write("⚠️ Todos os exames têm o mesmo valor")
                    st.dataframe(mesclado_7[['Descrição', 'Valor_Total']])
                else:
                    if convênio == 'LABORATORIO ASO':
                        st.write('⚠️Valores insuficientes para uma seleção')

                    else:
                        faixa_valor_valor_7 = st.slider(
                            'Escolha uma faixa de valor monetário (7 dias)',
                            min_value=float(mesclado_7['Valor_Total'].min()),
                            max_value=float(mesclado_7['Valor_Total'].max()),
                            value=(float(mesclado_7['Valor_Total'].min()), float(
                                mesclado_7['Valor_Total'].max())),
                            key='slider_valor_7_dias'
                        )
                        valor3_7, valor4_7 = faixa_valor_valor_7
                        filtro1_7 = (mesclado_7['Valor_Total'] >= valor3_7) & (
                            mesclado_7['Valor_Total'] <= valor4_7)

                        # Aplicar ambos os filtros se ambos os sliders foram criados
                        if 'filtro_7_qtde' in locals():
                            st.dataframe(mesclado_7[filtro_7_qtde & filtro1_7])
                        else:
                            st.dataframe(mesclado_7[filtro1_7])
        # Fim das faixas para 7 dias

    # Últimos 30 dias:

    if option == 'Último mês':
        lista_c = ['Todos']
        for valor in ultimos_30['Convênio'].unique():
            lista_c.append(valor)

        convênio = st.selectbox(
            'Filtrar por tipo de convênio',
            lista_c
        )

        if convênio == 'Todos':
            # Top 5 exames mais vendidos por quantidade
            mais_vendidos_qtde_30 = ultimos_30['Descrição'].value_counts()

            # Top 5 exames mais lucrativos por valor
            mais_vendidos_valor_30 = ultimos_30.groupby(
                'Descrição')['Valor'].sum().sort_values(ascending=False)

            # Métricas dos convênios em dataframe
            convenios_valor = ultimos_30.groupby(
                'Convênio')['Valor'].sum().sort_values(ascending=False)
            convenios_qtde = ultimos_30['Convênio'].value_counts()

            # Criar dataframe com convênios
            df_convenios = pd.DataFrame({
                'Convênio': convenios_valor.index,
                'Valor Total (R$)': convenios_valor.values,
                'Quantidade': [convenios_qtde[conv] for conv in convenios_valor.index]
            }).reset_index(drop=True)

            co1, co2, co3 = st.columns(3)
            with co1:
                st.write('🏆 Top 5 Exames Mais Vendidos (Quantidade)')
                st.dataframe(mais_vendidos_qtde_30.head(5),
                             use_container_width=True)
            with co2:
                st.write('💰 Top 5 Exames Mais Lucrativos (Valor)')
                st.dataframe(mais_vendidos_valor_30.head(5),
                             use_container_width=True)
            with co3:
                st.write('🏥 Todos os Convênios')
                st.dataframe(df_convenios, use_container_width=True)
        else:
            filtro_30 = ultimos_30[ultimos_30['Convênio'] == convênio]

            # Top 5 exames mais vendidos por quantidade
            mais_vendidos_qtde_30 = filtro_30['Descrição'].value_counts()

            # Top 5 exames mais lucrativos por valor
            mais_vendidos_valor_30 = filtro_30.groupby(
                'Descrição')['Valor'].sum().sort_values(ascending=False)

            # Métricas do convênio específico
            valor_total = filtro_30['Valor'].sum()
            qtde_total = len(filtro_30)

            co1, co2, co3 = st.columns(3)
            with co1:
                st.write(
                    f'🏆 Top 5 Exames Mais Vendidos - {convênio} (Quantidade)')
                st.dataframe(mais_vendidos_qtde_30.head(5),
                             use_container_width=True)
            with co2:
                st.write(
                    f'💰 Top 5 Exames Mais Lucrativos - {convênio} (Valor)')
                st.dataframe(mais_vendidos_valor_30.head(5),
                             use_container_width=True)
            with co3:
                st.write('🏥 Métricas do Convênio')
                st.metric(
                    label=f"{convênio}",
                    value=f"R$ {valor_total:,.2f}",
                    delta=f"{qtde_total} exames"
                )

        # Início das faixas de valores para 30 dias:
        co1, co2 = st.columns(2)

        # Criar o dataframe mesclado com nomes de colunas corretos
        qtde_df_30 = mais_vendidos_qtde_30.reset_index()
        qtde_df_30.columns = ['Descrição', 'Quantidade']

        valor_df_30 = mais_vendidos_valor_30.reset_index()
        valor_df_30.columns = ['Descrição', 'Valor_Total']

        mesclado_30 = pd.merge(qtde_df_30, valor_df_30,
                               on='Descrição', how='outer')
        mesclado_30 = mesclado_30.fillna(0)  # Preencher NaN com 0

        faixas_30 = st.checkbox(
            'Filtre o painel por faixas de valores (30 dias)', key='faixas_30_dias')

        if faixas_30:
            with co1:
                # Verificar se há variação nos valores antes de criar o slider
                if mesclado_30['Quantidade'].min() == mesclado_30['Quantidade'].max():
                    st.write("⚠️ Todos os exames têm a mesma quantidade")
                else:
                    if convênio == 'LABORATORIO ASO':
                        st.write('⚠️Valores insuficientes para seleção')
                    else:
                        faixa_valor_qtde_30 = st.slider(
                            'Escolha uma faixa de valor para quantidade (30 dias)',
                            min_value=int(mesclado_30['Quantidade'].min()),
                            max_value=int(mesclado_30['Quantidade'].max()),
                            value=(int(mesclado_30['Quantidade'].min()),
                                   int(mesclado_30['Quantidade'].max())),
                            key='slider_qtde_30_dias'
                        )
                        valor1_30, valor2_30 = faixa_valor_qtde_30

                        filtro_30_qtde = (mesclado_30['Quantidade'] >= valor1_30) & (
                            mesclado_30['Quantidade'] <= valor2_30)

                # Verificar se há variação nos valores antes de criar o slider
                if mesclado_30['Valor_Total'].min() == mesclado_30['Valor_Total'].max():
                    st.write("⚠️ Todos os exames têm o mesmo valor")
                    st.dataframe(mesclado_30[['Descrição', 'Valor_Total']])
                else:
                    if convênio == 'LABORATORIO ASO':
                        st.write('⚠️Valores insuficientes para uma seleção')
                    else:
                        faixa_valor_valor_30 = st.slider(
                            'Escolha uma faixa de valor monetário (30 dias)',
                            min_value=float(mesclado_30['Valor_Total'].min()),
                            max_value=float(mesclado_30['Valor_Total'].max()),
                            value=(float(mesclado_30['Valor_Total'].min()), float(
                                mesclado_30['Valor_Total'].max())),
                            key='slider_valor_30_dias'
                        )
                        valor3_30, valor4_30 = faixa_valor_valor_30
                        filtro1_30 = (mesclado_30['Valor_Total'] >= valor3_30) & (
                            mesclado_30['Valor_Total'] <= valor4_30)

                        # Aplicar ambos os filtros se ambos os sliders foram criados
                        if 'filtro_30_qtde' in locals():
                            st.dataframe(
                                mesclado_30[filtro_30_qtde & filtro1_30])
                        else:
                            st.dataframe(mesclado_30[filtro1_30])

if selected == 'Painel de acompanhamento geral':

    new = option_menu(
        menu_title=None,
        options=['Análise por tipo de exame',
                 'Análise temporal',
                 'Análise por Convênio'],
        orientation='horizontal',
        icons=['bar-chart', 'graph-up', 'star'],
        styles={
            'container': {
                'padding': '30px',
                'background-color': 'black',
            },

            'icon': {
                'color': 'blue',
                'font-size': '20px'
            },

            'nav-link': {
                'color': 'white',
            },

            'nav-link-selected': {
                'background-color': 'red',
                'font-weight': "bold"
            }
        }
    )

    if new == 'Análise por tipo de exame':
        st.subheader('Tícket médio por tipo de exame (maior ao menor)')

        ticket = df.groupby('Descrição').agg(
            quantidade_vendida=('Descrição', 'size'),
            Valor=('Valor', 'sum'),
            ticket_medio=('Valor', 'mean')
        ).sort_values(by='ticket_medio', ascending=False)

        # Converter valores monetários para formato brasileiro
        ticket['Valor'] = ticket['Valor'].apply(formatar_valor_brasileiro)
        ticket['ticket_medio'] = ticket['ticket_medio'].apply(
            lambda x: f"R$ {x:.2f}".replace('.', ','))

        st.dataframe(ticket)
        st.divider()
        st.subheader(
            'Top 10 exames mais frequentes e com maior valor em vendas')
        mais_valiosos = df.groupby('Descrição')['Valor'].sum(
        ).reset_index().sort_values(by='Valor', ascending=False)
        mais_frequentes = df['Descrição'].value_counts().reset_index()

        # Aplicar formatação brasileira
        mais_valiosos_formatado = mais_valiosos.head(10).copy()
        mais_valiosos_formatado['Valor_Formatado'] = mais_valiosos_formatado['Valor'].apply(
            formatar_valor_brasileiro)

        fig = px.bar(mais_valiosos_formatado, x='Valor',
                     y='Descrição', text='Valor_Formatado')

        fig.update_traces(
            textposition='inside',
            textfont=dict(size=12, color='white')
        )
        fig.update_layout(xaxis_title='Valor (R$)')
        st.plotly_chart(fig)

        fig = px.bar(mais_frequentes.head(10), x='count',
                     y='Descrição', text='count')
        fig.update_traces(
            textposition='inside',
            texttemplate='%{text}',
            textfont=dict(size=12, color='white')
        )
        fig.update_layout(xaxis_title='Quantidade')
        st.plotly_chart(fig)

    if new == 'Análise temporal':

        st.subheader('Número médio de exames por mês durante o período')
        exames_por_mes = df['ano_mes'].value_counts()
        # Calcula a média de exames por mês (total de exames dividido pelo número de meses únicos)
        media_exames_mes = exames_por_mes.mean()

        df['data_completa'] = df['Data'].dt.date
        media_diaria_por_mes = df.groupby(
            ['ano_mes', 'data_completa']).size().groupby('ano_mes').mean().reset_index()
        media_diaria_por_mes.columns = ['ano_mes', 'Média Diária']

        fig = px.bar(media_diaria_por_mes, x='ano_mes',
                     y='Média Diária', text='Média Diária')

        fig.update_traces(
            textposition='outside',
            texttemplate='%{text:.1f}',
            textfont=dict(size=12, color='white')
        )
        fig.update_layout(
            xaxis_title='Período',
            yaxis_title='Média de Exames por Dia'
        )
        st.plotly_chart(fig)

        st.subheader(
            'Visualização da evolução mensal dos exames por valor e número de exames')
        lista_c = ['Todos']
        for valor in df['Convênio'].unique():
            lista_c.append(valor)

        with st.expander('Filtrar por exames'):
            lista_e = st.multiselect(
                'Filtre por exames',
                df['Descrição'].unique()
            )

        convênio = st.selectbox(
            'Filtrar por convênio',
            lista_c
        )
        chek_qtde = st.checkbox('Visualizar por número de exames')

        if chek_qtde:
            if convênio == 'Todos':
                if lista_e == []:
                    visualização = df.groupby(
                        'ano_mes').size().reset_index(name='Quantidade')

                    fig = px.bar(visualização, x='ano_mes', y='Quantidade',
                                 text='Quantidade')
                    fig.update_traces(
                        textposition='outside',
                        texttemplate='%{text}',
                        textfont=dict(size=12, color='white')
                    )
                    fig.update_layout(yaxis_title='Quantidade')
                    st.plotly_chart(fig)

                else:
                    data = df[df['Descrição'].isin(lista_e)]
                    visualização = data.groupby(
                        ['ano_mes', 'Descrição']).size().reset_index(name='Quantidade')

                    fig = px.bar(visualização, x='ano_mes', y='Quantidade',
                                 text='Quantidade', color='Descrição')
                    fig.update_traces(
                        textposition='outside',
                        texttemplate='%{text}',
                        textfont=dict(size=12, color='white'))

                    fig.update_layout(yaxis_title='Quantidade')
                    st.plotly_chart(fig)
            else:
                if lista_e == []:
                    filtro_conv = df[df['Convênio'] == convênio]
                    visualização = filtro_conv.groupby(
                        'ano_mes').size().reset_index(name='Quantidade')
                    fig = px.bar(visualização, x='ano_mes',
                                 y='Quantidade', text='Quantidade')
                    fig.update_traces(
                        textposition='outside',
                        texttemplate='%{text}',
                        textfont=dict(size=12, color='white'))

                    fig.update_layout(yaxis_title='Quantidade')

                    st.plotly_chart(fig)
                else:
                    filtro_conv = df[df['Convênio'] == convênio]
                    data = filtro_conv[filtro_conv['Descrição'].isin(lista_e)]
                    data = filtro_conv[filtro_conv['Descrição'].isin(lista_e)]
                    visualização = data.groupby(
                        ['ano_mes', 'Descrição']).size().reset_index(name='Quantidade')
                    fig = px.bar(visualização, x='ano_mes', y='Quantidade',
                                 text='Quantidade', color='Descrição')
                    fig.update_traces(
                        textposition='outside',
                        texttemplate='%{text}',
                        textfont=dict(size=12, color='white')
                    )
                    fig.update_layout(yaxis_title='Quantidade')
                    st.plotly_chart(fig)

        if not chek_qtde:
            if convênio == 'Todos':
                if lista_e == []:
                    visualização = df.groupby(
                        'ano_mes')['Valor'].sum().reset_index()
                    visualização['Valor_Formatado'] = visualização['Valor'].apply(
                        formatar_valor_brasileiro)
                    fig = px.bar(visualização, x='ano_mes',
                                 y='Valor', text='Valor_Formatado')
                    fig.update_traces(
                        textposition='outside',
                        textfont=dict(size=12, color='white')
                    )
                    fig.update_layout(yaxis_title='Valor (R$)')
                    st.plotly_chart(fig)
                else:
                    data = df[df['Descrição'].isin(lista_e)]
                    visualização = data.groupby(['ano_mes', 'Descrição'])[
                        'Valor'].sum().reset_index()
                    visualização['Valor_Formatado'] = visualização['Valor'].apply(
                        formatar_valor_brasileiro)
                    fig = px.bar(visualização, x='ano_mes', y='Valor',
                                 text='Valor_Formatado', color='Descrição')
                    fig.update_traces(
                        textposition='outside',
                        textfont=dict(size=12, color='white')
                    )
                    fig.update_layout(yaxis_title='Valor (R$)')
                    st.plotly_chart(fig)
            else:
                if lista_e == []:
                    filtro_conv = df[df['Convênio'] == convênio]
                    visualização = filtro_conv.groupby(
                        'ano_mes')['Valor'].sum().reset_index()
                    visualização['Valor_Formatado'] = visualização['Valor'].apply(
                        formatar_valor_brasileiro)
                    fig = px.bar(visualização, x='ano_mes',
                                 y='Valor', text='Valor_Formatado')
                    fig.update_traces(
                        textposition='outside',
                        textfont=dict(size=12, color='white')
                    )
                    fig.update_layout(yaxis_title='Valor (R$)')
                    st.plotly_chart(fig)
                else:
                    filtro_conv = df[df['Convênio'] == convênio]
                    data = filtro_conv[filtro_conv['Descrição'].isin(lista_e)]
                    visualização = data.groupby(['ano_mes', 'Descrição'])[
                        'Valor'].sum().reset_index()
                    visualização['Valor_Formatado'] = visualização['Valor'].apply(
                        formatar_valor_brasileiro)
                    fig = px.bar(visualização, x='ano_mes', y='Valor',
                                 text='Valor_Formatado', color='Descrição')
                    fig.update_traces(
                        textposition='outside',
                        textfont=dict(size=12, color='white')
                    )
                    fig.update_layout(yaxis_title='Valor (R$)')
                    st.plotly_chart(fig)

    if new == 'Análise por Convênio':
        st.subheader('Ticket médio por tipo de convênio')
        ticket_conv = df.groupby('Convênio').agg(
            Quantidade=('Convênio', 'size'),
            Valor=('Valor', 'sum'),
            Ticket_médio=('Valor', 'mean')
        ).sort_values(by='Ticket_médio', ascending=False)

        # Converter valores monetários para formato brasileiro
        ticket_conv['Valor'] = ticket_conv['Valor'].apply(
            formatar_valor_brasileiro)
        ticket_conv['Ticket_médio'] = ticket_conv['Ticket_médio'].apply(
            lambda x: f"R$ {x:.2f}".replace('.', ','))

        st.dataframe(ticket_conv)

        st.divider()
        st.subheader('Proporção do valor dos exames por tipo de convênio')
        proporção_convenios = df.groupby(
            ['ano_mes', 'Convênio'])['Valor'].sum()
        total = df.groupby('ano_mes')['Valor'].sum()
        proporção = (proporção_convenios/total)*100

        fig = px.bar(proporção.reset_index(), x='ano_mes',
                     y='Valor', color='Convênio', text='Valor')
        fig.update_traces(
            textposition='inside',
            textfont=dict(size=10, color='white', family='Arial'),
            texttemplate='%{text:.1f}%',
            textangle=0
        )
        fig.update_layout(
            xaxis_title='Período',
            yaxis_title='Porcentagem (%)',
            showlegend=True
        )
        st.plotly_chart(fig)

        st.subheader('Proporção do número dos exames por tipo de Convênio')
        proporção_convenios = df.groupby(
            ['ano_mes'])['Convênio'].value_counts()
        total = df['ano_mes'].value_counts().sort_index(ascending=True)
        proporção = (proporção_convenios/total)*100

        fig = px.bar(proporção.reset_index(), x='ano_mes',
                     y='count', color='Convênio', text='count')
        fig.update_traces(
            textposition='inside',
            textfont=dict(size=10, color='white', family='Arial'),
            texttemplate='%{text:.1f}%',
            textangle=0
        )
        fig.update_layout(
            xaxis_title='Período',
            yaxis_title='Porcentagem (%)',
            showlegend=True
        )
        st.plotly_chart(fig)
