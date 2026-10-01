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
├── raw/                # Dados brutos (download direto dos sites)
├── processed/          # Dados tratados, prontos para uso no dashboard
│   └── DADOS_MANUAIS.xlsx  # Única planilha que requer atualização manual
│
pages/                  # Páginas adicionais do dashboard (exceto a principal)
treat_data/             # Scripts de tratamento e atualização de dados
utils/                  # Funções auxiliares utilizadas no dashboard
```

> ⚠️ Apenas o arquivo `DADOS_MANUAIS.xlsx` (em `data/processed/`) deve ser atualizado manualmente. Os demais dados são atualizados por meio dos scripts em `treat_data/`.

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

   O script imprime o que precisa de revisão: anos de início e alcance (nacional/subnacional) derivados para instrumentos novos, e regiões ou faixas de renda que faltarem. Para esses últimos, acrescente a jurisdição em `data/extra_country_info.csv` (colunas `Jurisdiction;Income Group;Region`) e rode de novo.
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

### Demais bases

1. Edite manualmente a planilha:
  `data/processed/DADOS_MANUAIS.xlsx`

2. Salve a data de referência do **dado** mais recente (e não de download) em:
  `data/update_info.csv`


