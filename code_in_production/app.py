import streamlit as st
import app_functions as af
import plots as pl
import pandas as pd
import custom_calculations as calcs

#import matplotlib.pyplot as plt
st.set_page_config(layout='wide')
st.title('Stoxx600 Equities Dashboard')

with st.sidebar:

    with st.form(key='initial_params_form'):
        n_quantiles = st.number_input('Number of Quantiles:', min_value=1, value=10)
        min_stocks_per_date_ratio = st.number_input('Minimum stocks per date ratio:', min_value=0.0, max_value=1.0, value=0.8)
        min_total_dates_ratio = st.number_input('Minimum total dates ratio:', min_value=0.0, max_value=1.0, value=0.8)
        data_directory_filepath = st.text_input('Filepath to data directory:', value=r'C:\Users\hugo.perezdealbeniz\Desktop\Ranking DIP European Equities\ReutersEikon\data\pivoted_data')
        prices_csv_filepath = st.text_input('Filepath to prices csv:', value=r'C:\Users\hugo.perezdealbeniz\Desktop\Ranking DIP European Equities\ReutersEikon\data\Final Data\PriceClose.csv')
        mask_filepath = st.text_input('Filepath to index constituency mask:', value=r'C:\Users\hugo.perezdealbeniz\Desktop\Ranking DIP European Equities\ReutersEikon\data\PriceClose_vertical\monthly_constituents_filter.csv')
        init_form_button = st.form_submit_button()

    if 'start_app' not in st.session_state:
        st.session_state.start_app = False
        
    if init_form_button:
        st.session_state.clean_data_dict = af.filter_data(fr'{data_directory_filepath}',min_stocks_per_date_ratio,min_total_dates_ratio)[0]
        st.session_state.prices_df = pd.read_csv(fr'{prices_csv_filepath}',index_col=0)
        st.session_state.mask = pd.read_csv(fr'{mask_filepath}',index_col=0)
        st.session_state.start_app = True
        
 
    if 'create_weighted_indicator' not in st.session_state:
        st.session_state.create_weighted_indicator = False
    
    if st.button('Create Multi-factor Indicator'):
        st.session_state.create_weighted_indicator = True
    
    if st.session_state.create_weighted_indicator == True:
        with st.form('weighted_indicator_form'):
            indicator_name = st.text_input('Indicator Name:')
            weighted_ratio_weights_df = st.experimental_data_editor(pd.DataFrame(dict(Factor=st.session_state.clean_data_dict.keys(), Weight=0.0, Type='-')),num_rows='dynamic',width=600)
            weighted_indicator_form_button = st.form_submit_button()
        
        if weighted_indicator_form_button:
            st.success('Created Successfully')
            weighted_indicator_df = af.multi_factor_ranking(weighted_ratio_weights_df, st.session_state.clean_data_dict, n_quantiles)
            st.session_state.clean_data_dict[indicator_name] = weighted_indicator_df
            st.session_state.create_weighted_indicator = False
            st.experimental_rerun()


    if 'create_custom_indicator' not in st.session_state:
        st.session_state.create_custom_indicator = False

    if st.button('Create Custom Indicator'):
        st.session_state.create_custom_indicator = True

    if st.session_state.create_custom_indicator == True:
        with st.form('custom_indicator_form'):
            indicator_name = st.text_input('Indicator Name:')
            user_input = st.text_input('Formula:')
            custom_indicator_form_button = st.form_submit_button()
            calcs.mask = st.session_state.mask
            locals_dict = {k:v for k,v in calcs.__dict__.items() if not k.startswith('__')}
            locals_dict.update(st.session_state.clean_data_dict)
            st.write(locals_dict.keys()) # write docs to screen
        
        if custom_indicator_form_button:
            custom_df = eval(user_input,{},locals_dict)
            st.session_state.clean_data_dict[indicator_name] = custom_df
            st.session_state.create_custom_indicator = False
            st.experimental_rerun()

if st.session_state.start_app == True:
    n_indicators = st.number_input('Number of Indicators:',value=1)

    cols = st.columns(n_indicators)
    for i in range(n_indicators):
        with cols[i]:
            
            selected_ratio = st.selectbox('Ratio:', st.session_state.clean_data_dict.keys(),key=f'ratio_{i}')
            
            type_of_indicator = st.selectbox('Type:', ['alto','bajo'],key=f'type_{i}')
            log_scale = st.checkbox('Logarithmic Scale:',key=f'log_graphs_{i}')
            masked_data = af.apply_mask(st.session_state.clean_data_dict[selected_ratio],st.session_state.mask)
            ranked_data = af.rank_data(masked_data, n_quantiles, type_of_indicator)
            #fig,ax = plt.subplots()
            #ax.plot(ranked_data.notna().sum(axis=1))
            #st.pyplot(fig)
            rents_df = af.get_rents_df(ranked_data, st.session_state.prices_df, n_quantiles,1,1)
            st.write(len(rents_df)/277)
            graphs_dict = {
                'NAV Absoluto': pl.plot_NAV_absoluto,
                'NAV Relativo a Equiponderado': pl.plot_NAV_relativo,
                'Rentabilidad Media Anualizada': pl.plot_rentabilidad_media,
                'Volatilidad Anualizada':pl.plot_volatilidad,
                'Sharpe Ratio':pl.plot_sharpe
                }

            desired_graphs = st.multiselect('Desired Graphs:',graphs_dict.keys(),key=f'desired_graphs_{i}')
        
            for graph in desired_graphs:
                st.plotly_chart(graphs_dict[graph](rents_df, selected_ratio, log_scale=log_scale),True)

else:
    st.warning('Please Submit the data and params form in the sidebar to load the app.')