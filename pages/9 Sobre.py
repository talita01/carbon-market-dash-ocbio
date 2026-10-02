import os 
import streamlit as st
import pandas as pd
from utils import components as c

############################## Configurações da página (inicio) ##############################
c.pag_config(os.path.basename(__file__))
############################## Configurações da página (fim) ##############################


st.markdown(""" 
### **Dashboard: Precificação de Carbono**  

A precificação de carbono é uma ferramenta essencial para enfrentar as mudanças climáticas, pois atribui um custo às emissões de gases de efeito estufa (GEE), incentivando sua redução por parte de governos, empresas e consumidores. Ao tornar visível o custo ambiental do carbono, esses instrumentos ajudam a orientar investimentos, promover inovação tecnológica e viabilizar o cumprimento das metas climáticas.   

Existem diferentes tipos de instrumentos de precificação que variam em estrutura e abrangência. Este painel tem como foco os instrumentos de precificação direta, como taxas sobre carbono, sistemas de comércio de emissões (ETS) e mecasnismos de crédito de carbono, que estabelecem um preço explícito por tonelada de CO₂ emitida e têm papel central nas estratégias nacionais e internacionais de descarbonização.              
            """)


dados = [
    ["Direto", "",
      "Taxa de carbono", 
     "Preço fixo por tonelada de CO₂ emitida.", "Canadá, Colômbia, África do Sul"],

    ["Direto", "Aplica um preço explícito por tonelada de CO₂ emitida.",
     "Sistema de comércio de emissões (ETS)", 
     "Limite total de emissões; entidades compram e vendem permissões negociáveis.", 
     "EU ETS, RGGI (EUA), China ETS"],

    ["Direto", "",
     "Mecanismos de crédito de carbono", 
     "Créditos gerados por atividades que evitam ou removem emissões; podem ser vendidos.", 
     "Voluntary Carbon Market, Artigo 6.4 (Acordo de Paris)"],

    ["Indireto", 
     "Instrumentos que alteram os preços de produtos associados às emissões de carbono, mas sem vinculação proporcional às emissões geradas. Embora adotados por razões econômicas ou sociais, criam um sinal indireto de preço do carbono.", 
     "-", "-", 
     "• Impostos sobre combustíveis (gasolina, diesel)\n• Impostos sobre produtos energéticos\n• Subsídios aos combustíveis fósseis que reduzem artificialmente seu custo"],

    ["Interno", "",
    #  "Utilizado voluntariamente por empresas para incorporar o custo do carbono em suas decisões estratégicas e operacionais.", 
     "Preço sombra", 
     "Valor hipotético por tonelada de CO₂ usado em decisões internas de investimento.", 
     "-"],

    ["Interno", 
     "Utilizado voluntariamente por empresas para incorporar o custo do carbono em suas decisões estratégicas e operacionais.", 
    "Taxa interna de carbono", 
     "Cobrança interna por emissões entre unidades da empresa, com fundos reinvestidos em mitigação.", 
     "-"],

     ["Interno", "",
    #  "Utilizado voluntariamente por empresas para incorporar o custo do carbono em suas decisões estratégicas e operacionais.", 
     "Preço implícito", 
     "Custo real por tonelada de CO₂ evitada via ações já realizadas pela organização.", 
     "-"],
]

colunas = ["Tipo", "Descrição", "Instrumento", "Descrição do Instrumento", "Exemplos"]
df = pd.DataFrame(dados, columns=colunas).set_index(['Tipo', 'Descrição'])

# Estilo básico sem aplicar funções (para evitar KeyError)
styled_df = df.style.set_properties(**{
    'text-align': 'left',
    'white-space': 'pre-wrap'
}).set_table_styles([{
    'selector': 'th',
    'props': [('text-align', 'left')]
}])


html = df.style.to_html()

style_str = [i for i in html.split('"') if 'level0_col1' in i ][0][:-len("level0_col1")-1]
table_html ="""<style type="text/css"> 
    #T_cea8f_level1_row0  {
        border-bottom: 1px solid transparent;
    }
    #T_cea8f_level1_row1  {
        border-bottom: 1px solid transparent;
    }
    #T_cea8f_level1_row4  {
        border-bottom: 1px solid transparent;
    }
    #T_cea8f_level1_row5  {
        border-bottom: 1px solid transparent;
    }
</style> 
<table id="T_cea8f"> <thead> <tr>  <th class="index_name level0" >Tipo</th> <th class="index_name level1" >Descrição</th> <th id="T_cea8f_level0_col0" class="col_heading level0 col0" >Instrumento</th> <th id="T_cea8f_level0_col1" class="col_heading level0 col1" >Descrição do Instrumento</th> <th id="T_cea8f_level0_col2" class="col_heading level0 col2" >Exemplos</th> </tr> </thead> <tbody> <tr> <th id="T_cea8f_level0_row0" class="row_heading level0 row0" rowspan="3">Direto</th> <th id="T_cea8f_level1_row0" class="row_heading level1 row0" ></th> <td id="T_cea8f_row0_col0" class="data row0 col0" >Taxa de carbono</td> <td id="T_cea8f_row0_col1" class="data row0 col1" >Preço fixo por tonelada de CO₂ emitida.</td> <td id="T_cea8f_row0_col2" class="data row0 col2" >Canadá, Colômbia, África do Sul</td> </tr> <tr> <th id="T_cea8f_level1_row1" class="row_heading level1 row1" >Aplica um preço explícito por tonelada de CO₂ emitida.</th> <td id="T_cea8f_row1_col0" class="data row1 col0" >Sistema de comércio de emissões (ETS)</td> <td id="T_cea8f_row1_col1" class="data row1 col1" >Limite total de emissões; entidades compram e vendem permissões negociáveis.</td> <td id="T_cea8f_row1_col2" class="data row1 col2" >EU ETS, RGGI (EUA), China ETS</td> </tr> <tr> <th id="T_cea8f_level1_row2" class="row_heading level1 row2" ></th> <td id="T_cea8f_row2_col0" class="data row2 col0" >Mecanismos de crédito de carbono</td> <td id="T_cea8f_row2_col1" class="data row2 col1" >Créditos gerados por atividades que evitam ou removem emissões; podem ser vendidos.</td> <td id="T_cea8f_row2_col2" class="data row2 col2" >Voluntary Carbon Market, Artigo 6.4 (Acordo de Paris)</td> </tr> <tr> <th id="T_cea8f_level0_row3" class="row_heading level0 row3" >Indireto</th> <th id="T_cea8f_level1_row3" class="row_heading level1 row3" >Instrumentos que alteram os preços de produtos associados às emissões de carbono, mas sem vinculação proporcional às emissões geradas. Embora adotados por razões econômicas ou sociais, criam um sinal indireto de preço do carbono.</th> <td id="T_cea8f_row3_col0" class="data row3 col0" >-</td> <td id="T_cea8f_row3_col1" class="data row3 col1" >-</td> <td id="T_cea8f_row3_col2" class="data row3 col2" >• Impostos sobre combustíveis (gasolina, diesel) • Impostos sobre produtos energéticos • Subsídios aos combustíveis fósseis que reduzem artificialmente seu custo</td> </tr> <tr> <th id="T_cea8f_level0_row4" class="row_heading level0 row4" rowspan="3">Interno</th> <th id="T_cea8f_level1_row4" class="row_heading level1 row4" ></th> <td id="T_cea8f_row4_col0" class="data row4 col0" >Preço sombra</td> <td id="T_cea8f_row4_col1" class="data row4 col1" >Valor hipotético por tonelada de CO₂ usado em decisões internas de investimento.</td> <td id="T_cea8f_row4_col2" class="data row4 col2" >-</td> </tr> <tr> <th id="T_cea8f_level1_row5" class="row_heading level1 row5" >Utilizado voluntariamente por empresas para incorporar o custo do carbono em suas decisões estratégicas e operacionais.</th> <td id="T_cea8f_row5_col0" class="data row5 col0" >Taxa interna de carbono</td> <td id="T_cea8f_row5_col1" class="data row5 col1" >Cobrança interna por emissões entre unidades da empresa, com fundos reinvestidos em mitigação.</td> <td id="T_cea8f_row5_col2" class="data row5 col2" >-</td> </tr> <tr> <th id="T_cea8f_level1_row6" class="row_heading level1 row6" ></th> <td id="T_cea8f_row6_col0" class="data row6 col0" >Preço implícito</td> <td id="T_cea8f_row6_col1" class="data row6 col1" >Custo real por tonelada de CO₂ evitada via ações já realizadas pela organização.</td> <td id="T_cea8f_row6_col2" class="data row6 col2" >-</td> </tr> </tbody> </table>""".replace("T_a5fc4", style_str)


st.write(table_html.replace("T_cea8f", style_str),unsafe_allow_html=True)

st.link_button("Saiba mais sobre a FGV Agro",
               url="https://agro.fgv.br/")
