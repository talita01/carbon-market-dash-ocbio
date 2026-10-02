import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import components as c

############################## Configurações da página (inicio) ##############################
c.pag_config(os.path.basename(__file__))
c.sobre_dash()
############################## Configurações da página (fim) ##############################

# Carregar os dados
marcos = pd.read_excel("data/processed/DADOS_MANUAIS.xlsx", sheet_name="SBCE_Marcos", dtype={"Data": str, "Fim": str})
em_regiao = pd.read_excel("data/processed/DADOS_MANUAIS.xlsx", sheet_name="EM_Regiao")
data_wb = pd.read_csv("data/processed/wb_info.csv", sep=";", decimal=",")
mvc_info = pd.read_csv("data/processed/mvc_credits_info.csv", sep=";", decimal=",", index_col=0)
mvc_credits = pd.read_csv("data/processed/mvc_credits.csv", sep=";", decimal=",", index_col=0)

st.title("Brasil")
st.write(c.fonte("SBCE", "WB", "MVC", "EM"))
st.markdown("##") #espacamento entre blocos

############################## SBCE ##############################
st.header("Mercado regulado: o SBCE")

st.markdown(
    "A **Lei 15.042, de 11 de dezembro de 2024**, institui o Sistema Brasileiro de Comércio de Emissões de Gases de Efeito "
    "Estufa (**SBCE**), um mercado regulado com limite máximo de emissões e negociação de cotas. O sistema tem dois ativos, "
    "inscritos no Registro Central do SBCE: a **Cota Brasileira de Emissões (CBE)**, direito de emitir uma tonelada de CO₂e, "
    "e o **Certificado de Redução ou Remoção Verificada de Emissões (CRVE)**, que representa uma tonelada de CO₂e reduzida "
    "ou removida e verificada sob metodologia credenciada.\n\n"
    "Ficam sujeitos à regulação os operadores de instalações que emitem mais de **10 mil tCO₂e por ano**, obrigados a "
    "monitorar e relatar suas emissões; acima de **25 mil tCO₂e por ano**, também a conciliar periodicamente suas "
    "obrigações (arts. 29 e 30). A produção primária agropecuária não é atividade regulada (art. 2º, §§ 2º e 3º). "
    "O CBIO, título do RenovaBio, não é ativo do SBCE: a lei não menciona o CBIO nem o RenovaBio, e prevê coordenação "
    "entre os instrumentos de precificação existentes (art. 4º, I).\n\n"
    "A cobertura setorial e o faseamento ainda dependem de regulamentação. Os setores e anos abaixo são de uma "
    "**proposta preliminar** do Ministério da Fazenda, não de norma em vigor."
)

# linha do tempo
marcos["Ano"] = marcos["Data"].str[:4].astype(int)
marcos["Quando"] = marcos.apply(
    lambda r: (pd.to_datetime(r["Data"]).strftime("%d/%m/%Y") if len(r["Data"]) > 4 else r["Data"]) +
              (f" a {pd.to_datetime(r['Fim']).strftime('%d/%m/%Y')}" if pd.notnull(r["Fim"]) else ""), axis=1)
marcos["x"] = pd.to_datetime(marcos["Data"].where(marcos["Data"].str.len() > 4, marcos["Data"] + "-01-01"))

fig = px.scatter(marcos, x="x", y="Situação", color="Situação", hover_name="Quando",
                 hover_data={"Marco": True, "x": False, "Situação": False},
                 labels={"x": "", "Situação": ""})
fig.update_traces(marker=dict(size=14))
fig.update_layout(title=dict(text="Marcos do SBCE", font=dict(size=16)), showlegend=False, height=320,
                  margin=dict(l=0, r=0, b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown("\n".join(f"- **{r['Quando']}** ({r['Situação'].lower()}): {r['Marco']}. Fonte: [{r['Fonte']}]({r['URL']})."
                       for _, r in marcos.iterrows()))
st.caption("A linha do tempo reúne as normas do SBCE e as etapas da regulamentação. As fases 2027, 2029 e 2031 são da proposta "
           "preliminar apresentada pelo Ministério da Fazenda em 19/05/2026; cada fase dura quatro anos e começa pela "
           "obrigação de monitorar e relatar. Não há preço de CBE: o mercado ainda não opera. " + c.fonte("SBCE"))

brasil_ets = data_wb[data_wb["Unique ID"] == "ETS_BR"]
if len(brasil_ets):
    linha = brasil_ets.iloc[0]
    with st.expander(f"O SBCE no Banco Mundial: \"{linha['Instrument name']}\", status {linha['Status'].lower()}"):
        st.markdown(f"Descrição do Banco Mundial (em inglês, como publicada):\n\n> {linha['Description']}")
        st.caption(c.fonte("WB"))

############################## MERCADO VOLUNTÁRIO ##############################
st.markdown("##") #espacamento entre blocos
st.header("Mercado voluntário no Brasil")

brasil = mvc_info[mvc_info["Country"] == "Brazil"]
por_pais = mvc_info.groupby("Country")["Total Credits Issued"].sum().sort_values(ascending=False)
posicao = list(por_pais.index).index("Brazil") + 1

metrics_col = st.columns(5)
metrics_col[0].metric("Projetos", len(brasil), border=True)
metrics_col[1].metric("Emitidos (mi)", f"{brasil['Total Credits Issued'].sum() / 1e6:.1f}", border=True)
metrics_col[2].metric("Aposentados (mi)", f"{brasil['Total Credits Retired'].sum() / 1e6:.1f}", border=True)
metrics_col[3].metric("Remanescentes (mi)", f"{brasil['Total Credits Remaining'].sum() / 1e6:.1f}", border=True)
metrics_col[4].metric("Posição mundial", f"{posicao}º de {len(por_pais)}", border=True,
                      help="Posição em créditos emitidos entre os países da base (projetos internacionais contam como um 'país').")
st.caption("Totais acumulados, em milhões de créditos, dos projetos com país Brasil na base da Berkeley, que reúne os registros ACR, ART, CAR, Gold Standard, ISO e VCS. " + c.fonte("MVC"))

# série anual
serie = mvc_credits[mvc_credits.index.isin(brasil.index)].groupby("Ano").sum()
serie = serie[serie.index >= 2005] / 1e6

fig = go.Figure()
for col in ["Aposentados", "Emitidos (data de emissão)"]:
    fig.add_trace(go.Bar(x=serie.index, y=serie[col], name=col))
fig.add_trace(go.Scatter(x=serie.index, y=serie["Emitidos (data de redução/remoção)"], name="Emitidos (data de redução/remoção)",
                         mode="lines+markers", line=dict(dash="dot", width=2), marker=dict(size=6)))
fig.update_layout(title=dict(text=f"Créditos de projetos no Brasil por ano | {serie.index.min()} - {serie.index.max()}", font=dict(size=16)),
                  yaxis_title="Milhões de créditos",
                  legend=dict(orientation="h", yanchor="bottom", x=0, y=1, font=dict(size=12)))
st.plotly_chart(fig, use_container_width=True)
st.caption("O gráfico mostra, por ano, os créditos emitidos (pela data de emissão e pela data da redução ou remoção, a safra) e os "
           "aposentados de projetos no Brasil. O ano corrente fica de fora por estar incompleto. " + c.fonte("MVC"))

# composição
COMPOSICAO = {"Scope": "Escopo", "Type": "Tipo de projeto", "Voluntary Registry": "Certificadora",
              "Reduction / Removal": "Redução ou remoção", "Voluntary Status": "Status do projeto"}
col1, col2 = st.columns([1, 4])
separar = col1.radio("Composição por", list(COMPOSICAO), format_func=lambda x: COMPOSICAO[x])
medida = col1.radio("Medida", ("Créditos emitidos", "Número de projetos"))
top = col1.number_input("Mostrar os maiores", min_value=3, max_value=30, value=10, step=1)

comp = brasil.groupby(separar)["Total Credits Issued"].agg(["sum", "count"])\
    .rename(columns={"sum": "Créditos emitidos", "count": "Número de projetos"})
comp["Créditos emitidos"] = comp["Créditos emitidos"] / 1e6
comp = comp.sort_values(medida, ascending=False)
outros = len(comp) - top
comp = comp.head(top).sort_values(medida)
fig = px.bar(comp, x=medida, y=comp.index, orientation="h", text_auto=".2f" if medida == "Créditos emitidos" else True,
             labels={medida: medida + (" (milhões)" if medida == "Créditos emitidos" else ""), "y": "", separar: ""})
fig.update_layout(title=dict(text=f"Projetos no Brasil por {COMPOSICAO[separar].lower()}", font=dict(size=16)))
col2.plotly_chart(fig, use_container_width=True)
nota_outros = f" Há outras {outros} categorias menores fora do gráfico." if outros > 0 else ""
st.caption("O gráfico mostra a composição dos projetos no Brasil, em número de projetos ou créditos emitidos." + nota_outros + " "
           "As categorias são as da Berkeley (em inglês para tipo de projeto e status). " + c.fonte("MVC"))

# comparação regional
st.subheader("Preço e volume na América Latina e Caribe")
alc = em_regiao[em_regiao["Região"] == "América Latina e Caribe"].set_index("Ano")
todas = em_regiao.groupby("Ano")["Volume (MtCO2e)"].sum()

col1, col2 = st.columns(2)
fig = px.bar(alc, x=alc.index, y="Volume (MtCO2e)", text_auto=True,
             labels={"x": "", "Ano": ""})
fig.update_xaxes(dtick=1)
fig.update_layout(title=dict(text="Volume negociado, América Latina e Caribe (MtCO2e)", font=dict(size=14)))
col1.plotly_chart(fig, use_container_width=True)

fig = px.line(alc, x=alc.index, y="Preço (US$/tCO2e)", markers=True, labels={"Ano": ""})
fig.update_xaxes(dtick=1)
fig.update_layout(title=dict(text="Preço médio, América Latina e Caribe (US$/tCO2e)", font=dict(size=14)))
col2.plotly_chart(fig, use_container_width=True)

participacao = (alc["Volume (MtCO2e)"] / todas.reindex(alc.index) * 100).round(0).astype(int)
st.caption("O painel não tem fonte de preço de crédito voluntário por país: a Ecosystem Marketplace publica por região, e o Brasil "
           "está dentro de América Latina e Caribe. Participação da região no volume reportado por região: " +
           "; ".join(f"{a}: {p}%" for a, p in participacao.items()) + ". "
           "Cada ano vem da edição mais recente que o reporta (" +
           "; ".join(f"{a}: {e}, {t}" for a, (e, t) in alc[["Edição", "Tabela"]].iterrows()) + "). " + c.fonte("EM"))
