import streamlit as st
import pandas as pd
import os

# Nome de cada base, como aparece nas legendas; a data vem de data/update_info.csv (mesma chave)
FONTES = {
    "WB": "Banco Mundial, Carbon Pricing Dashboard (dados atualizados em {})",
    "WB_CREDITO": "Banco Mundial, Carbon Pricing Dashboard, mecanismos de crédito (dados atualizados em {})",
    "WB_ARTIGO6": "Banco Mundial, Carbon Pricing Dashboard, acordos do Artigo 6.2 (dados atualizados em {})",
    "MVC": "Berkeley Carbon Trading Project, Voluntary Registry Offsets Database (versão de {})",
    "ICAO": "ICAO, CORSIA States for Chapter 3 State Pairs (edição de {})",
    "EM": "Forest Trends' Ecosystem Marketplace, State of the Voluntary Carbon Market ({})",
    "CER": "Clean Energy Regulator (Austrália), Quarterly Carbon Market Report, licença CC BY 4.0 (dados até {})",
    "RGGI": "RGGI, Allowance Prices and Volumes (último leilão em {})",
    "CORSIA_PRECO": "planilha manual do painel ({})",
    "SBCE": "Planalto, Agência Brasil e Brasil Participativo (consultados em {})",
}


def fonte(*chaves, nota=""):
    """Texto 'Fonte: ...' para a legenda de um gráfico, com a data do dado de cada base."""
    update_info = pd.read_csv("data/update_info.csv", index_col=0)["Last Update"]
    texto = "Fonte: " + "; ".join(FONTES[k].format(update_info[k]) for k in chaves) + "."
    return f"{texto} {nota}".strip()


def sobre_dash(st_location=st,expanded=False):
    with st_location.expander("Sobre o Dashboard", expanded=expanded):

        st_location.subheader("O que é o dashboard?")
        st_location.text("O Dashboard de Instrumentos de Precificação Direta de Carbono do FGV Bioeconomia é uma ferramenta interativa desenvolvida para apoiar formuladores de políticas públicas, pesquisadores, investidores e demais stakeholders. O painel reúne e organiza informações sobre mecanismos de precificação direta de carbono, como taxas e mecanismos de mercado (voluntário e regulado), em diferentes países. Este painel combina dados públicos e fontes internacionais reconhecidas, como o Banco Mundial, o Berkeley Carbon Trading Project, a Organização da Aviação Civil Internacional (ICAO), a Ecosystem Marketplace, o Clean Energy Regulator da Austrália, a RGGI e a B3, com análises e insights do FGV Bioeconomia. Seu objetivo é promover transparência, embasar decisões estratégicas e fomentar o debate sobre o papel da precificação de carbono na transição para uma economia de baixo carbono.")

        st_location.subheader("Como está organizado?")
        st_location.markdown("O conteúdo do dashboard está estruturado de forma temática, começando pelos **mecanismos de compliance** de precificação de carbono, que incluem **taxas de carbono** e **mercados regulados**. Em seguida, uma seção dedicada ao **CBIO (RenovaBio)** e os dados do **CORSIA**, o mecanismo global de compensação de emissões do setor de aviação internacional. Depois, os dados do **mercado voluntário de carbono (MCV)**, com informações sobre créditos emitidos, projetos por escopo e regiões de atuação, e os **mecanismos de crédito e acordos do Artigo 6.2**. Por fim, uma página sobre o **Brasil**: o marco do SBCE e o mercado voluntário no país.")

        st_location.subheader("Fontes")
        st_location.markdown(
            "- **Banco Mundial**, Carbon Pricing Dashboard: taxas de carbono, ETS, mecanismos de crédito e Artigo 6.2 (licença CC BY 4.0).\n"
            "- **Berkeley Carbon Trading Project**, Voluntary Registry Offsets Database: projetos e créditos do mercado voluntário.\n"
            "- **ICAO**, CORSIA States for Chapter 3 State Pairs: países participantes do CORSIA.\n"
            "- **Forest Trends' Ecosystem Marketplace**, State of the Voluntary Carbon Market: preço e volume do mercado voluntário por categoria e região.\n"
            "- **Clean Energy Regulator** (Austrália), Quarterly Carbon Market Report: ACCUs (licença CC BY 4.0).\n"
            "- **RGGI**, Allowance Prices and Volumes: leilões trimestrais.\n"
            "- **B3**, Séries Históricas: CBIO.\n"
            "- **Planalto, Agência Brasil e Brasil Participativo**: marcos do SBCE.\n\n"
            "Cada gráfico traz a fonte e a data do dado na legenda."
        )


def pag_config(file_name):

    page_name = file_name[2:].split('.')[0].replace('_', ' ').title()

    st.logo('data/logo.png', icon_image='data/logo.png',size='large')

    st.set_page_config (
        page_title=page_name,
        layout="wide",
        initial_sidebar_state="expanded"
    )
