#%%
"""
Mercado de ACCUs (Austrália) a partir do "QCMR data workbook" do Clean Energy Regulator (CER), que acompanha o
Quarterly Carbon Market Report. Licença: Creative Commons Atribuição 4.0 (https://cer.gov.au/about-us/our-policies/copyright).

Página dos relatórios: https://cer.gov.au/markets/reports-and-data/quarterly-carbon-market-reports
O endereço do workbook muda a cada trimestre (ex.: https://cer.gov.au/document/qcmr-data-workbook-june-quarter-2026).

Uso (a partir da raiz do repositório):
    python treat_data/treat_cer.py                 # trata data/raw/cer/qcmr-data-workbook.xlsx
    python treat_data/treat_cer.py URL_DO_WORKBOOK # baixa o workbook para esse arquivo e trata

Abas usadas (cabeçalho na linha 4; "-" para ausência; notas abaixo da tabela):
    Figure 1.1  ACCUs emitidas por tipo de método, por trimestre
    Figure 1.3  projetos registrados por tipo de método, por trimestre
    Figure 1.6  cancelamentos de ACCUs fora do Safeguard (voluntários, de conformidade, governamentais), por trimestre
A Figura 1.7 (preço spot) é só gráfico no workbook, sem tabela.

Saída:
    data/processed/cer_accu.csv (year;quarter;series;category;value)
    data/update_info.csv, linha CER ("Data as at" da Figura 1.1)
"""
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ARQUIVO = Path("data/raw/cer/qcmr-data-workbook.xlsx")
ARQUIVO_ANTIGO = Path("data/archive/DADOS_MANUAIS_abas_arquivadas.xlsx")  # abas Australia_ERF e Australia_ERF_Quarter

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro",
         "Novembro", "Dezembro"]

FIGURAS = {  # aba -> nome da série no painel
    "Figure 1.1": "ACCUs emitidas",
    "Figure 1.3": "Projetos registrados",
    "Figure 1.6": "ACCUs canceladas (fora do Safeguard)",
}

CATEGORIAS = {
    "Vegetation": "Vegetação",
    "Waste": "Resíduos",
    "Savanna fire management": "Manejo de queimadas na savana",
    "Energy efficiency": "Eficiência energética",
    "Industrial fugitives": "Emissões fugitivas industriais",
    "Agriculture": "Agricultura",
    "Agriculture - soil carbon": "Agricultura: carbono no solo",
    "Agriculture - other": "Agricultura: outros",
    "Carbon Capture": "Captura de carbono",
    "Carbon capture": "Captura de carbono",
    "Transport": "Transporte",
    "Facilities": "Instalações",
    "Voluntary cancellations": "Voluntários",
    "Compliance cancellations": "De conformidade",
    "Government cancellations": "Governamentais",
}


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    conteudo = urllib.request.urlopen(req, timeout=120).read()
    if not conteudo.startswith(b"PK"):
        sys.exit(f"{url} não devolveu um arquivo xlsx; arquivo local não alterado.")
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_bytes(conteudo)
    print(f"Baixado: {url} ({len(conteudo):,} bytes)")


def ler_figura(aba):
    """Tabela trimestral de uma aba do workbook, em formato longo, e a data 'Data as at'."""
    bruto = pd.read_excel(ARQUIVO, sheet_name=aba, header=None)
    data_ref = re.search(r"(\d{2}/\d{2}/\d{4})", " ".join(bruto.iloc[:4, 0].astype(str))).group(1)
    linha_cab = bruto.index[bruto.iloc[:, 0].astype(str).str.strip() == "Year"][0]
    df = pd.read_excel(ARQUIVO, sheet_name=aba, header=linha_cab)
    df.columns = [str(c).strip() for c in df.columns]
    # a tabela termina na primeira linha sem trimestre (depois vêm as notas)
    df = df[df["Quarter"].astype(str).str.fullmatch(r"Q[1-4]")].copy()
    df["Year"] = df["Year"].astype(int)

    sem_traducao = [c for c in df.columns if c not in ("Year", "Quarter", "Total", "Annual total") and c not in CATEGORIAS]
    if sem_traducao:
        sys.exit(f"{aba}: categorias novas sem tradução em CATEGORIAS: {sem_traducao}")

    # confere que o total do trimestre é a soma das categorias (o "-" é ausência)
    valores = df.drop(columns=["Year", "Quarter", "Annual total"]).apply(pd.to_numeric, errors="coerce")
    soma = valores.drop(columns="Total").sum(axis=1)
    divergente = (soma - valores["Total"].fillna(0)).abs() > 1
    if divergente.any():
        print(f"  {aba}: trimestres em que o total difere da soma das categorias:",
              df[divergente][["Year", "Quarter"]].values.tolist())

    longo = valores.drop(columns="Total").assign(year=df["Year"], quarter=df["Quarter"])\
        .melt(id_vars=["year", "quarter"], var_name="category", value_name="value").dropna(subset=["value"])
    longo["category"] = longo["category"].map(CATEGORIAS)
    longo["series"] = FIGURAS[aba]
    return longo, data_ref


def validar(cer):
    """Compara com as abas Australia_ERF (mensal) e Australia_ERF_Quarter que estavam na planilha manual."""
    if not ARQUIVO_ANTIGO.exists():
        print(f"Validação não feita: {ARQUIVO_ANTIGO} não existe.")
        return
    total = cer.groupby(["series", "year", "quarter"])["value"].sum().unstack(0)

    def compara(nome, antiga, nova):
        juntos = pd.concat([antiga.rename("antiga"), nova.rename("CER")], axis=1, join="inner").dropna()
        dif = juntos[(juntos["antiga"] - juntos["CER"]).abs() > 0.5]
        print(f"  {nome}: {len(juntos)} trimestres sobrepostos, {len(juntos) - len(dif)} iguais, {len(dif)} diferentes")
        if len(dif):
            dif = dif.assign(diferenca=dif["antiga"] - dif["CER"])
            print("    " + dif.to_string().replace("\n", "\n    "))

    print("Validação contra as abas antigas:")
    mensal = pd.read_excel(ARQUIVO_ANTIGO, sheet_name="Australia_ERF").dropna(subset=["PROJETOS", "CRÉDITOS"], how="all")
    mensal["DATA"] = pd.to_datetime(mensal["DATA"])
    mensal["year"], mensal["quarter"] = mensal["DATA"].dt.year, "Q" + mensal["DATA"].dt.quarter.astype(str)
    trimestral = mensal.groupby(["year", "quarter"])[["PROJETOS", "CRÉDITOS"]].sum()
    compara("Australia_ERF, CRÉDITOS (soma trimestral) x ACCUs emitidas (Fig. 1.1)",
            trimestral["CRÉDITOS"], total["ACCUs emitidas"])
    compara("Australia_ERF, PROJETOS (soma trimestral) x projetos registrados (Fig. 1.3)",
            trimestral["PROJETOS"], total["Projetos registrados"])

    q = pd.read_excel(ARQUIVO_ANTIGO, sheet_name="Australia_ERF_Quarter")
    q["year"] = q["DATA"].str[-4:].astype(int)
    q["quarter"] = "Q" + q["DATA"].str[1]
    q = q.set_index(["year", "quarter"])
    canc = cer[cer["series"] == FIGURAS["Figure 1.6"]].pivot_table(index=["year", "quarter"], columns="category", values="value")
    compara("Australia_ERF_Quarter, TOTAL x cancelamentos totais (Fig. 1.6)", q["TOTAL"], canc.sum(axis=1))
    compara("Australia_ERF_Quarter, VOLUNTÁRIO x cancelamentos voluntários (Fig. 1.6)", q["VOLUNTÁRIO"], canc["Voluntários"])
    compara("Australia_ERF_Quarter, MANDATÓRIO x cancelamentos de conformidade (Fig. 1.6)", q["MANDATÓRIO"], canc["De conformidade"])
    compara("Australia_ERF_Quarter, TOTAL x ACCUs emitidas (Fig. 1.1)", q["TOTAL"], total["ACCUs emitidas"])


def update_cer(save_path="data/processed"):
    partes, datas = [], {}
    for aba in FIGURAS:
        longo, data_ref = ler_figura(aba)
        partes.append(longo)
        datas[aba] = data_ref
        print(f"{aba}: {longo['year'].min()} a {longo['year'].max()}, data de referência {data_ref}")

    cer = pd.concat(partes)[["year", "quarter", "series", "category", "value"]]
    cer.to_csv(f"{save_path}/cer_accu.csv", sep=";", decimal=",", index=False)

    data = datetime.strptime(datas["Figure 1.1"], "%d/%m/%Y")
    last_update_db = pd.read_csv("data/update_info.csv", index_col=0)
    last_update_db.loc["CER"] = f"{MESES[data.month - 1]} {data.day}, {data.year}"
    last_update_db.to_csv("data/update_info.csv")

    validar(cer)
    print("Done CER")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        baixar(sys.argv[1])
    update_cer()
