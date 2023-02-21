import eikon as ek
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
start_time = time.time()
ek.set_app_key('89915a3b58874e1599870c6ecc45d6edd6344f8c')

CLOSEPRICE_df,err = ek.get_data(instruments='0#.STOXX',fields=['TR.CLOSEPRICE','TR.CLOSEPRICE.periodenddate'],parameters={'SDate':'20000101','EDate':'20230101','Frq':'FQ','Curn':'EUR','CALCMETHOD':'CLOSE'})
print('data downloaded', time.time()-start_time)
CLOSEPRICE_df.rename(columns={'Period End Date':'Date'},inplace=True)

pivoted_CLOSEPRICE_df = CLOSEPRICE_df.pivot(index='Date',columns='Instrument',values='Close Price')

selected_constituents_df = pivoted_CLOSEPRICE_df.dropna(axis=1)

ranked_df = selected_constituents_df.T

###### HAY QUE HACER DE FORMA VECTORIZADA #########
for date,prices in zip(selected_constituents_df.index,selected_constituents_df.astype(float).values):
    ranked_df[date] = pd.qcut(prices,10,duplicates='drop',labels=False)
ranked_df
print('ranking completed', time.time()-start_time)
#### decil 0 tiene los valores mas bajos y el 9 los mas altos ####
def deciles_lists(df):
    diccionario = {}
    for i in range(10):
        diccionario[f'decil_{i}'] = {}
        for date,ranks in df.items():
            diccionario[f'decil_{i}'][date] = ranks.loc[ranks == i].index.tolist()
    return diccionario

deciles_dict = deciles_lists(ranked_df)

rentabilidad_acciones_df = selected_constituents_df.pct_change()

deciles_df = selected_constituents_df.quantile(q=np.arange(0.1,1,0.1),axis=1)

rentabilidades_dict = {}
rentabilidades_dict['equiponderado'] = {}
for decil,fechas in deciles_dict.items():
    rentabilidades_dict[decil] = {}
    for fecha, stocks in fechas.items():
        rentabilidades_dict[decil][fecha] = rentabilidad_acciones_df.loc[fecha,stocks].mean()
        rentabilidades_dict['equiponderado'][fecha] = rentabilidad_acciones_df.loc[fecha].mean()
print('rentabilidades cacluladas', time.time()-start_time)
plt.style.use('ggplot')

plt.figure(figsize=(20,10))
for decil in rentabilidades_dict:
    plt.plot(list(rentabilidades_dict['decil_0'].keys())[1:],np.array(list(rentabilidades_dict[decil].values())[1:]).cumsum(),label=decil)
plt.xticks(rotation=-45,fontsize=10,ha='left',rotation_mode='anchor')
plt.legend()
plt.tight_layout()
plt.show()
keys = list(rentabilidades_dict.keys())
rentabilidades_medias = [np.mean(list(rentabilidades_dict[decil].values())[1:]) for decil in rentabilidades_dict]

plt.bar(keys,rentabilidades_medias[::-1])
plt.xticks(rotation=-45,ha='left',rotation_mode='anchor')

plt.show()
print('graficos hechos', time.time()-start_time)