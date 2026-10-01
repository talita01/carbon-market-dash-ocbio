#%%
"""
Baixa as séries de CBIO da B3 (aplicativo "Séries Históricas") e grava os CSVs
brutos em data/raw/cbio/, no formato que treat_cbio.py espera.

A API da B3 devolve um ano civil por chamada (o ano da data final), por isso o
script baixa ano a ano, do ano da última data já processada até o ano atual.

Uso (a partir da raiz do repositório):
    python treat_data/baixar_cbio.py            # do ano da última data processada até hoje
    python treat_data/baixar_cbio.py 2023       # a partir de um ano específico
"""
import base64
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

API = "https://sistemaswebb3-balcao.b3.com.br/historicalSeriesProxy/historicalSeriesCall"
SERIES = {  # id da série na API da B3 -> nome do arquivo bruto
    4: "aposentadoria_cbio.csv",
    1: "estoque_cbio.csv",
    3: "negociacoes_cbio.csv",
}
SAIDA = Path("data/raw/cbio")


def baixar_ano(id_serie, ano):
    """Retorna as linhas do CSV (texto latin1) de uma série em um ano civil."""
    params = {"language": "pt-br",
              "dateInitial": f"{ano}-01-01",
              "dateFinal": f"{ano}-12-31",
              "asset": "CBIO",
              "idInformation": id_serie}
    codigo = base64.b64encode(json.dumps(params, separators=(",", ":")).encode()).decode()
    req = urllib.request.Request(f"{API}/GetDownload/{codigo}", headers={"User-Agent": "Mozilla/5.0"})
    corpo = urllib.request.urlopen(req, timeout=60).read().decode()
    if len(corpo) <= 2:  # a B3 devolve "" ou "[]" quando não há dados
        return []
    texto = base64.b64decode(corpo).decode("latin1")
    # as linhas de dados terminam em ";" e o cabeçalho não: remove o ";" final
    return [linha.rstrip(";") for linha in texto.splitlines() if linha.strip()]


def baixar_serie(id_serie, anos):
    cabecalho, linhas = None, []
    for ano in anos:
        bloco = baixar_ano(id_serie, ano)
        if not bloco:
            print(f"  {ano}: sem dados")
            continue
        cabecalho = cabecalho or bloco[0]
        linhas += bloco[1:]
        print(f"  {ano}: {len(bloco) - 1} linhas")
    return cabecalho, linhas


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ano_inicial = int(sys.argv[1])
    else:
        ultima = pd.read_csv("data/processed/cbio_data.csv", sep=";", index_col=0, parse_dates=True).index.max()
        ano_inicial = ultima.year

    anos = range(ano_inicial, date.today().year + 1)
    SAIDA.mkdir(parents=True, exist_ok=True)

    for id_serie, arquivo in SERIES.items():
        print(arquivo)
        cabecalho, linhas = baixar_serie(id_serie, anos)
        if cabecalho is None:
            sys.exit(f"Nenhum dado retornado para {arquivo}; arquivo não alterado.")
        with open(SAIDA / arquivo, "w", encoding="latin1", newline="") as f:
            f.write("\n".join([cabecalho] + linhas) + "\n")
