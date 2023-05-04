import streamlit as st
import app_functions as af
import plots as pl
import pandas as pd
import os
import custom_calculations as calcs
from quantstats.reports import html as qs_html

st.set_page_config(layout='wide')
st.title('Stoxx600 Equities Dashboard')

if 'start_app' not in st.session_state:
    st.session_state.start_app = False

with st.sidebar:

    with st.form(key='initial_params_form'):
        n_quantiles = st.number_input('Number of Quantiles:', min_value=1, value=10)
        min_stocks_per_date_ratio = st.number_input('Minimum stocks per date ratio:', min_value=0.0, max_value=1.0, value=0.8)
        min_total_dates_ratio = st.number_input('Minimum total dates ratio:', min_value=0.0, max_value=1.0, value=0.8)
        data_directory_filepath = st.text_input('Filepath to data directory:',key='data_fp', value=r'Z:\Interés Departamental\Model Portfolio\Hugo\Ranking DIP European Equities\copia 12-04-2023\data\vertical_dowload_files')
        prices_csv_filepath = st.text_input('Filepath to prices csv:',key='prices_fp', value=r'Z:\Interés Departamental\Model Portfolio\Hugo\Ranking DIP European Equities\copia 12-04-2023\data\vertical_dowload_files\PriceClose.csv')
        with st.expander('Index Constituency Filtering'):
            mask_filepath = st.text_input('Filepath to index constituency mask:',key='mask_fp', value=r'Z:\Interés Departamental\Model Portfolio\Hugo\Ranking DIP European Equities\copia 12-04-2023\data\PriceClose_vertical\monthly_constituents_filter.csv')
            expected_stocks_per_date = st.number_input('Expexted stocks per date:',value=600,min_value=0)
        init_form_button = st.form_submit_button()
        
    if init_form_button:
        st.session_state.prices_df = af.read_and_sort_data(fr'{prices_csv_filepath}')
        if mask_filepath.lower() == 'none':
            st.session_state.mask = None
        else:
            st.session_state.mask = af.read_and_sort_data(fr'{mask_filepath}')
        st.session_state.clean_data_dict,st.session_state.bad_dfs = af.filter_data(
            fr'{data_directory_filepath}',min_stocks_per_date_ratio,min_total_dates_ratio,expected_stocks_per_date,st.session_state.mask)
        st.warning(f'Rejected Data:\n{list(st.session_state.bad_dfs.keys())}')
        st.session_state.start_app = True
        

if st.session_state.start_app == True:

    with st.sidebar:
        if 'create_weighted_indicator' not in st.session_state:
            st.session_state.create_weighted_indicator = False
        if st.button('Create Multi-factor Indicator'):
            st.session_state.create_weighted_indicator = True
        if st.session_state.create_weighted_indicator == True:
            with st.form('weighted_indicator_form'):
                weighted_indicator_name = st.text_input('Indicator Name:')
                weighted_ratio_weights_df = st.experimental_data_editor(pd.DataFrame(dict(Factor=st.session_state.clean_data_dict.keys(), Weight=0.0, Type='-')),width=600)
                weighted_indicator_form_button = st.form_submit_button()
            if weighted_indicator_form_button:
                weighted_indicator_df = af.multi_factor_ranking(weighted_ratio_weights_df, st.session_state.clean_data_dict, n_quantiles,st.session_state.mask)
                st.session_state.clean_data_dict[weighted_indicator_name] = weighted_indicator_df
                st.success('Created Successfully')
                st.session_state.create_weighted_indicator = False


        if 'create_custom_indicator' not in st.session_state:
            st.session_state.create_custom_indicator = False
        if st.button('Create Custom Indicator'):
            st.session_state.create_custom_indicator = True
        if st.session_state.create_custom_indicator == True:
            with st.form('custom_indicator_form'):
                custom_indicator_name = st.text_input('Indicator Name:')
                user_input = st.text_input('Formula:')
                custom_indicator_form_button = st.form_submit_button()
                
                calcs.mask = st.session_state.mask
                calcs_dict = {k:v for k,v in calcs.__dict__.items() if not k.startswith('__') and k not in ['ta','pd','apply_mask','mask']}
                locals_dict = calcs_dict.copy()
                locals_dict.update(st.session_state.clean_data_dict)
                docstrings = {k:v.__doc__ for k, v in calcs_dict.items()}
                
                with st.expander('Available Functions documentation'):
                    for key, value in docstrings.items():
                        st.markdown(f"**{key}**")
                        st.markdown(value)
            if custom_indicator_form_button:
                custom_df = eval(user_input,{'__builtins__':{}},locals_dict)
                st.session_state.clean_data_dict[custom_indicator_name] = custom_df
                st.success('Created Successfully')
                st.session_state.create_custom_indicator = False


        if 'download_indicator' not in st.session_state:
            st.session_state.download_indicator = False
        if st.button('Download Indicator'):
            st.session_state.download_indicator = True
        if st.session_state.download_indicator == True:
            with st.form('download_indicator_form'):
                indicator_to_download = st.selectbox('Indicator:',options=st.session_state.clean_data_dict.keys())
                download_indicator_name = st.text_input('Name:')
                download_indicator_form_button = st.form_submit_button('Download')
            if download_indicator_form_button:
                if f'{download_indicator_name}.csv' in os.listdir(data_directory_filepath):
                    i = 0
                    while f'{download_indicator_name}.csv' in os.listdir(data_directory_filepath):
                        download_indicator_name = f'{download_indicator_name.split("(")[0]}({i})'
                        i += 1
                    st.warning(f'File already existed. Saving as:{download_indicator_name}')
                st.session_state.clean_data_dict[indicator_to_download].to_csv(fr'{data_directory_filepath}\{download_indicator_name}.csv')
                st.success('Downloaded Successfully')
                st.session_state.download_indicator = False
            
    
    n_indicators = st.number_input('Number of Indicators:',value=1)

    cols = st.columns(n_indicators)
    for i in range(n_indicators):
        with cols[i]:
            selected_ratio = st.selectbox('Ratio:', st.session_state.clean_data_dict.keys(),key=f'ratio_{i}')
            
            subcol1,subcol2 = st.columns(2)
            with subcol1:       
                type_of_indicator = st.selectbox('Type:', ['high','low'],key=f'type_{i}')

            print(selected_ratio)
            masked_data = af.apply_mask(st.session_state.clean_data_dict[selected_ratio],st.session_state.mask)
            ranked_data = af.rank_data(masked_data, n_quantiles, type_of_indicator)
            returns_df = af.get_returns(ranked_data, st.session_state.prices_df, n_quantiles,1,1)
            
            with subcol2:
                st.markdown('##')
                with st.expander('Date Range'):
                    start_date = st.date_input('Start Date',value=(index_list:=returns_df.index.to_list())[0])
                    end_date = st.date_input('End Date',value=index_list[-1])
            subcol3,subcol4 = st.columns(2)
            with subcol3:       
                log_scale = st.checkbox('Logarithmic Scale:',key=f'log_graphs_{i}')
            with subcol4:
                notna_graph = st.checkbox('Show Non-missing Values Graph',key=f'notna_graph_{i}')
            
            if notna_graph:
                st.write(len(returns_df)/277)
                st.plotly_chart(pl.notna_plot(ranked_data),True)
            graphs_dict = {
                'NAV Absoluto': pl.plot_NAV_absoluto,
                'NAV Relativo a Equiponderado': pl.plot_NAV_relativo,
                'Rentabilidad Media Anualizada': pl.plot_rentabilidad_media,
                'Volatilidad Anualizada':pl.plot_volatilidad,
                'Sharpe Ratio':pl.plot_sharpe
                }

            desired_graphs = st.multiselect('Desired Graphs:',graphs_dict.keys(),key=f'desired_graphs_{i}')

            for graph in desired_graphs:
                st.plotly_chart(graphs_dict[graph](returns_df.loc[start_date:end_date], selected_ratio, log_scale=log_scale),True,config=pl.config)
            
            if f'download_tearsheet_{i}' not in st.session_state:
                st.session_state[f'download_tearsheet_{i}'] = False
            if st.button('Create Tearsheet',key=f'tearsheet_button_{i}'):
                st.session_state[f'download_tearsheet_{i}'] = True
            if st.session_state[f'download_tearsheet_{i}'] == True:
                with st.form(f'download_tearsheet_form_{i}'):
                    quantile = st.selectbox(label='Quantile:',options=returns_df.columns)
                    match_date_range = st.checkbox('Match Date Range')
                    download_tearsheet_form_button = st.form_submit_button('Download')
                if download_tearsheet_form_button:
                    tearsheet_df = returns_df.copy()
                    if match_date_range:
                        tearsheet_df = tearsheet_df.loc[start_date:end_date]
                    name = '{}_{}'.format(selected_ratio,quantile)
                    fp = f'{data_directory_filepath}/tearsheets/{name}.html'
                    if 'tearsheets' not in os.listdir(data_directory_filepath):
                        os.mkdir(data_directory_filepath+'/tearsheets')
                    qs_html(returns = tearsheet_df[quantile],benchmark=tearsheet_df['equiponderado'], periods_per_year=12, match_dates=True, title=name, download_filename=fp,output='')
                    st.success(f'Downloaded Successfully!\n\nTearsheet available at {fp}')
                    st.session_state[f'download_tearsheet_{i}'] = False


else:
    st.warning('Please Submit the data and params form in the sidebar to load the app.')