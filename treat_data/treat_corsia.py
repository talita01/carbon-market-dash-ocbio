#%%
"""
Estados participantes do CORSIA por ano, extraídos dos PDFs da ICAO "CORSIA States for Chapter 3 State Pairs"
(uma edição por ano de participação).

Fonte: https://www.icao.int/environmental-protection/CORSIA/Pages/state-pairs.aspx
O site da ICAO devolve HTTP 403 a downloads automáticos (curl, urllib): baixe cada edição pelo navegador e salve em
data/raw/corsia/corsia-states-chapter3-AAAA.pdf, em que AAAA é o ano de participação (o ano da frase
"The following N States will participate in CORSIA from 1 January AAAA").
Os termos da ICAO não permitem redistribuir os PDFs (data/raw não é versionada); o painel publica só a lista de
Estados, citando a edição.

Uso (a partir da raiz do repositório):
    python treat_data/treat_corsia.py

Saída:
    data/processed/corsia_countries.csv  (year;country;ISO;name;edition)
        country: nome como impresso na edição; name: nome usado no painel (o da edição mais recente para o mesmo ISO,
        porque a ICAO mudou grafias, p. ex. "Turkey" para "Türkiye")
    data/update_info.csv, linha ICAO (capa da edição mais recente)
"""
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

PASTA = Path("data/raw/corsia")
ARQUIVO_ANTIGO = Path("data/archive/DADOS_MANUAIS_abas_arquivadas.xlsx")  # aba CORSIA_countries, usada até 2026

MESES = {"January": "Janeiro", "February": "Fevereiro", "March": "Março", "April": "Abril", "May": "Maio",
         "June": "Junho", "July": "Julho", "August": "Agosto", "September": "Setembro", "October": "Outubro",
         "November": "Novembro", "December": "Dezembro"}

# A capa da edição para 2023 não traz data extraível; a tabela de emendas das edições seguintes registra
# "3rd ... 1 August 2022".
EDICAO_SEM_DATA_NA_CAPA = {2023: "3ª edição, publicada em 1º de agosto de 2022"}


def ler_edicao(arquivo):
    """Retorna (ano, n_declarado, capa, estados) de um PDF da ICAO."""
    paginas = [p.extract_text() for p in PdfReader(arquivo).pages]
    texto = "\n".join(paginas)

    frase = re.search(r"The following (\d+)\s+States will participate in CORSIA from 1 January (\d{4})", texto)
    if not frase:
        raise ValueError(f"{arquivo}: frase 'The following N States will participate...' não encontrada")
    n_declarado, ano = int(frase.group(1)), int(frase.group(2))

    capa = re.search(r"(" + "|".join(MESES) + r")\s+(\d{4})", paginas[0].split("Carbon Offsetting")[0])
    capa = f"{MESES[capa.group(1)]}, {capa.group(2)}" if capa else EDICAO_SEM_DATA_NA_CAPA.get(ano, "sem data na capa")

    lista = texto[frase.end():texto.index("– END –")]
    estados = []
    for linha in lista.splitlines():
        linha = linha.strip()
        # descarta o ":" do fim da frase, cabeçalhos de página e números de página
        if not linha or linha == ":" or linha.startswith("ICAO document") or linha.isdigit():
            continue
        estados.append(linha)

    return ano, n_declarado, capa, estados


def validar(corsia):
    """Compara com a aba CORSIA_countries que o painel usava (2021 a 2025), por código ISO."""
    if not ARQUIVO_ANTIGO.exists():
        print(f"Validação não feita: {ARQUIVO_ANTIGO} não existe.")
        return
    antigo = pd.read_excel(ARQUIVO_ANTIGO, sheet_name="CORSIA_countries")
    antigo["country"] = antigo["country"].str.strip()
    iso = pd.read_csv("data/processed/iso_countries.csv", sep=";", index_col=1)["ISO"]
    antigo["ISO"] = antigo["country"].map(iso)
    print("Validação contra a aba antiga CORSIA_countries:")
    print("  nomes da aba antiga sem ISO:", antigo[antigo["ISO"].isnull()]["country"].tolist())
    for ano in sorted(antigo["year"].unique()):
        a = set(antigo[antigo["year"] == ano]["ISO"])
        n = set(corsia[corsia["year"] == ano]["ISO"])
        print(f"  {ano}: aba antiga {len(a)}, ICAO {len(n)}; só na antiga {sorted(a - n)}; só na ICAO {sorted(n - a)}")
    # grafias diferentes para o mesmo ISO fazem um país parecer ter saído quando se agrupa pelo nome
    grafias = antigo.groupby("ISO")["country"].unique()
    print("  ISO com mais de uma grafia na aba antiga:", {k: list(v) for k, v in grafias.items() if len(v) > 1})


def update_corsia(save_path="data/processed"):
    iso = pd.read_csv("data/processed/iso_countries.csv", sep=";", index_col=1)["ISO"]

    linhas, capas = [], {}
    for arquivo in sorted(PASTA.glob("corsia-states-chapter3-*.pdf")):
        ano, n_declarado, capa, estados = ler_edicao(arquivo)
        if int(arquivo.stem[-4:]) != ano:
            raise ValueError(f"{arquivo.name}: o PDF é da lista de {ano}")
        print(f"{ano}: {len(estados)} Estados extraídos; o documento declara {n_declarado}; capa: {capa}")
        if len(estados) != n_declarado:
            raise ValueError(f"{arquivo.name}: extraídos {len(estados)} Estados, o documento declara {n_declarado}")
        capas[ano] = capa
        linhas += [{"year": ano, "country": e, "edition": capa} for e in estados]

    corsia = pd.DataFrame(linhas)
    corsia["ISO"] = corsia["country"].map(iso)
    sem_iso = corsia[corsia["ISO"].isnull()]["country"].unique()
    if len(sem_iso):
        raise ValueError(f"Nomes sem ISO em data/processed/iso_countries.csv (acrescente a grafia): {list(sem_iso)}")

    # nome do painel: o da edição mais recente
    corsia["name"] = corsia["ISO"].map(corsia.sort_values("year").groupby("ISO")["country"].last())

    corsia = corsia[["year", "country", "ISO", "name", "edition"]]
    corsia.to_csv(f"{save_path}/corsia_countries.csv", sep=";", index=False)

    ultimo = max(capas)
    last_update_db = pd.read_csv("data/update_info.csv", index_col=0)
    last_update_db.loc["ICAO"] = f"{capas[ultimo]}; participantes até {ultimo}"
    last_update_db.to_csv("data/update_info.csv")

    validar(corsia)
    print("Done CORSIA")


if __name__ == "__main__":
    update_corsia()
