# Dashboard – Precificação de Carbono

Este repositório contém todos os códigos, dados e instruções necessários para rodar o dashboard interativo de **Precificação de Carbono**. Além das páginas do dashboard, também estão incluídos os dados brutos, processados e os scripts de tratamento.

---

## Como rodar o dashboard

1. Use **Python 3.12 ou 3.13** (a página do mercado voluntário usa sintaxe que não existe no 3.11) e instale os requisitos:

   ```bash
   pip install -r requirements.txt
   ```

2. Execute a página inicial do dashboard:

   ```bash
   streamlit run "1 Mecanismos _de_Compliance .py"
   ```

---

## Estrutura do Repositório

```
data/
│
├── raw/                # Dados brutos (download direto dos sites; não versionados)
├── processed/          # Dados tratados, prontos para uso no dashboard
│   └── DADOS_MANUAIS.xlsx  # Única planilha que requer atualização manual
├── archive/            # Abas da planilha manual que saíram de uso (aba "Arquivamento" explica cada uma)
├── update_info.csv     # Data de referência de cada base, usada nas legendas
│
pages/                  # Páginas adicionais do dashboard (exceto a principal)
treat_data/             # Scripts de tratamento e atualização de dados
utils/                  # Funções auxiliares utilizadas no dashboard
```

> ⚠️ Apenas o arquivo `DADOS_MANUAIS.xlsx` (em `data/processed/`) deve ser atualizado manualmente. Os demais dados são atualizados por meio dos scripts em `treat_data/`.

A aba **Fontes** da `DADOS_MANUAIS.xlsx` registra, para cada base do painel, a fonte, a URL, a data do dado, a licença e a página que a usa. Atualize-a junto com a base.

| Página | Bases | Script |
|---|---|---|
| 1 Mecanismos de Compliance, 2 Taxa de Carbono | `wb_info.csv`, `wb_time_series.csv` | `treat_wb.py`, `get_lat_long.py` |
| 3 Mercados Regulados | as do Banco Mundial e `rggi_leiloes.csv` | `treat_wb.py`, `treat_rggi.py` |
| 4 CBIO RenovaBio | `cbio_data.csv`, `cbio_negociacoes.csv` | `baixar_cbio.py`, `treat_cbio.py` |
| 5 CORSIA | `corsia_countries.csv`; aba `CORSIA_price` | `treat_corsia.py` |
| 6 Mercado Voluntário | `mvc_credits_info.csv`, `mvc_credits.csv`; abas `EM_Categoria` e `EM_Regiao` | `treat_mvc.py` |
| 7 Mecanismos de Crédito | `wb_crediting_info.csv`, `wb_crediting_issuance.csv`, `wb_cooperative.csv`, `cer_accu.csv` | `treat_wb.py`, `treat_cer.py` |
| 8 Brasil | aba `SBCE_Marcos`, `wb_info.csv`, bases da Berkeley, aba `EM_Regiao` | — |

---

## Como atualizar os dados

Rode todos os scripts a partir da **raiz do repositório** (`python treat_data/...`).

### World Bank

1. Baixe a base no site: [World Bank Carbon Pricing Dashboard](https://carbonpricingdashboard.worldbank.org/about-us#download-data) (link "Download Data in Excel")
2. Substitua o arquivo em: `data/raw/dados_wb.xlsx`
3. Execute:

   ```bash
   python treat_data/treat_wb.py
   ```

   O script trata também as abas de mecanismos de crédito e do Artigo 6.2 (página 7). Ele imprime o que precisa de revisão: anos de início e alcance (nacional/subnacional) derivados para instrumentos novos, e regiões ou faixas de renda que faltarem. Para esses últimos, acrescente a jurisdição em `data/extra_country_info.csv` (colunas `Jurisdiction;Income Group;Region`) e rode de novo.
4. (Caso não vá atualizar o MCV) Rode também:

   ```bash
   python treat_data/get_lat_long.py
   ```

   Isso atualiza os dados de latitude e longitude para visualização no mapa. As coordenadas já buscadas ficam em um cache local (`data/processed/coords.pkl`, não versionado); sem ele, o script busca todos os lugares e leva alguns minutos (1 consulta por segundo).

---

### Mecanismo de Compensação Voluntária (MCV)

1. Baixe a base no site da [Berkeley](https://gspp.berkeley.edu/berkeley-carbon-trading-project/offsets-database)
2. Substitua o arquivo em: `data/raw/dados_mvc.xlsx`
3. Execute:

   ```bash
   python treat_data/treat_mvc.py
   ```
4. Rode:

   ```bash
   python treat_data/get_lat_long.py
   ```

---

### CBIO (Créditos de Descarbonização)

1. Baixe as séries **Aposentadoria**, **Estoque** e **Negociações** da [B3](https://www.b3.com.br/pt_br/b3/sustentabilidade/produtos-e-servicos-esg/credito-de-descarbonizacao-cbio/cbio-consultas/) para `data/raw/cbio/`:

   ```bash
   python treat_data/baixar_cbio.py
   ```

   O script baixa do ano da última data já processada até o ano atual (a API da B3 entrega um ano por vez). Também é possível baixar manualmente no site e salvar os `.csv` com os mesmos nomes.
2. Execute:

   ```bash
   python treat_data/treat_cbio.py
   ```

   > ⚠️ Se uma data aparecer duas vezes, o script mantém a **última** ocorrência (o dado novo substitui o antigo).

---

### CORSIA (ICAO)

1. Na página [CORSIA States for Chapter 3 State Pairs](https://www.icao.int/environmental-protection/CORSIA/Pages/state-pairs.aspx), baixe pelo navegador a edição nova (o site bloqueia downloads automáticos) e salve em `data/raw/corsia/corsia-states-chapter3-AAAA.pdf`, em que `AAAA` é o ano de participação.
2. Execute:

   ```bash
   python treat_data/treat_corsia.py
   ```

   O script confere se o número de Estados extraído é o que o documento declara e para se algum nome não estiver em `data/processed/iso_countries.csv` (acrescente a grafia nova ao arquivo). Os termos da ICAO não permitem redistribuir os PDFs; por isso `data/raw` não é versionada.

---

### Austrália (Clean Energy Regulator)

1. Na página dos [Quarterly Carbon Market Reports](https://cer.gov.au/markets/reports-and-data/quarterly-carbon-market-reports), copie o endereço do "QCMR data workbook" do trimestre mais recente (muda a cada trimestre).
2. Execute, com esse endereço:

   ```bash
   python treat_data/treat_cer.py https://cer.gov.au/document/qcmr-data-workbook-june-quarter-2026
   ```

   Sem endereço, o script trata o arquivo já salvo em `data/raw/cer/qcmr-data-workbook.xlsx`.

---

### RGGI

1. Execute (baixa a tabela [Allowance Prices and Volumes](https://www.rggi.org/auctions/auction-results/prices-volumes) e trata):

   ```bash
   python treat_data/treat_rggi.py
   ```

---

### Demais bases (planilha manual)

1. Edite manualmente a planilha `data/processed/DADOS_MANUAIS.xlsx`:
   - `EM_Categoria` e `EM_Regiao`: tabelas do State of the Voluntary Carbon Market, da [Ecosystem Marketplace](https://www.ecosystemmarketplace.com/publications/), transcritas do PDF. Cada linha registra edição, tabela e página; para cada ano vale a edição mais recente que o reporta.
   - `SBCE_Marcos`: normas e etapas do SBCE, com fonte e URL em cada linha.
   - `CORSIA_price`: sem fonte registrada.
   - Abas que saírem de uso vão para `data/archive/DADOS_MANUAIS_abas_arquivadas.xlsx`, com o motivo na aba `Arquivamento`.

2. Salve a data de referência do **dado** mais recente (e não de download) em `data/update_info.csv` (linhas `EM`, `SBCE` e `CORSIA_PRECO`) e atualize a aba `Fontes`.

---

### Validação das séries novas

`treat_corsia.py`, `treat_cer.py` e `treat_rggi.py` comparam a série nova com a aba antiga correspondente em `data/archive/` no período sobreposto e imprimem as divergências.


