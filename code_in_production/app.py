import streamlit as st
import app_functions as af
import pandas as pd
import matplotlib.pyplot as plt

st.title('Stoxx600 Equities Dashboard')

initial_form = st.form('initial_params_form')

with initial_form:
    n_quantiles = st.number_input('Number of Quantiles:', min_value=1, value=10)
    min_stocks_per_date_ratio = st.number_input('Minimum stocks per date ratio:', min_value=0.0, max_value=1.0, value=0.8)
    min_total_dates_ratio = st.number_input('Minimum total dates ratio:', min_value=0.0, max_value=1.0, value=0.8)
    data_directory_filepath = st.text_input('Filepath to data directory:', value=r'C:\Users\hugo.perezdealbeniz\Desktop\Ranking DIP European Equities\ReutersEikon\data\pivoted_data')
    prices_csv_filepath = st.text_input('Filepath to prices csv:',value=r'C:\Users\hugo.perezdealbeniz\Desktop\Ranking DIP European Equities\ReutersEikon\data\Final Data\PriceClose.csv')
initial_form.form_submit_button()

clean_data_dict = af.filter_data(data_directory_filepath,min_stocks_per_date_ratio,min_total_dates_ratio)[0]

selected_ratio = st.selectbox('Ratio:',clean_data_dict.keys())

rents_dict = af.rank_data(clean_data_dict[selected_ratio],prices_csv_filepath,n_quantiles)

desired_graphs = st.multiselect('Desired Graphs:',['NAV Absoluto','NAV Relativo a Equiponderado','Rentabilidad Media Anualizada', 'Volatilidad Anualizada', 'Sharpe Ratio'])

log_scale = st.checkbox('Logarithmic Scale:')

graphs_dict = {
    #'NAV Absoluto':af.plot_NAV_absoluto,
    'NAV Absoluto': af.plot_NAV_absoluto,
    'NAV Relativo a Equiponderado': af.plot_NAV_relativo,
    'Rentabilidad Media Anualizada': af.plot_rentabilidad_media,
    'Volatilidad Anualizada':af.plot_volatilidad,
    'Sharpe Ratio':af.plot_sharpe}
colors = ["#0068c9","#d7dce6","#7f51b5","#ffd578","#ff902d","#8af0aa","#2db19f","#ffb1b1","#ff3030","#83c9ff",'#000000']

for graph in desired_graphs:
    st.plotly_chart(graphs_dict[graph](rents_dict,colors,log_scale))

