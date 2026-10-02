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


mvc_credits = pd.read_csv("data/processed/mvc_credits.csv", sep=";", decimal=",",index_col=0)
mvc_credits_info = pd.read_csv("data/processed/mvc_credits_info.csv", sep=";", decimal=",",index_col=0)
iso_countries = pd.read_csv("data/processed/iso_countries.csv", sep=";", decimal=",",index_col=1)
update_info = pd.read_csv("data/update_info.csv",index_col=0)['Last Update']

mvc_credits_info.rename(columns={"First Year of Project (Vintage)":"Start Year"},inplace=True)
mvc_credits_info["Start Year"] = mvc_credits_info["Start Year"].astype(int, errors='ignore')

#copia para parte 2 do dash
credits_pais = mvc_credits.copy()
pais_info = mvc_credits_info.copy()


#titulo
st.title("Mercado Voluntário")
st.write(c.fonte("MVC", "EM"))
st.markdown("##") #espacamento entre blocos



## filtros ## 
col1, col2 = st.columns([1, 5])

dado = col1.radio("Mapa",("Total Créditos Emitidos","Número de Projetos"))

anos_disp = mvc_credits_info["Start Year"].dropna().astype(int).sort_values().unique()[::-1]
tempo = col1.selectbox("Ano Início",["Total"]+list(anos_disp),
                             help="Total será a soma de todos os anos disponíveis.")

setor = col1.selectbox("Escopo",["Todos"]+list(mvc_credits_info["Scope"].sort_values().unique()),
                                help="Todos será a soma de todos os escopos disponíveis")


## prepara dados baseado nos filtros ##
if tempo != "Total":
    mvc_credits_info = mvc_credits_info[mvc_credits_info["Start Year"] == tempo]
    tempo_info = tempo

else:
    tempo_info = f"{int(mvc_credits_info["Start Year"].min())} - {int(mvc_credits_info["Start Year"].max())}"

if setor != "Todos":
    mvc_credits_info= mvc_credits_info[mvc_credits_info["Scope"] == setor]
    setor_info = setor
else:
    setor_info = f"<sup>{', '.join(mvc_credits_info["Scope"].unique())}</sup>"

#filtra as datas (index) 
mvc_credits = mvc_credits[mvc_credits.index.isin(mvc_credits_info.index)]

if not len(mvc_credits_info):
    col2.warning("Nenhum projeto corresponde aos filtros selecionados.")

else:
    creditos_pais = mvc_credits_info.groupby("Country")["Total Credits Issued"].agg(["count","sum"])\
        .rename(columns={"count":"Número de Projetos","sum":"Total Créditos Emitidos"})

    creditos_pais  = creditos_pais[creditos_pais.index.isin(iso_countries.index)] #exclude international projects 
    creditos_pais = creditos_pais.join(iso_countries)

    # mapa #
    fig = px.choropleth(creditos_pais,
                        locations="ISO",
                        color=creditos_pais[dado],
                        hover_name=creditos_pais.index,
                        hover_data=["Total Créditos Emitidos","Número de Projetos"],
                        labels={"Total Créditos Emitidos":"Total Créditos Emitidos",
                                "Número de Projetos":"Número de Projetos"},
                        scope="world")

    fig.update_geos(showocean=True, oceancolor="#F2F2F2", showcountries=True,
                        showland=True, landcolor="#F2F2F2",)

    fig.update_layout(
                 
        title=dict(text=f"{dado} por País | {tempo_info} <br>{setor_info}", font=dict(size=20),),
        width=800,
        height=500,
        margin=dict(b=0),

        showlegend=True,
        legend=dict(
            orientation="v",x=0,xanchor="right",
            y=0.9,yanchor="auto", font=dict(size=14)
        ),
        )

    col2.plotly_chart(fig, use_container_width=True)
st.caption("O mapa apresenta a distribuição geográfica dos créditos de carbono emitidos no mercado voluntário, com base em projetos certificados em diferentes escopos. A visualização permite a seleção por ano e escopo, e pode ser alternada entre o total de créditos emitidos ou o número de projetos registrados por país. " + c.fonte("MVC"))


st.markdown("##") #espacamento entre blocos
setor_info= "<sup>Todos os escopos disponíveis" if setor == "Todos" else f"<sup>{setor_info}" #ajusta subtitulo

#serie historica de créditos
summary_credits = mvc_credits.groupby("Ano").sum()

fig = go.Figure()

for col in ['Aposentados', 'Emitidos (data de emissão)']:
    fig.add_trace(go.Bar(
        x= summary_credits.index,y=summary_credits[col],name=col
    ))

fig.add_trace(go.Scatter(
    x= summary_credits.index,y=summary_credits["Emitidos (data de redução/remoção)"],
    name="Emitidos (data de redução/remoção)", mode="lines+markers",
    line=dict(dash="dot", width=2), marker=dict(size=6)
))

fig.update_layout(title=dict(text=f"Série histórica de demanda e oferta de créditos de carbono | {tempo_info}<br>{setor_info}", font=dict(size=20),),
                   legend=dict(orientation="h", yanchor="bottom",x=0, y=1,font=dict(size=12)))

st.plotly_chart(fig, use_container_width=True)
st.caption("O gráfico mostra a evolução anual do total de créditos de carbono emitidos (por data de emissão e remoção/redução) e aposentados no mercado voluntário de carbono. O ano corrente fica de fora por estar incompleto. " + c.fonte("MVC"))

col2, col3 = st.columns(2)

# por tipo
summary_objective = mvc_credits_info.groupby("Reduction / Removal")["Total Credits Issued"].count().sort_values().to_frame("total")
summary_objective["percent"] = summary_objective.div(summary_objective.sum())*100
summary_objective["percent"] = summary_objective["percent"].round(2).astype(str) + "%"

fig  = px.bar(summary_objective,x="total",text="percent",
              title=f"Créditos por Tipo de Projeto | {tempo_info}<br>{setor_info}",
            labels={"total":"Número de Projetos", "Reduction / Removal":"Objetivo"})
col2.plotly_chart(fig, use_container_width=True)
col2.caption("O gráfico apresenta o número de projetos no mercado voluntário de carbono de acordo com o tipo de projeto. " + c.fonte("MVC"))

# por escopo
summary_objective = mvc_credits_info.groupby("Voluntary Registry")["Total Credits Issued"].count().sort_values().to_frame("total")
summary_objective["percent"] = summary_objective.div(summary_objective.sum())*100
summary_objective["percent"] = summary_objective["percent"].round(2).astype(str) + "%"

fig  = px.bar(summary_objective,x="total",text="percent",
              title=f"Créditos por Certificadora | {tempo_info}<br>{setor_info}",
            labels={"total":"Número de Projetos", "Voluntary Registry":"Certificadora"})
col3.plotly_chart(fig, use_container_width=True)
col3.caption("Este gráfico mostra o número de projetos registrados em diferentes certificadoras no mercado voluntário de carbono. " + c.fonte("MVC"))

st.markdown("##") #espacamento entre blocos
st.subheader("Créditos no MVC por localização")

col1, col2, col3, col4 = st.columns(4)

LOCAIS_DICT = {"Region":"Região", "Country":"País"}
visualizar_por = col1.radio("Visualizar por:", ("Region", "Country"),horizontal=True,format_func=lambda x:LOCAIS_DICT[x])
visualizar = col2.radio("Visualizar",("Número de Projetos","Total Créditos Emitidos"))

anos_possiveis = list(pais_info["Start Year"].dropna().astype(int).sort_values().unique()[::-1])
tempo = col3.selectbox("Ano Início",["Total"]+anos_possiveis,help="Total será a soma de todos os anos disponíveis.",key=2)

CATEGORIAS_DICT = {"Reduction / Removal":"Tipo de Projeto","Voluntary Registry":"Certificadora","Scope":"Escopo","Total":"Total" }
separar_por = col4.selectbox("Separar por:", ("Total","Scope", "Voluntary Registry","Reduction / Removal"),help="Total será a soma de projetos disponíveis",key=3,
                             format_func=lambda x: CATEGORIAS_DICT[x])


escolher_top = False #inicializar variavel 

if tempo != "Total":
    pais_info = pais_info[pais_info["Start Year"]== tempo]
    tempo_info = f"em {tempo}"

else:
    tempo_info = f"entre {min(anos_possiveis)} à {max(anos_possiveis)}"

    if visualizar_por == "Country":
        escolher_top = col1.toggle("Filtrar Número de Países", True)


if separar_por != "Total":
    data_plot = pais_info.groupby([visualizar_por,separar_por])["Total Credits Issued"].agg(["count","sum"])\
                .rename(columns={"count":"Número de Projetos","sum":"Total Créditos Emitidos"})

    data_plot = data_plot[visualizar].unstack(level=1)

else:
    data_plot = pais_info.groupby(visualizar_por)["Total Credits Issued"].agg(["count","sum"])\
        .rename(columns={"count":"Número de Projetos","sum":"Total Créditos Emitidos"})[[visualizar]]
    
    
data_plot['total'] = data_plot.sum(axis=1)

if escolher_top:
    
    cola, colb = col1.columns(2)
    top_num = cola.number_input("Número de Países", min_value=1, max_value=len(pais_info["Country"].unique()), value=10, step=1)
    maiores = colb.checkbox("Maiores", True)

    data_plot=data_plot.sort_values(by="total", ascending=not maiores).replace(0,np.nan).dropna(how='all')[:top_num]

    
    subtitle = f"<sup> Top {top_num} Países com {'Maior' if maiores else 'Menor'} {visualizar}"

else:
    subtitle = ""

data_plot=data_plot.sort_values(by="total", ascending=True).drop("total", axis=1)


fig = px.bar(data_plot,
             y=data_plot.index,
             x=data_plot.columns,
            title=f"{visualizar} por {visualizar_por} | Projetos Iniciados {tempo_info} <br>{subtitle}",
            labels={separar_por:CATEGORIAS_DICT[separar_por],visualizar_por:LOCAIS_DICT[visualizar_por],"value":visualizar}
             )

st.plotly_chart(fig, use_container_width=True)
st.caption("O gráfico apresenta a distribuição do número de projetos de carbono no mercado voluntário por região. A visualização oferece diferentes possibilidades de consulta: é possível agrupar os dados por região ou país, selecionar a métrica desejada (número de projetos ou total de créditos emitidos), definir o recorte temporal com base no ano de início, e ainda visualizar os resultados por escopo do projeto, certificadora ou tipo de projeto (ex: redução, remoção, etc.). " + c.fonte("MVC"))

##################### 
st.header("MVC: preço e volume")

col1, col2 = st.columns(2)

ver_dados_por = col1.radio("Ver dados por:", ("Região", "Categoria"),horizontal=True)

aba_em = "EM_Regiao" if ver_dados_por == "Região" else "EM_Categoria"
df_em = pd.read_excel("data/processed/DADOS_MANUAIS.xlsx", sheet_name=aba_em)
edicoes = df_em.groupby("Ano")[["Edição", "Tabela"]].first()

volume = col2.radio("Comparar Volume",("Total","Porcentagem"),horizontal=True) #como deixar mais claro?

#graficos mercado 
col1, col2 = st.columns(2)

#volume de créditos 
df_selecionado = df_em.pivot_table(index="Ano", columns=ver_dados_por,
                                   values=["Volume (MtCO2e)", "Preço (US$/tCO2e)"])

volume_df = df_selecionado["Volume (MtCO2e)"]
if volume == "Porcentagem":
    volume_df = volume_df.div(volume_df.fillna(0).sum(axis=1), axis=0)

info_vol = "%" if volume == "Porcentagem" else "MtCO2e"

fig = px.bar(volume_df,
            title=f"Volume Negociado por {ver_dados_por}",
            labels={"value": f"Volume ({info_vol})", "Ano": "", ver_dados_por: ""})
fig.update_xaxes(dtick=1)

if volume == "Porcentagem":
    fig.update_layout(yaxis_tickformat = '.00%',)

nota_em = "Volume e preço médio das transações registradas pela Ecosystem Marketplace em cada ano. " \
    "Cada ano vem da edição mais recente que o reporta: " + \
    "; ".join(f"{a}: {e}, {t}" for a, (e, t) in edicoes.iterrows()) + \
    ". Ausente: não reportado na edição. " \
    "Esta série não emenda com a série de 2016 a 2020 que o painel mostrava antes (edição 2021): a Ecosystem Marketplace mudou as categorias e as regiões."

col2.plotly_chart(fig, use_container_width=True)
col2.caption("Este gráfico mostra o volume anual de créditos negociados no mercado voluntário. É possível comparar os dados em termos absolutos ou relativos (percentual do total reportado no ano), e visualizar por região ou categoria. " + nota_em + " " + c.fonte("EM"))

fig = px.bar(df_selecionado["Preço (US$/tCO2e)"],
            barmode="group",
            title=f"Preço Médio por {ver_dados_por}",
            labels={"value": "US$/tCO2e", "Ano": "", ver_dados_por: ""})
fig.update_xaxes(dtick=1)
fig.update_layout(yaxis_tickformat = '$,',)

col1.plotly_chart(fig, use_container_width=True)
col1.caption("O gráfico apresenta o preço médio anual dos créditos de carbono no mercado voluntário. A visualização permite alternar entre dados por região ou categoria. " + nota_em + " " + c.fonte("EM"))
