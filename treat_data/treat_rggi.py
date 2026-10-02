#%%
"""
Resultados dos leilões trimestrais da RGGI (Regional Greenhouse Gas Initiative), lidos da tabela oficial
"Allowance Prices and Volumes": https://www.rggi.org/auctions/auction-results/prices-volumes

A página não oferece arquivo para download nem licença aberta ("© RGGI 2026"); os dados são citados no painel.
A tabela HTML é lida com expressões regulares da biblioteca padrão (colunas Auction, Date, Quantity Offered,
CCR Sold, Quantity Sold, Clearing Price, Total Proceeds; "--" em CCR Sold nos leilões sem reserva de contenção de custos).
Entre 2009 e 2011 a tabela traz também leilões de licenças de safra futura ("Auction 3 (Future)" etc.), no mesmo dia
dos leilões regulares; nessas datas o Total Proceeds da linha regular soma as duas vendas.

Uso (a partir da raiz do repositório):
    python treat_data/treat_rggi.py            # baixa a página para data/raw/rggi/ e trata
    python treat_data/treat_rggi.py --local    # trata a página já baixada

Saída:
    data/processed/rggi_leiloes.csv (auction;future;date;quantity_offered;ccr_sold;quantity_sold;clearing_price;total_proceeds)
        future: True nos leilões de licenças de safra futura
        quantidades em licenças (short tons de CO2), preço em US$/licença, receita em US$
    data/update_info.csv, linha RGGI (data do último leilão)
"""
import html
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

URL = "https://www.rggi.org/auctions/auction-results/prices-volumes"
ARQUIVO = Path("data/raw/rggi/prices-volumes.html")
ARQUIVO_ANTIGO = Path("data/archive/DADOS_MANUAIS_abas_arquivadas.xlsx")  # aba RGGI_USD_Volume

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro",
         "Novembro", "Dezembro"]
COLUNAS = {"Auction": "auction", "Date": "date", "Quantity Offered": "quantity_offered", "CCR Sold": "ccr_sold",
           "Quantity Sold": "quantity_sold", "Clearing Price": "clearing_price", "Total Proceeds": "total_proceeds"}


def baixar():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    pagina = urllib.request.urlopen(req, timeout=60).read()
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_bytes(pagina)
    print(f"Baixado: {URL} ({len(pagina):,} bytes)")


def _texto(celula):
    return html.unescape(re.sub(r"<[^>]+>", " ", celula)).strip()


def ler_tabela(pagina):
    tabelas = re.findall(r"<table.*?</table>", pagina, flags=re.S)
    if len(tabelas) != 1:
        sys.exit(f"Esperava uma tabela na página, encontrei {len(tabelas)}; o layout mudou.")
    cabecalho = [_texto(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", tabelas[0], flags=re.S)]
    if cabecalho != list(COLUNAS):
        sys.exit(f"Colunas inesperadas: {cabecalho}")
    linhas = []
    for tr in re.findall(r"<tr>(.*?)</tr>", tabelas[0].split("<tbody>")[1], flags=re.S):
        celulas = [_texto(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
        if celulas:
            linhas.append(celulas)
    df = pd.DataFrame(linhas, columns=list(COLUNAS.values()))

    df.insert(1, "future", df["auction"].str.contains("(Future)", regex=False))
    df["auction"] = df["auction"].str.extract(r"(\d+)", expand=False).astype(int)
    df["date"] = pd.to_datetime(df["date"])
    for col in ["quantity_offered", "ccr_sold", "quantity_sold", "clearing_price", "total_proceeds"]:
        df[col] = pd.to_numeric(df[col].str.replace(r"[$,]", "", regex=True).replace("--", np.nan))
    return df.sort_values(["date", "future"]).reset_index(drop=True)


def validar(rggi):
    """Compara com a aba RGGI_USD_Volume (trimestral, set/2008 a jun/2022), pelo mês do leilão."""
    if not ARQUIVO_ANTIGO.exists():
        print(f"Validação não feita: {ARQUIVO_ANTIGO} não existe.")
        return
    antigo = pd.read_excel(ARQUIVO_ANTIGO, sheet_name="RGGI_USD_Volume")
    antigo["mes"] = pd.to_datetime(antigo["DATA"]).dt.to_period("M")
    # a coluna RECEITA da aba é fórmula (VOLUME x US$) sem valor gravado; recalculada aqui
    antigo["RECEITA"] = antigo["VOLUME"] * antigo["US$"]
    novo = rggi[~rggi["future"]].assign(mes=rggi["date"].dt.to_period("M"))
    juntos = antigo.merge(novo, on="mes", how="left")
    print("Validação contra a aba antiga RGGI_USD_Volume:")
    print(f"  {len(antigo)} trimestres na aba antiga; {juntos['auction'].notnull().sum()} com leilão no mesmo mês")
    for antiga, nova, tol in [("US$", "clearing_price", 0.005), ("VOLUME", "quantity_sold", 0.5),
                              ("RECEITA", "total_proceeds", 1)]:
        dif = juntos[(juntos[antiga] - juntos[nova]).abs() > tol]
        print(f"  {antiga} x {nova}: {len(juntos) - len(dif)} iguais, {len(dif)} diferentes")
        if len(dif):
            print("    " + dif[["DATA", "auction", antiga, nova]].to_string(index=False).replace("\n", "\n    "))


def update_rggi(save_path="data/processed"):
    rggi = ler_tabela(ARQUIVO.read_text(encoding="utf-8"))
    print(f"{len(rggi)} linhas ({(~rggi['future']).sum()} leilões regulares, {rggi['future'].sum()} de safra futura), "
          f"de {rggi['date'].min().date()} a {rggi['date'].max().date()}")

    # a receita deve ser quantidade vendida x preço; nas datas com leilão de safra futura soma as duas vendas
    venda = rggi["quantity_sold"] * rggi["clearing_price"]
    venda_dia = venda.groupby(rggi["date"]).transform("sum")
    calc = ~rggi["future"] & ((venda - rggi["total_proceeds"]).abs() > 1) & ((venda_dia - rggi["total_proceeds"]).abs() > 1)
    print("Leilões em que a receita difere de quantidade vendida x preço:", rggi[calc]["auction"].tolist())

    rggi.to_csv(f"{save_path}/rggi_leiloes.csv", sep=";", decimal=",", index=False, date_format="%Y-%m-%d")

    ultimo = rggi["date"].max()
    last_update_db = pd.read_csv("data/update_info.csv", index_col=0)
    last_update_db.loc["RGGI"] = f"{MESES[ultimo.month - 1]} {ultimo.day}, {ultimo.year}"
    last_update_db.to_csv("data/update_info.csv")

    validar(rggi)
    print("Done RGGI")


if __name__ == "__main__":
    if "--local" not in sys.argv:
        baixar()
    update_rggi()
