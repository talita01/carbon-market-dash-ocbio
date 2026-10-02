import os
import streamlit as st  
import pandas as pd
import numpy as np
import plotly.express as px

from utils import components as c

############################## Configurações da página (inicio) ##############################
c.pag_config(os.path.basename(__file__))
c.sobre_dash(expanded=True)
############################## Configurações da página (fim) ##############################

# Carregar os dados
data_wb = pd.read_csv("data/processed/wb_info.csv",sep=";",decimal=",")
series_wb = pd.read_csv("data/processed/wb_time_series.csv",sep=";",decimal=",")
update_info = pd.read_csv("data/update_info.csv",index_col=0)['Last Update']

# Informações gerais
st.title("Mecanismos de Compliance")
st.text(c.fonte("WB"))

# Estatisticas de data_wb
percent_emissoes = sum(data_wb["Share of global emissions covered"].dropna())*100
# variação: soma da aba Compliance_Emissions no último ano menos a do ano anterior
emissoes_ano = series_wb.groupby("Year")["Emissions"].sum()*100
ano_emissoes = series_wb.dropna(subset=["Emissions"])["Year"].max()
crescimento_percent_emissoes = emissoes_ano[ano_emissoes] - emissoes_ano[ano_emissoes-1]

implementadas = data_wb[data_wb['Status']=="Implementado"]
iniciativas_implementadas = len(implementadas["Instrument name"].unique())
iniciativas_anteriores = len(implementadas[implementadas["Start Year"]<implementadas["Start Year"].max()]["Instrument name"].unique())
crescimento_iniciativas = iniciativas_implementadas - iniciativas_anteriores

preco_medio = series_wb[series_wb["Year"]==series_wb["Year"].max()]["Price"].dropna().mean()
preco_medio_ano_anterior = series_wb[series_wb["Year"]==series_wb["Year"].max()-1]["Price"].dropna().mean()
crescimento_preco_medio = preco_medio - preco_medio_ano_anterior

#mostra metricas
metrics_col = st.columns(3)
metrics_col[0].metric(f"Iniciativas Implementadas", iniciativas_implementadas, f"{crescimento_iniciativas}", border=True,help='Variação em relação ao ano anterior abaixo')
metrics_col[1].metric("Percentual de emissões globais cobertas", f"{percent_emissoes:.2f}%",delta=f"{crescimento_percent_emissoes:.2f} p.p.", border=True,help=f'Variação em relação ao ano anterior abaixo, em pontos percentuais ({ano_emissoes-1} a {ano_emissoes}, soma da cobertura de emissões dos instrumentos no Banco Mundial)')
metrics_col[2].metric("Preço médio (US$/tCO2e)", f"{preco_medio:.2f}", delta=f"{crescimento_preco_medio:.2f} USD", border=True,help='Variação em relação ao ano anterior abaixo')
 
st.markdown("##") #espacamento entre blocos

#Mapa das Iniciativas
mapa, filtros = st.columns([3,1])

with filtros:

    st.subheader("Filtros")

    status = st.selectbox(
        "Status",
        options=data_wb["Status"].unique()
    )

    tipo = st.multiselect(
        "Abrangência",
        options=data_wb["Subtype"].unique(),
        default=data_wb["Subtype"].unique()
    )

    if status=="Implementado":
            
        tamanho_marcador = st.radio(
            "Tamanho do marcador",
            options=["% de cobertura da jurisdição", "Padrão"],
            index=0
        ) 
    else:

        tamanho_marcador =  "Padrão"

with mapa:

    map_data = data_wb[(data_wb["Status"]==status) &
                        (data_wb["Subtype"].isin(tipo)) &
                        (data_wb["lat"].notnull() )]
    
    map_data["Share of jurisdiction emissions covered"].fillna(0,inplace=True)
    map_data["Share of global emissions covered"].fillna(0,inplace=True)

    hover_txt = {col:False for col in map_data.columns}

    if status  == "Implementado":
        hover_txt["Share of jurisdiction emissions covered"] =  f":.2%"
        hover_txt["Share of global emissions covered"] = f":.2%"
        hover_txt["Subtype"] = True
    else:
        hover_txt["Subtype"] = True


    fig = px.scatter_geo(map_data, lat="lat", lon="lon", color="Type",
                    hover_name="Instrument name", hover_data=hover_txt,
                    size= None if tamanho_marcador=="Padrão" else "Share of jurisdiction emissions covered",
                        projection="equirectangular",
                    labels={"Type":"Tipo de Iniciativa"})

    if tamanho_marcador=="Padrão" : fig.update_traces(marker=dict(size=10))

    fig.update_geos(showocean=True, oceancolor="#F2F2F2", showcountries=True,
                     showland=True, landcolor="#F2F2F2",)
    
    substitle = "" if tamanho_marcador=="Padrão" else "Marcadores proporcionais ao percentual de cobertura da jurisdição"
    title = f'Mecanismos de compliance para precificação de carbono | {status} <br><sup>{substitle}'

    fig.update_layout(
    
        title=dict(text=title, font=dict(size=24),),
            
            width=700,
            height=600,
            margin=dict(b=0),

            showlegend=True,
            legend=dict(
                orientation="v",x=0.5,xanchor="center",
                y=0,yanchor="auto", font=dict(size=14), 
            ),
        )


    st.plotly_chart(fig,theme="streamlit", use_container_width=True)

    caption = "O mapa apresenta a distribuição geográfica dos mecanismos de compliance para precificação de carbono," \
            " classificados em dois tipos principais: taxas de carbono, representados por círculos azuis escuros, " \
            "e sistemas de comércio de emissões, representados por círculos azuis claros. " \
    
    if tamanho_marcador!="Padrão":
        caption+= "O tamanho dos marcadores é proporcional ao percentual de cobertura da jurisdição," \
        " ou seja, reflete a abrangência do instrumento em relação às emissões totais da localidade. "
    
    st.caption(caption + " " + c.fonte("WB"))


#Gráfico de barras/linhas tipos de Iniciativas 

st.header("Distribuição de Iniciativas")

barras, linhas = st.columns(2)

with barras:

    col1, col2 = st.columns(2)

    eixo_x = col1.radio(
        "Agregar por",
        options=["Region", "Income group","Status"],horizontal=True,index=2,
        #traduzir as opções
        format_func=lambda x: "Região" if x=="Region" else "Faixa de Renda" if x=="Income group" else "Status"
    )

    if eixo_x != "Status":
            
        filtro_dados = col2.selectbox(
            "Status da Iniciativa",
            options=data_wb["Status"].unique(), key='col1'
        )

        filtro_leg = " | "+filtro_dados
        filtro_dados = [filtro_dados]

    else:
        filtro_dados = data_wb["Status"].unique()
        filtro_leg = ""

    barra_data = data_wb[data_wb["Status"].isin(filtro_dados)].groupby([eixo_x,'Type'])['Instrument name']\
                        .count()\
                        .to_frame().reset_index()
    
    fig = px.bar(barra_data, x=eixo_x, 
                 y="Instrument name", color="Type", 
                 barmode='group',
                text_auto=True,
                 labels={"Subtype":"Número de Iniciativas","Status":"","Type":"",
                         "Instrument name":"Número de Iniciativas","Region":"Região",},
                 title=f"Distribuição de Iniciativas por {eixo_x} {filtro_leg}",)



    fig.update_layout(

            width=800,
            height=500,

            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1,
                x=0,
                font=dict(size=12)
            ),
        )
    
    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("O gráfico apresenta o número de mecanismos de *compliance* para precificação de carbono, classificados por tipo de instrumento: **taxa de carbono** e **sistema de comércio de emissões**. A visualização permite a aplicação de diferentes filtros e formas de agregação: é possível **filtrar as iniciativas por status** e **agregar os resultados por região geográfica e faixa de renda** (conforme classificação do Banco Mundial). " + c.fonte("WB"))


with linhas:

    filtro_dados = st.radio(
        "Status da Iniciativa",
        options=data_wb["Status"].unique(),
        horizontal=True
    )

    linhas_data = data_wb[(data_wb["Status"]==filtro_dados)].groupby(["Start Year","Type"])["Instrument name"]\
            .count().to_frame().reset_index()
    
    linhas_data = linhas_data\
        .join(linhas_data.groupby("Type")["Instrument name"].cumsum().to_frame("Total"))

    fig = px.line(linhas_data, x="Start Year",
                   y="Total", color='Type',
                   labels={"Type":"","Start Year":"Ano",},
                   title=f"Distribuição de Iniciativas por Ano e Tipo | {filtro_dados}",
                   )
    

    fig.update_layout(

            width=800,
            height=500,

            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1,
                x=0,
                font=dict(size=12)
            ),
        )
    
    

    st.plotly_chart(fig, use_container_width=True)
    # instrumentos sem ano de início ficam fora da linha do tempo; anos derivados ficam marcados
    status_sel = data_wb[data_wb["Status"]==filtro_dados]
    sem_ano = status_sel[status_sel["Start Year"].isnull()]["Instrument name"].tolist()
    derivados = status_sel[status_sel["Start Year derived"].fillna(False).astype(bool)]
    nota = ""
    if sem_ano:
        nota += f" O arquivo do Banco Mundial não informa o ano de início de {len(sem_ano)} instrumentos com este status, que não aparecem na linha do tempo: {', '.join(sem_ano)}."
    if len(derivados):
        nota += " Ano de início derivado pelo painel (o Banco Mundial não o informa): " + \
            ", ".join(f"{n} ({int(a)})" for n, a in derivados[["Instrument name","Start Year"]].values) + "."
    st.caption("O gráfico apresenta a evolução do número  de mecanismos de compliance para precificação de carbono, por status, ao longo do tempo, diferenciando entre taxas de carbono e sistemas de comércio de emissões. É possível filtrar as iniciativas por status." + nota + " " + c.fonte("WB"))
    

st.markdown("##") #espacamento entre blocos
st.header("Séries Históricas")

preco, emissoes, receita = st.columns(3)

with preco:

    price_data = series_wb.groupby(["Instrument Type","Year"])["Price"]\
        .agg(["mean","median","min","max"]).dropna(how="all").reset_index()

    agg_dict = {"mean":"Média","median":"Mediana","min":"Mínimo","max":"Máximo","sum":"Total"}

    plot_placeholder = st.empty()

    aggregation = st.radio(
        "Agregar por Preço",
        options=["mean","median","min","max"],
        index=0,
        horizontal=True,

        format_func=lambda x: agg_dict[x]
    )

    labels_dict = {"Instrument Type":"","Year":"Ano",aggregation:""}
    labels_dict.update(agg_dict)
    
    fig = px.line(price_data, x="Year", y=aggregation, color='Instrument Type',
                    labels=labels_dict)

    fig.update_layout(

            title=dict(text=f"Evolução do Preço por Tipo de Iniciativa | {agg_dict[aggregation]}", ),
            
            width=500,
            height=400,

            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1,
                x=0,
                font=dict(size=12)
            ),
        )

    plot_placeholder.plotly_chart(fig, use_container_width=True)
    st.caption("O gráfico mostra a evolução histórica dos preços  em mecanismos de compliance para precificação  de carbono, diferenciando entre taxas de carbono  e ETS. A visualização permite que o preço seja  agregado por valor médio, mediana, mínimo, e  máximo. " + c.fonte("WB"))


with emissoes:
    
    emissoes = series_wb.groupby(["Instrument Type","Year"])["Emissions"].sum()*100
    emissoes = emissoes.to_frame().reset_index()

    labels_dict = {"Instrument Type":"","Year":"Ano","Emissions":"%"}
    labels_dict.update(agg_dict)

    fig = px.line(emissoes, x="Year", y="Emissions", color='Instrument Type',
                    labels=labels_dict)


    fig.update_layout(

            title=dict(text=f"% das Emissões Cobertas por Tipo de Iniciativa", ),
            
            width=500,
            height=400,

            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1,
                x=0,
                font=dict(size=12)
            ),
        )

    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("O gráfico apresenta a proporção de emissões de gases de efeito estufa cobertas por mecanismos de compliance para precificação de carbono, ao longo do tempo, por tipo de iniciativa. " + c.fonte("WB"))


with receita:

    receita_data = series_wb.groupby(["Instrument Type","Year"])["Revenue"]\
        .agg(["mean","sum"]).dropna(how="all").reset_index().dropna()

    agg_dict = {"mean":"Média","sum":"Total"}

    plot_placeholder = st.empty()

    aggregation = st.radio(
        "Agregar por Preço",
        options=["mean","sum"],
        index=0,
        horizontal=True,
        format_func=lambda x: agg_dict[x]
    )

    labels_dict = {"Instrument Type":"","Year":"Ano",aggregation:""}
    labels_dict.update(agg_dict)

    
    fig = px.line(receita_data, x="Year", y=aggregation, color='Instrument Type',
                    labels=labels_dict
                    )

    fig.update_layout(

            title=dict(text=f"Evolução da Receita {agg_dict[aggregation]} por Tipo de Iniciativa", ),
            
            width=500,
            height=400,

            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1,
                x=0,
                font=dict(size=12)
            ),
        )

    plot_placeholder.plotly_chart(fig, use_container_width=True)
    st.caption("O gráfico mostra a receita anual gerada por  mecanismos de compliance para precificação de  carbono, desagregada por tipo (taxa de carbono e  ETS). A visualização premite que a receita seja agregada por valor médio e total. " + c.fonte("WB"))


st.header("Comparação Preço Explícito")

ets, carbon_tax = st.columns(2)

last_year = series_wb['Year'].max()
latest_prices = series_wb[series_wb['Year'] == last_year].copy()
latest_prices = latest_prices.set_index(['Name of the initiative', 'Instrument Type'])['Price'].unstack()

price_ets, price_carbon_tax = latest_prices['ETS'].dropna().sort_values().reset_index(),\
                                latest_prices['Taxas de Carbono'].dropna().sort_values().reset_index()


with ets:
    fig = px.scatter(price_ets, y='Name of the initiative', x='ETS',
                    labels={"Name of the initiative":"",'ETS':"US$/tCO2e"},
                    )

    fig.update_layout(

        title=dict(text=f"Preço Explícito ETS em {last_year} (US$/tCO2e)", ),
        margin=dict(l=0, r=0, b=0),

    )

    
    st.plotly_chart(fig, use_container_width=True)

with carbon_tax:
    fig = px.scatter(price_carbon_tax, y='Name of the initiative', x='Taxas de Carbono',
                    labels={"Name of the initiative":"",'Taxas de Carbono':"US$/tCO2e"},
                    )
    
    fig.update_layout(

        title=dict(text=f"Preço Explícito Taxas de Carbono em {last_year} (US$/tCO2e)", ),
        margin=dict(l=0, r=0, b=0),
    )


    st.plotly_chart(fig, use_container_width=True)

st.caption(f"O gráfico apresenta o preço explícito do carbono (em US$/tCO₂e) praticado em diferentes países e regiões, em {last_year}, com distinção entre taxas de carbono e ETS. " + c.fonte("WB"))