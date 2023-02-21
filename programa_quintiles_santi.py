
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#***IMPORTANTE QUE LA PESTAÑA DE PRECIOS SE LLAME "Precios"***

#PATH DEL ARCHIVO Y LEEMOS EL EXCEL:
path_excel="C:/Users/santiago.royuela/Desktop/Python_Santi/Ranking_Factores_Acciones/plantilla Santi.xlsx"

#CARGAMOS EL EXCEL
excel = pd.ExcelFile(path_excel)
#GUARDAMOS LOS NOMBRES DE LAS HOJAS DEL EXCEL
hojas_excel = excel.sheet_names


#INICIAMOS EL BUCLE PARA LEER TODAS LAS HOJAS DEL EXCEL
n_sheet = 0
for sheet in hojas_excel:

    globals()['%s' % sheet] = pd.read_excel(path_excel, sheet_name= hojas_excel[n_sheet])
    #pd.DataFrame(data)

    #ELIMINAMOS LAS 4 PRIMERAS FILAS
    globals()['%s' % sheet] = (globals()['%s' % sheet]).iloc[4:]

    #NOS QUEDAMOS SOLO CON TICKERS:
    globals()['%s' % sheet] = (globals()['%s' % sheet]).drop((globals()['%s' % sheet]).index[[1,2]])

    #REINICIAMOS EL INDICE:
    (globals()['%s' % sheet]).reset_index(drop=True, inplace=True)

    #RENOMBRAMOS EL NOMBRE DE LAS COLUMNAS COMO LA PRIMERA FILA QUE VAN A SER TICKERS Y FECHA:
    (globals()['%s' % sheet]).columns=(globals()['%s' % sheet]).iloc[0]
    (globals()['%s' % sheet]) = (globals()['%s' % sheet]).drop((globals()['%s' % sheet]).index[[0]])
    #LLAMAMOS A LA PRIMERA COLUMNA FECHA:
    (globals()['%s' % sheet]).rename(columns={'Ticker':'FECHA'}, inplace=True)
    #MODIFICAMOS EL FORMATO PARA QUE SEA UNA FECHA:
    (globals()['%s' % sheet])['FECHA'] = pd.to_datetime((globals()['%s' % sheet])['FECHA'], dayfirst=True)
    #HACEMOS QUE LA COLUMNA FECHA SEA EL INDICE, Y ELIMINAMOS AQUELLAS FILAS QUE NO TENGAN FECHA (SERÁN FILAS VACIAS)
    globals()['%s' % sheet] =  globals()['%s' % sheet].set_index('FECHA')
    globals()['%s' % sheet] = globals()['%s' % sheet].drop(pd.Timestamp('NaT'))

    n_sheet = n_sheet +1

#OBTENEMOS LOS RETORNOS:
retornos = Precios.pct_change()

#CREAMOS EL LOOP DEL REBALANCEO:
#******PARA QUE RATIO QUEREMOS QUE HAGA EL ANALISIS*****:
Ratio_analizado = Ratio

#for row in np.arange(0,len(Ratio_analizado.index)):
#for row in np.arange(0,10):

rets_cuartiles = pd.DataFrame(columns=['FECHA', 'PRIMER_QUINTIL', 'SEGUNDO_QUINTIL', 'TERCER_QUINTIL', 'CUARTO_QUINTIL', 'QUINTO_QUINTIL','EQUIPONDERADO'])

for row in np.arange(1,(len(Ratio_analizado.index)-1)):

    fecha_rets = Ratio_analizado.index

    #creamos los cuartiles:
    ranking = (Ratio_analizado.iloc[row]).rank(pct=True)
    primer_quintil = ranking.loc[(ranking >= 0.80) & (ranking <= 1)]
    segundo_quintil = ranking.loc[(ranking >= 0.60) & (ranking < 0.80)]
    tercer_quintil = ranking.loc[(ranking >= 0.40) & (ranking < 0.60)]
    cuarto_quintil = ranking.loc[(ranking >= 0.20) & (ranking < 0.40)]
    quinto_quintil = ranking.loc[(ranking >= 0) & (ranking < 0.20)]
    equiponderado = ranking.loc[(ranking >= 0) & (ranking <= 1)]

    #COGEMOS SOLO LOS TICKERS
    pri_quintil_tickers = primer_quintil.index.values
    seg_quintil_tickers = segundo_quintil.index.values
    ter_quintil_tickers = tercer_quintil.index.values
    cuar_quintil_tickers = cuarto_quintil.index.values
    quin_quintil_tickers = quinto_quintil.index.values
    equiponderado_tickers = equiponderado.index.values

    #OBTENEMOS EL RETORNO MEDIO DEL CUARTIL
    ret_pri_quintil = ((retornos.iloc[row+1])[pri_quintil_tickers]).mean()
    ret_seg_quintil = ((retornos.iloc[row+1])[seg_quintil_tickers]).mean()
    ret_ter_quintil = ((retornos.iloc[row+1])[ter_quintil_tickers]).mean()
    ret_cuar_quintil = ((retornos.iloc[row+1])[cuar_quintil_tickers]).mean()
    ret_quin_quintil = ((retornos.iloc[row+1])[quin_quintil_tickers]).mean()
    ret_equiponderado = ((retornos.iloc[row+1])[equiponderado_tickers]).mean()

    #OBTENEMOS LA FECHA DE LOS RETORNOS:
    fecha_rets = retornos.index[row+1]

    rets_cuartiles = rets_cuartiles.append({'FECHA': fecha_rets, 'PRIMER_QUINTIL': ret_pri_quintil, 'SEGUNDO_QUINTIL': ret_seg_quintil, 
    'TERCER_QUINTIL': ret_ter_quintil, 'CUARTO_QUINTIL': ret_cuar_quintil, 'QUINTO_QUINTIL': ret_quin_quintil,'EQUIPONDERADO': ret_equiponderado}, ignore_index=True)

#PONEMOS LA FECHA COMO INDICE:
rets_cuartiles = rets_cuartiles.set_index('FECHA')

#HACEMOS QUE LOS RETORNOS SEAN ACUMULADOS, podemos hacer que sean entre dos fechas:
rets_acum = np.exp(rets_cuartiles['2000':'2023'].cumsum())

#GRAFICAMOS LOS RETORNOS
#rets_acum.plot(figsize = (12,8), grid = TRUE)
rets_acum.plot(figsize = (12,8))
plt.show()

#CALCULAMOS EL EXCESO DE RETORNO MENSUAL:

#ENTRE QUE FECHAS QUIERES QUE SEA EL ESTUDIO:
rets_cuartiles_exc = rets_cuartiles

rets_cuartiles_exc['PRIMER_QUINTIL_EXCES_RETURN'] = rets_cuartiles_exc['PRIMER_QUINTIL'] - rets_cuartiles_exc['EQUIPONDERADO']
rets_cuartiles_exc['SEGUNDO_QUINTIL_EXCES_RETURN'] = rets_cuartiles_exc['SEGUNDO_QUINTIL'] - rets_cuartiles_exc['EQUIPONDERADO']
rets_cuartiles_exc['TERCER_QUINTIL_EXCES_RETURN'] = rets_cuartiles_exc['TERCER_QUINTIL'] - rets_cuartiles_exc['EQUIPONDERADO']
rets_cuartiles_exc['CUARTO_QUINTIL_EXCES_RETURN'] = rets_cuartiles_exc['CUARTO_QUINTIL'] - rets_cuartiles_exc['EQUIPONDERADO']
rets_cuartiles_exc['QUINTO_QUINTIL_EXCES_RETURN'] = rets_cuartiles_exc['QUINTO_QUINTIL'] - rets_cuartiles_exc['EQUIPONDERADO']


#CREAMOS EL DICCIONARIO PARA CALCULAR LA MEDIA DE EXCESO DE RETORNO:
exceso_retornos = {'1_QUIN_EXCES_RETURN': rets_cuartiles_exc['PRIMER_QUINTIL_EXCES_RETURN'].mean(),
        '2_QUIN_EXCES_RETURN': rets_cuartiles_exc['SEGUNDO_QUINTIL_EXCES_RETURN'].mean(),
        '3_QUIN_EXCES_RETURN': rets_cuartiles_exc['TERCER_QUINTIL_EXCES_RETURN'].mean(),
        '4_QUIN_EXCES_RETURN': rets_cuartiles_exc['CUARTO_QUINTIL_EXCES_RETURN'].mean(),
        '5_QUIN_EXCES_RETURN': rets_cuartiles_exc['QUINTO_QUINTIL_EXCES_RETURN'].mean()
        }



#GRAFICAMOS CON GRÁFICOS DE BARRAS EL EXCESO DE RETORNO MENSUAL:
names = list(exceso_retornos.keys())
values = list(exceso_retornos.values())
plt.bar(range(len(exceso_retornos)), values, tick_label=names)
plt.show()



#GRAFICAMOS EL EXCESO DE RETORNO ACUMULADO DE CADA QUINTIL, para la fecha que queramos:
rets_acum_exc = np.exp(rets_cuartiles['2000':'2022'].cumsum())
rets_acum_exc = rets_acum_exc[['PRIMER_QUINTIL_EXCES_RETURN','SEGUNDO_QUINTIL_EXCES_RETURN', 'TERCER_QUINTIL_EXCES_RETURN'
,'CUARTO_QUINTIL_EXCES_RETURN',  'QUINTO_QUINTIL_EXCES_RETURN']]

#GRAFICAMOS LOS RETORNOS
#rets_acum.plot(figsize = (12,8), grid = TRUE)
rets_acum_exc.plot(figsize = (12,8))
plt.show()




















