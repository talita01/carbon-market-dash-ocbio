#%%
import pandas as pd 

def update_cbio(aposentadoria,estoque,negociacoes):

    cbio = pd.read_csv("data/processed/cbio_data.csv",sep=";",decimal=",",index_col=0)
    cbio.index = pd.to_datetime(cbio.index)
    print("CBIO LAST DATE:",cbio.index.max())

    # Aposentadoria e estoque
    aposentadoria["Data"] = pd.to_datetime(aposentadoria["Data"],format="%d/%m/%Y")

    aposentadoria = aposentadoria\
                            .drop(["Quantidade (Parte Obrigada)","Quantidade (Parte Não Obrigada)"],axis=1)\
                            .set_index("Data")\
                            .sort_index()\
                            .rename(columns={"Totalização":"Aposentadoria"})

    estoque["Data"] = pd.to_datetime(estoque["Data"],format="%d/%m/%Y")

    estoque = estoque\
                .drop(estoque.columns[1:-1],axis=1)\
                .set_index("Data")\
                .sort_index()\
                .rename(columns={"Totalização":"Estoque"})
    
    cbio_new = aposentadoria.join(estoque,how="outer")

    cbio = pd.concat([cbio,cbio_new]).sort_index()
    cbio = cbio[~cbio.index.duplicated(keep='last')]
    print("CBIO NEW LAST DATE:",cbio.index.max())

    #Negociacoes
    negociacoes_old = pd.read_csv("data/processed/cbio_negociacoes.csv",sep=";",decimal=",",index_col=0)
    negociacoes_old.index = pd.to_datetime(negociacoes_old.index)
    print("NEGOCIACOES LAST DATE:",negociacoes_old.index.max())

    negociacoes["Data"] = pd.to_datetime(negociacoes["Data"],format="%d/%m/%Y")

    negociacoes = negociacoes.rename(columns={"Total": "Qtde Negociada"})\
                                .drop(['Qtde (Parte Obrigada)',
                                'Qtde (Parte Não Obrigada) Cliente',
                                'Qtde (Parte Não Obrigada) Inst. Financeira',
                                'Qtde (Parte Não Obrigada) Total',],axis=1)\
                                .set_index("Data")\
                                .sort_index()
    
    negociacoes = pd.concat([negociacoes_old,negociacoes]).sort_index()
    negociacoes = negociacoes[~negociacoes.index.duplicated(keep='last')]
    print("NEGOCIACOES NEW LAST DATE:",negociacoes.index.max())
    
    negociacoes.to_csv("data/processed/cbio_negociacoes.csv",sep=";",decimal=",")
    cbio.to_csv("data/processed/cbio_data.csv",sep=";",decimal=",")



if __name__ == "__main__":
    aposentadoria = pd.read_csv('data/raw/cbio/aposentadoria_cbio.csv',sep=";",encoding='latin1',decimal=",",thousands=".")
    estoque = pd.read_csv('data/raw/cbio/estoque_cbio.csv',sep=";",encoding='latin1',decimal=",",thousands=".")
    negociacoes = pd.read_csv('data/raw/cbio/negociacoes_cbio.csv',sep=";",encoding='latin1',decimal=",",thousands=".")

    update_cbio(aposentadoria,estoque,negociacoes)




#ADICIONA DADOS 2020 (baixado separadamentes)
# aposentadoria = pd.read_csv('data/raw/aposentadoria_cbio.csv',sep=";",encoding='latin1',decimal=",",thousands=".")
# aposentadoria2020 = pd.read_csv('data/raw/aposentadoria2020.csv',sep=";")

# aposentadoria2020["Data"] = pd.to_datetime(aposentadoria2020["Data"],format="%d/%m/%Y")

# aposentadoria2020 = aposentadoria2020\
#                         .dropna(axis=1,how='all')\
#                         .set_index("Data")\
#                         .sort_index()\
#                         .rename(columns={"Quantidade":"Aposentadoria"})

# aposentadoria["Data"] = pd.to_datetime(aposentadoria["Data"],format="%d/%m/%Y")

# aposentadoria = aposentadoria\
#                         .drop(["Quantidade (Parte Obrigada)","Quantidade (Parte Não Obrigada)"],axis=1)\
#                         .set_index("Data")\
#                         .sort_index()\
#                         .rename(columns={"Totalização":"Aposentadoria"})

# aposentadoria = pd.concat([aposentadoria,aposentadoria2020]).sort_index()

# # ESTOQUE
# estoque = pd.read_csv('data/raw/estoque_cbio.csv',sep=";",encoding='latin1',decimal=",",thousands=".")
# estoque_2020 = pd.read_csv('data/raw/estoque2020.csv',sep=";",decimal=",",thousands=".")

# estoque_2020["Data"] = pd.to_datetime(estoque_2020["Data"],format="%d/%m/%Y")

# estoque_2020 = estoque_2020\
#                         .drop(["Emissor","Parte Obrigada","Parte Não Obrigada"],axis=1)\
#                         .set_index("Data")\
#                         .sort_index()\
#                         .rename(columns={"Totalização":"Estoque"})


# estoque["Data"] = pd.to_datetime(estoque["Data"],format="%d/%m/%Y")

# estoque = estoque\
#             .drop(estoque.columns[1:-1],axis=1)\
#             .set_index("Data")\
#             .sort_index()\
#             .rename(columns={"Totalização":"Estoque"})

# estoque = pd.concat([estoque,estoque_2020]).sort_index()

# cbio = aposentadoria.join(estoque,how="outer")
# cbio.to_csv("data/processed/cbio_data.csv",sep=";",decimal=",")


# #%%
# negociacoes = pd.read_csv('data/raw/negociacoes_cbio.csv',sep=";",encoding='latin1',decimal=",",thousands=".")
# negociacoes_2020 = pd.read_csv('data/raw/negociacoes_2020.csv',sep=";",decimal=",",thousands=".")

# negociacoes["Data"] = pd.to_datetime(negociacoes["Data"],format="%d/%m/%Y")

# negociacoes = negociacoes.rename(columns={"Total": "Qtde Negociada"})\
#                             .drop(['Qtde (Parte Obrigada)',
#                             'Qtde (Parte Não Obrigada) Cliente',
#                             'Qtde (Parte Não Obrigada) Inst. Financeira',
#                             'Qtde (Parte Não Obrigada) Total',],axis=1)\
#                             .set_index("Data")\
#                             .sort_index()

# negociacoes_2020["Data"] = pd.to_datetime(negociacoes_2020["Data"],format="%d/%m/%Y")
# negociacoes_2020 = negociacoes_2020\
#                             .set_index("Data")\
#                             .sort_index()

# negociacoes = pd.concat([negociacoes,negociacoes_2020])
# negociacoes.to_csv("data/processed/cbio_negociacoes.csv",sep=";",decimal=",")