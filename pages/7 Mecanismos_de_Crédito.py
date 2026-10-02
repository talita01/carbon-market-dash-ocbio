import os
import streamlit as st
import pandas as pd
import plotly.express as px

from utils import components as c

############################## Configurações da página (inicio) ##############################
c.pag_config(os.path.basename(__file__))
c.sobre_dash()
############################## Configurações da página (fim) ##############################

# Carregar os dados
detalhe = pd.read_csv("data/processed/wb_crediting_info.csv", sep=";", decimal=",")
emissao = pd.read_csv("data/processed/wb_crediting_issuance.csv", sep=";", decimal=",")
acordos = pd.read_csv("data/processed/wb_cooperative.csv", sep=";")
cer = pd.read_csv("data/processed/cer_accu.csv", sep=";", decimal=",")
iso = pd.read_csv("data/processed/iso_countries.csv", sep=";", index_col=1)["ISO"]

emissao = emissao.merge(detalhe[["Mechanism", "Administration"]], on="Mechanism", how="left")
ultimo_ano = emissao["Year"].max()

st.title("Mecanismos de Crédito e Artigo 6")
st.write(c.fonte("WB_CREDITO", "WB_ARTIGO6", "CER"))
st.markdown("##") #espacamento entre blocos

# METRICAS (RESUMO)
emitido_ultimo = emissao[emissao["Year"] == ultimo_ano]["Issued"].sum() / 1e6
emitido_anterior = emissao[emissao["Year"] == ultimo_ano - 1]["Issued"].sum() / 1e6

metrics_col = st.columns(4)
metrics_col[0].metric("Mecanismos implementados", (detalhe["Status"] == "Implementado").sum(), border=True,
                      help="Mecanismos com status 'Implemented' na aba Crediting_Detail do Banco Mundial.")
metrics_col[1].metric(f"Emitidos em {ultimo_ano} (milhões)", f"{emitido_ultimo:.1f}",
                      delta=f"{emitido_ultimo - emitido_anterior:.1f} milhões", border=True,
                      help="Soma dos mecanismos da aba Crediting_Issuance; variação em relação ao ano anterior abaixo.")
metrics_col[2].metric(f"Emitidos até {ultimo_ano} (bilhões)", f"{detalhe['Cumulative issued (kt)'].sum() / 1e6:.2f}",
                      border=True, help=f"Créditos emitidos até 31/12/{ultimo_ano}: soma dos acumulados informados na aba Crediting_Detail (em mil toneladas, convertidos).")
metrics_col[3].metric("Acordos do Artigo 6.2", len(acordos), border=True,
                      help="Acordos da aba Cooperative Approaches, em qualquer estágio.")

st.markdown("##") #espacamento entre blocos

# EMISSÃO ANUAL
st.header("Emissão anual de créditos")

col1, col2 = st.columns([1, 4])
agrupar = col1.radio("Agrupar por", ("Administração", "Mecanismo"),
                     help="Mecanismo: os 10 maiores emissores no último ano; os demais somados em 'Outros'.")
ano_inicial = col1.slider("A partir de", int(emissao["Year"].min()), int(ultimo_ano), 2010)

dados = emissao[emissao["Year"] >= ano_inicial].copy()
if agrupar == "Administração":
    dados["grupo"] = dados["Administration"]
    legenda = "Administração"
else:
    maiores = emissao[emissao["Year"] == ultimo_ano].nlargest(10, "Issued")["Mechanism"]
    dados["grupo"] = dados["Mechanism"].where(dados["Mechanism"].isin(maiores), "Outros")
    legenda = "Mecanismo"

dados = dados.groupby(["Year", "grupo"])["Issued"].sum().div(1e6).reset_index()
fig = px.bar(dados, x="Year", y="Issued", color="grupo",
             labels={"Year": "Ano", "Issued": "Milhões de créditos", "grupo": legenda})
fig.update_layout(title=dict(text=f"Créditos emitidos por ano, por {legenda.lower()}", font=dict(size=16)),
                  legend=dict(font=dict(size=11)))
col2.plotly_chart(fig, use_container_width=True)
st.caption("O gráfico mostra a emissão anual de créditos de carbono pelos mecanismos de crédito independentes (como o Verified Carbon Standard e o Gold Standard), "
           "internacionais (como o Mecanismo de Desenvolvimento Limpo) e governamentais. Segundo o Banco Mundial, os números incluem emissões "
           "originais e não originais, e os dos mecanismos governamentais são em geral autodeclarados, podendo não coincidir com os acumulados. "
           + c.fonte("WB_CREDITO"))

# MECANISMOS
st.markdown("##") #espacamento entre blocos
st.header("Mecanismos de crédito")

col1, col2, col3 = st.columns(3)
status = col1.multiselect("Status", detalhe["Status"].unique(), default=["Implementado"])
administracao = col2.multiselect("Administração", detalhe["Administration"].unique(),
                                 default=list(detalhe["Administration"].unique()))
somente_aceitos = col3.toggle("Só os aceitos em instrumentos de compliance", False)

tabela = detalhe[detalhe["Status"].isin(status) & detalhe["Administration"].isin(administracao)]
if somente_aceitos:
    tabela = tabela[tabela["Accepted by compliance instruments"].notnull()]

tabela = tabela.sort_values("Cumulative issued (kt)", ascending=False)[[
    "Mechanism", "Administration", "Status", "Year of Implementation", "Scope", "Jurisdiction", "Credit name",
    "Price (Range)", "Accepted by compliance instruments", "Eligible sectors", "Cumulative issued (kt)",
    "Cumulative retired (kt)", "Cumulative projects registered"]]\
    .rename(columns={"Mechanism": "Mecanismo", "Administration": "Administração", "Year of Implementation": "Início",
                     "Scope": "Abrangência", "Jurisdiction": "Jurisdição", "Credit name": "Crédito",
                     "Price (Range)": "Preço (faixa, como informado)",
                     "Accepted by compliance instruments": "Aceito por instrumentos de compliance",
                     "Eligible sectors": "Setores elegíveis",
                     "Cumulative issued (kt)": f"Emitidos até {ultimo_ano} (mil t)",
                     "Cumulative retired (kt)": f"Aposentados até {ultimo_ano} (mil t)",
                     "Cumulative projects registered": f"Projetos registrados até {ultimo_ano}"})

st.dataframe(tabela, hide_index=True, use_container_width=True,
             column_config={"Início": st.column_config.NumberColumn(format="%d")})
nao_classificados = detalhe[detalhe["Status"] == "Não classificado"]["Mechanism"].tolist()
nota_status = f" Sem status reconhecível no arquivo do Banco Mundial, aparecem como 'Não classificado': {', '.join(nao_classificados)}." \
    if nao_classificados else ""
st.caption(f"A tabela lista {len(tabela)} mecanismos de crédito com os filtros escolhidos, ordenados pelo total emitido. "
           "As faixas de preço estão como o Banco Mundial as informa, em moeda e ano variados." + nota_status + " " + c.fonte("WB_CREDITO"))

# ARTIGO 6.2
st.markdown("##") #espacamento entre blocos
st.header("Artigo 6.2: acordos bilaterais")
st.markdown("O Artigo 6.2 do Acordo de Paris permite a transferência de resultados de mitigação (ITMOs) entre países, "
            "com ajuste correspondente: o país vendedor que autoriza a transferência soma a quantidade transferida às "
            "suas emissões reportadas, para evitar dupla contagem.")

col1, col2 = st.columns(2)

por_comprador = acordos.groupby(["Buyer", "Status"]).size().reset_index(name="Acordos")
ordem = por_comprador.groupby("Buyer")["Acordos"].sum().sort_values().index.tolist()
fig = px.bar(por_comprador, y="Buyer", x="Acordos", color="Status", orientation="h",
             category_orders={"Buyer": ordem[::-1]},
             labels={"Buyer": "", "Status": ""})
fig.update_layout(title=dict(text="Acordos por país comprador e estágio", font=dict(size=16)),
                  legend=dict(orientation="h", yanchor="top", y=-0.2, x=0))
col1.plotly_chart(fig, use_container_width=True)

vendedores = acordos.groupby("Seller").size().reset_index(name="Acordos")
vendedores["ISO"] = vendedores["Seller"].map(iso)
fig = px.choropleth(vendedores.dropna(subset=["ISO"]), locations="ISO", color="Acordos", hover_name="Seller",
                    color_continuous_scale="Blues", projection="equirectangular")
fig.update_geos(showocean=True, oceancolor="#F2F2F2", showcountries=True, showland=True, landcolor="#F2F2F2")
fig.update_layout(title=dict(text="Acordos por país vendedor", font=dict(size=16)), margin=dict(b=0))
col2.plotly_chart(fig, use_container_width=True)

st.caption(f"Os gráficos mostram os {len(acordos)} acordos bilaterais do Artigo 6.2 registrados pelo Banco Mundial, de "
           f"{acordos['Year'].min()} a {acordos['Year'].max()}, por país comprador e estágio (memorando de entendimento, acordo "
           "de implementação ou autorização bilateral concluída) e por país vendedor. Acordos do Japão (JCM) e da Austrália "
           "(IPCOS) ficam entre os mecanismos governamentais, não nesta lista. Esta aba do Banco Mundial foi atualizada "
           "um ano antes das demais. " + c.fonte("WB_ARTIGO6"))

with st.expander("Ver lista de acordos"):
    st.dataframe(acordos.rename(columns={"Buyer": "Comprador", "Year": "Ano", "Seller": "Vendedor",
                                         "Status": "Estágio", "Notes": "Notas"}),
                 hide_index=True, use_container_width=True,
                 column_config={"Ano": st.column_config.NumberColumn(format="%d")})

# AUSTRÁLIA
st.markdown("##") #espacamento entre blocos
st.header("Austrália: créditos de carbono (ACCU)")

col1, col2 = st.columns([1, 4])
freq = col1.radio("Agregação", ("Anual", "Trimestral"))
serie = col1.radio("Série", cer["series"].unique())

dados = cer[cer["series"] == serie].copy()
ano_cer = dados["year"].max()
trimestres_cer = dados[dados["year"] == ano_cer]["quarter"].nunique()
if freq == "Anual":
    dados["periodo"] = dados["year"].astype(str)
else:
    dados["periodo"] = dados["year"].astype(str) + "-" + dados["quarter"]
dados = dados.groupby(["periodo", "category"])["value"].sum().reset_index()

unidade = "Projetos" if serie == "Projetos registrados" else "ACCUs (1 ACCU = 1 tCO2e)"
fig = px.bar(dados, x="periodo", y="value", color="category",
             labels={"periodo": "", "value": unidade, "category": ""})
fig.update_layout(title=dict(text=f"{serie}, por {'tipo de método' if 'cancel' not in serie else 'tipo de cancelamento'}",
                             font=dict(size=16)))
col2.plotly_chart(fig, use_container_width=True)

nota_ano = f" No modo anual, {ano_cer} tem só {trimestres_cer} trimestre(s)." if trimestres_cer < 4 else ""
st.caption("O gráfico mostra, por trimestre ou ano, as ACCUs (Australian Carbon Credit Units) emitidas e os projetos "
           "registrados por tipo de método, e os cancelamentos de ACCUs fora do Safeguard Mechanism por tipo "
           "(voluntários, de conformidade e governamentais). O preço spot da ACCU não entra porque o Clean Energy "
           "Regulator o publica só em gráfico." + nota_ano + " " + c.fonte("CER"))
