import os
import streamlit as st  
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils import components as c

############################## Configurações da página (inicio) ##############################
c.pag_config(os.path.basename(__file__))
c.sobre_dash()
############################## Configurações da página (fim) ##############################

# Carregar os dados
cbio_data = pd.read_csv("data/processed/cbio_data.csv",sep=";",decimal=",",index_col=0)
cbio_data.index = pd.to_datetime(cbio_data.index)

st.title("CBIO Renovabio")
fonte_b3 = f"Fonte: B3, Séries Históricas de CBIO (dados até {cbio_data.index.max().strftime('%d/%m/%Y')})."
st.write(fonte_b3)


cbio_negociacoes = pd.read_csv("data/processed/cbio_negociacoes.csv",sep=";",decimal=",",index_col=0)
cbio_negociacoes.index = pd.to_datetime(cbio_negociacoes.index)
cbio_negociacoes.rename(columns={"Valor Financeiro":"Receita"}, inplace=True)

#Filtros
freq_dict = {False:"Diário", "M":"Mensal", "Q":"Trimestral", "Y":"Anual"}
freq = st.sidebar.radio("Agregação", (False,"M", "Q", "Y"), index=1, horizontal=True,
                format_func=lambda x: freq_dict[x]) # Use format_func to replace spaces with underscores and convert to lowercase

if freq:
    cbio_data  = cbio_data.groupby(pd.Grouper(freq=freq)).sum()
    cbio_negociacoes = cbio_negociacoes.drop(["Ativo","Liquidação"],axis=1).astype(float).groupby(pd.Grouper(freq=freq)).mean()

# Gráficos
fig = go.Figure()
fig.add_trace(go.Scatter(x=cbio_data.index, y=cbio_data["Aposentadoria"], mode='lines', name='Aposentadoria'))
fig.add_trace(go.Scatter(x=cbio_data.index, y=cbio_data["Estoque"], mode='lines', name='Estoque',yaxis='y2'))

fig.update_layout(title=f"Créditos de Descarbonização (CBIO): Aposentadoria e Estoque <br><sup>{cbio_data.index[0].date()} - {cbio_data.index[-1].date()}<sup>",
                    yaxis2=dict( overlaying='y', side='right'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1))

st.plotly_chart(fig, use_container_width=True)
st.caption("O gráfico mostra a evolução dos créditos de descarbonização (CBIOs) aposentados e do estoque no âmbito do RenovaBio, na agregação escolhida ao lado. A linha mais escura representa o volume de CBIOs efetivamente aposentados (eixo à esquerda), enquanto a linha mais clara indica o estoque disponível no mercado (eixo à direita). " + fonte_b3)


preco, receita = st.columns(2)

with preco:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cbio_negociacoes.index, y=cbio_negociacoes["Preço Médio"], mode='lines', name='Medio'))

    fig.update_layout(title=f"Preço Médio {freq_dict[freq]} (R$) <br><sup>{cbio_negociacoes.index[0].date()} - {cbio_negociacoes.index[-1].date()}<sup>",
                        yaxis2=dict( overlaying='y', side='right'),
                        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1))

    st.plotly_chart(fig, use_container_width=True)
    st.caption("O gráfico mostra a evolução do preço médio dos créditos de descarbonização (CBIOs), na agregação escolhida ao lado. " + fonte_b3)

with receita:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cbio_negociacoes.index, y=cbio_negociacoes["Receita"], mode='lines', name='Receita (R$)'))

    fig.update_layout(title=f"Receita Média {freq_dict[freq]} (R$) <br><sup>{cbio_negociacoes.index[0].date()} - {cbio_negociacoes.index[-1].date()}<sup>",
                        yaxis2=dict( overlaying='y', side='right'),
                        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1))

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Este gráfico apresenta o valor financeiro médio das transações com CBIOs, na agregação escolhida ao lado. " + fonte_b3)

