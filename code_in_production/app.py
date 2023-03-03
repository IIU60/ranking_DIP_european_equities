import streamlit as st
import app_functions as af
import pandas as pd

st.title('Stoxx600 Equities Dashboard')

with st.form(key='initial_params_form'):
    n_quantiles = st.number_input('Number of Quantiles:', min_value=1, value=10)
    min_stocks_per_date_ratio = st.number_input('Minimum stocks per date ratio:', min_value=0.0, max_value=1.0, value=0.8)
    min_total_dates_ratio = st.number_input('Minimum total dates ratio:', min_value=0.0, max_value=1.0, value=0.8)
    data_directory_filepath = st.text_input('Filepath to data directory:', value=r'C:\Users\hugo.perezdealbeniz\Desktop\Ranking DIP European Equities\ReutersEikon\data\pivoted_data')
    prices_csv_filepath = st.text_input('Filepath to prices csv:', value=r'C:\Users\hugo.perezdealbeniz\Desktop\Ranking DIP European Equities\ReutersEikon\data\Final Data\PriceClose.csv')
    init_form_button = st.form_submit_button()

if 'clean_data_dict' not in st.session_state:
    st.session_state.clean_data_dict = af.filter_data(data_directory_filepath,min_stocks_per_date_ratio,min_total_dates_ratio)[0]
if 'create_custom_indicator' not in st.session_state:
    st.session_state.create_custom_indicator = False

if st.button('Create Multi-factor Indicator'):
    st.session_state.create_custom_indicator = True

if st.session_state.create_custom_indicator == True:
    with st.form('custom_indicator_form'):
        indicator_name = st.text_input('Indicator Name:')
        custom_ratio_weights_df = st.experimental_data_editor(pd.DataFrame(dict(Factor=st.session_state.clean_data_dict.keys(), Weight=0.0, Type='-')),num_rows='dynamic',width=600)
        custom_indicator_form_button = st.form_submit_button()
    
    if custom_indicator_form_button:
        st.balloons()
        custom_indicator_df = af.multi_factor_ranking(custom_ratio_weights_df, st.session_state.clean_data_dict, n_quantiles)
        st.session_state.clean_data_dict[indicator_name] = custom_indicator_df
        st.session_state.create_custom_indicator = False
        st.experimental_rerun()

cols = st.columns(2)
with cols[0]:
    selected_ratio = st.selectbox('Ratio:', st.session_state.clean_data_dict.keys())
with cols[1]:
    type_of_indicator = st.selectbox('Type:', ['alto','bajo'])
log_scale = st.checkbox('Logarithmic Scale:')

ranked_data, labels = af.rank_data(st.session_state.clean_data_dict[selected_ratio], n_quantiles, type_of_indicator)
rents_df = af.get_rents_df(ranked_data, prices_csv_filepath,labels)

graphs_dict = {
    'NAV Absoluto': af.plot_NAV_absoluto,
    'NAV Relativo a Equiponderado': af.plot_NAV_relativo,
    'Rentabilidad Media Anualizada': af.plot_rentabilidad_media,
    'Volatilidad Anualizada':af.plot_volatilidad,
    'Sharpe Ratio':af.plot_sharpe
    }
colors = ["#0068c9","#d7dce6","#7f51b5","#ffd578","#ff902d","#8af0aa","#2db19f","#ffb1b1","#ff3030","#83c9ff",'#000000']

if type_of_indicator == 'bajo':
    colors = colors[::-1]
desired_graphs = st.multiselect('Desired Graphs:',graphs_dict.keys())

for graph in desired_graphs:
    st.plotly_chart(graphs_dict[graph](rents_df,colors,log_scale))