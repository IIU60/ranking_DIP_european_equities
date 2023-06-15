import os
import pandas as pd
import streamlit as st

import app_functions as af
import plots as pl
import custom_calculations as calcs

from quantstats.reports import html as qs_html


st.set_page_config(layout='wide')
st.title('Equities Ranking Dashboard')
#Flag to wait for pararms form to be submitted
if 'start_app' not in st.session_state:
    st.session_state.start_app = False


with st.sidebar:

    with st.form(key='initial_params_form'):
        #Initial parameters user input
        n_quantiles = st.number_input('Number of Quantiles:', min_value=1, value=10)
        min_stocks_per_date_ratio = st.number_input('Minimum stocks per date ratio:', min_value=0.0, max_value=1.0, value=0.8)
        min_total_dates_ratio = st.number_input('Minimum total dates ratio:', min_value=0.0, max_value=1.0, value=0.8)
        data_directory_filepath = st.text_input('Filepath to data directory:',key='data_fp', value=r'Z:\Interés Departamental\Model Portfolio\Hugo\Ranking DIP European Equities\copia 12-04-2023\data\vertical_dowload_files')
        prices_csv_filepath = st.text_input('Filepath to prices csv:',key='prices_fp', value=r'Z:\Interés Departamental\Model Portfolio\Hugo\Ranking DIP European Equities\copia 12-04-2023\data\vertical_dowload_files\PriceClose.csv')
        
        #Index constituency filtering parameters
        with st.expander('Index Constituency Filtering'):
            mask_filepath = st.text_input('Filepath to index constituency mask:',key='mask_fp', value=r'Z:\Interés Departamental\Model Portfolio\Hugo\Ranking DIP European Equities\copia 12-04-2023\data\PriceClose_vertical\monthly_constituents_filter.csv')
            expected_stocks_per_date = st.number_input('Expexted stocks per date:',value=600,min_value=0)
        
        init_form_button = st.form_submit_button()
        
    if init_form_button:
        #Read prices file and add to session state
        st.session_state.prices_df = af.read_and_sort_data(fr'{prices_csv_filepath}')
        #Ignoring fitering functionality
        if mask_filepath.lower() == 'none':
            st.session_state.mask = None
        else: #Read mask, add to session state
            st.session_state.mask = af.read_and_sort_data(fr'{mask_filepath}')
        #Read and filter the data in in the data directory
        st.session_state.good_dfs,st.session_state.bad_dfs = af.filter_data(
            fr'{data_directory_filepath}',min_stocks_per_date_ratio,min_total_dates_ratio,expected_stocks_per_date,st.session_state.mask)
        if 'data_dict' not in st.session_state:
            st.session_state.data_dict = {}
        st.session_state.data_dict.update(st.session_state.good_dfs)
        #Show rejected files
        st.warning(f'Rejected Data:\n{list(st.session_state.bad_dfs.keys())}')
        st.session_state.start_app = True
        
#Load the platform when flag
if st.session_state.start_app == True:

    with st.sidebar:
        #weighted indicator flag
        if 'create_weighted_indicator' not in st.session_state:
            st.session_state.create_weighted_indicator = False
        #button to flag on click
        if st.button('Create Multi-factor Indicator'):
            st.session_state.create_weighted_indicator = True
        #when flag open form
        if st.session_state.create_weighted_indicator == True:
            
            with st.form('weighted_indicator_form'):
                weighted_indicator_name = st.text_input('Indicator Name:')
                #creating and showing the dataframe with available indicators
                weighted_ratio_weights_df = st.data_editor(pd.DataFrame(dict(Factor=st.session_state.data_dict.keys(), Weight=0.0, Type='-')),width=600)
                
                weighted_indicator_form_button = st.form_submit_button()
           
            if weighted_indicator_form_button:
                #Get weighted mean of rankings of the indicators specified in the dataframe
                weighted_indicator_df = af.multi_factor_ranking(weighted_ratio_weights_df, st.session_state.data_dict, n_quantiles,st.session_state.mask)
                #add data to session state
                st.session_state.data_dict[weighted_indicator_name] = weighted_indicator_df
                
                st.success('Created Successfully')
                #Unflag to close the form on next reload
                st.session_state.create_weighted_indicator = False

        #custom indicator flag
        if 'create_custom_indicator' not in st.session_state:
            st.session_state.create_custom_indicator = False
        #button to flag on click
        if st.button('Create Custom Indicator'):
            st.session_state.create_custom_indicator = True
        #on flag load form
        if st.session_state.create_custom_indicator == True:

            with st.form('custom_indicator_form'):
                #name and formula user input
                custom_indicator_name = st.text_input('Indicator Name:')
                user_input = st.text_input('Formula:')

                custom_indicator_form_button = st.form_submit_button()
                #setting the mask variable in custom_calcs.py to the filtering mask set by the user (this is required for the beta function to not need the mask as a parameter)
                calcs.mask = st.session_state.mask
                #creating a dictionary of the functions in custom_calculations.py (excluding dunders, builtins, and imports)
                calcs_dict = {k:v for k,v in calcs.__dict__.items() if not k.startswith('__') and k not in ['ta','pd','apply_mask','mask']}
                #creating the dictionary for the local namespace of the eval function and adding the platforms data to it
                locals_dict = calcs_dict.copy()
                locals_dict.update(st.session_state.data_dict)
                #gathering functions docstrings for documentation
                docstrings = {k:v.__doc__ for k, v in calcs_dict.items()}
                #showing the documentation of the available functions
                with st.expander('Available Functions documentation'):
                    for key, value in docstrings.items():
                        st.markdown(f"**{key}**")
                        st.markdown(value)
            #when form submit:
            if custom_indicator_form_button:
                #evaluate the formula
                custom_df = eval(user_input,{'__builtins__':{}},locals_dict)
                #appending data to session state
                st.session_state.data_dict[custom_indicator_name] = custom_df

                st.success('Created Successfully')
                #unflag to close on reload
                st.session_state.create_custom_indicator = False

        #flag
        if 'download_indicator' not in st.session_state:
            st.session_state.download_indicator = False
        #button to raise flag
        if st.button('Download Indicator'):
            st.session_state.download_indicator = True
        #on flag:
        if st.session_state.download_indicator == True:
            #user input form
            with st.form('download_indicator_form'):
                indicator_to_download = st.selectbox('Indicator:',options=st.session_state.data_dict.keys())
                download_indicator_name = st.text_input('Name:')
                download_indicator_form_button = st.form_submit_button('Download')

            if download_indicator_form_button:
                #check directory for filename and modify if found
                filename = af.check_dir_and_change_filename(download_indicator_name,data_directory_filepath,'.csv')
                #save to csv
                st.session_state.data_dict[indicator_to_download].to_csv(fr'{data_directory_filepath}\{filename}.csv')

                st.success('Downloaded Successfully')
                #unflag to close on reload
                st.session_state.download_indicator = False
            
    #number of columns to show
    n_indicators = st.number_input('Number of Indicators:',value=1)

    cols = st.columns(n_indicators)

    for i in range(n_indicators):
        #in each column:
        with cols[i]:
            #selected dataframe
            selected_ratio = st.selectbox('Ratio:', st.session_state.data_dict.keys(),key=f'ratio_{i}')
            #columns for params
            subcol1,subcol2 = st.columns(2)
            #type of indicator 'high'/'low'
            with subcol1:       
                type_of_indicator = st.selectbox('Type:', ['high','low'],key=f'type_{i}')
            #show working values name in terminal
            print('\nWorking on: ',selected_ratio)
            #apply filtering mask
            masked_data = af.apply_mask(st.session_state.data_dict[selected_ratio],st.session_state.mask)
            #rank the data
            ranked_data = af.rank_data(masked_data, n_quantiles, type_of_indicator)
            #calculate the returns
            returns_df = af.get_returns(ranked_data, st.session_state.prices_df, n_quantiles,shift_period=1,rets_period=1) # shift and returns period set to 1 row
            #list of dates for the date range form
            index_list = returns_df.index.to_list()
            #date range form
            with subcol2:
                st.markdown('##')
                with st.expander('Date Range'):
                    start_date = st.date_input('Start Date',value=index_list[0],min_value=index_list[0],max_value=index_list[-1],key=f'start_date_{i}')
                    end_date = st.date_input('End Date',value=index_list[-1],min_value=index_list[0],max_value=index_list[-1],key=f'end_date_{i}')
            #log scale and notna graph options
            subcol3,subcol4 = st.columns(2)
            with subcol3:       
                log_scale = st.checkbox('Logarithmic Scale:',key=f'log_graphs_{i}')
            with subcol4:
                notna_graph = st.checkbox('Show Non-missing Values Graph',key=f'notna_graph_{i}')
            
            #show notna graph
            if notna_graph:
                st.write(len(returns_df)/277)
                st.plotly_chart(pl.notna_plot(ranked_data),True)
            #dict of plotting functions
            graphs_dict = {
                'NAV Absoluto': pl.plot_NAV_absoluto,
                'NAV Relativo a Equiponderado': pl.plot_NAV_relativo,
                'Rentabilidad Media Anualizada': pl.plot_rentabilidad_media,
                'Volatilidad Anualizada':pl.plot_volatilidad,
                'Sharpe Ratio':pl.plot_sharpe
                }

            desired_graphs = st.multiselect('Desired Graphs:',graphs_dict.keys(),key=f'desired_graphs_{i}')
            #plotting the graphs
            for graph in desired_graphs:
                st.plotly_chart(graphs_dict[graph](returns_df.loc[start_date:end_date], selected_ratio, log_scale=log_scale),True,config=pl.config)
            
            #downloading buttons columns
            download_cols = st.columns(3)

            with download_cols[0]:
                #flag
                if f'download_tearsheet_{i}' not in st.session_state:
                    st.session_state[f'download_tearsheet_{i}'] = False
                #button to flag on click
                if st.button('Create Tearsheet',key=f'tearsheet_button_{i}'):
                    st.session_state[f'download_tearsheet_{i}'] = True
                #on flag:
                if st.session_state[f'download_tearsheet_{i}'] == True:
                    #user input for quantile selection and date range matching
                    with st.form(f'download_tearsheet_form_{i}'):
                        quantile = st.selectbox(label='Quantile:',options=returns_df.columns)
                        match_date_range = st.checkbox('Match Date Range')
                        download_tearsheet_form_button = st.form_submit_button('Download')

                    if download_tearsheet_form_button:

                        tearsheet_df = returns_df.copy()
                        #reduce returns df to date range
                        if match_date_range:
                            tearsheet_df = tearsheet_df.loc[start_date:end_date]
                        #making dir if doesn't exist
                        if 'tearsheets_dir_fp' not in st.session_state:
                            st.session_state.tearsheets_dir_fp = f'{data_directory_filepath}/tearsheets'
                        if 'tearsheets' not in os.listdir(data_directory_filepath):
                            os.mkdir(st.session_state.tearsheets_dir_fp)
                        #setting filename and checking if it exists in dir
                        filename = '{}_{}_{}'.format(selected_ratio,type_of_indicator,quantile)
                        filename = af.check_dir_and_change_filename(filename,st.session_state.tearsheets_dir_fp,'.html')
                        filepath = f'{st.session_state.tearsheets_dir_fp}/{filename}.html'
                        #create and download tearsheet
                        qs_html(returns = tearsheet_df[quantile],benchmark=tearsheet_df['equiponderado'], periods_per_year=12, match_dates=True, title=filename, download_filename=filepath,output='')
                        
                        st.success(f'Downloaded Successfully!\n\nTearsheet available at {filepath}')
                        #unflag to close on reload
                        st.session_state[f'download_tearsheet_{i}'] = False
            

            with download_cols[1]:
                #flag
                if f'download_ranking_{i}' not in st.session_state:
                    st.session_state[f'download_ranking_{i}'] = False
                #button to flag
                if st.button('Download Ranking',key=f'ranking_button_{i}'):
                    st.session_state[f'download_ranking_{i}'] = True
                #on flag:
                if st.session_state[f'download_ranking_{i}'] == True:
                    #user input for date range matching
                    with st.form(f'download_ranking_form_{i}'):
                        match_date_range = st.checkbox('Match Date Range')
                        download_ranking_form_button = st.form_submit_button('Download')

                    if download_ranking_form_button:
                        #creating dir if doesn't exist
                        if 'rankings_dir_fp' not in st.session_state:
                            st.session_state.rankings_dir_fp = f'{data_directory_filepath}/rankings'
                        if 'rankings' not in os.listdir(data_directory_filepath):
                            os.mkdir(st.session_state.rankings_dir_fp)
                        #setting filename and modifiying if it already exists
                        filename = '{}_{}_rankings'.format(selected_ratio,type_of_indicator)
                        filename = af.check_dir_and_change_filename(filename,st.session_state.rankings_dir_fp,'.csv')
                        filepath = f'{st.session_state.rankings_dir_fp}/{filename}.csv'

                        rankings_df = ranked_data.copy()
                        #reducing df to date range if desired
                        if match_date_range:
                            rankings_df = rankings_df.loc[start_date:end_date]
                        #downloading df as csv
                        rankings_df.to_csv(filepath)

                        st.success(f'Downloaded Successfully!\n\nFile available at {filepath}')
                        #unflag to close on reload
                        st.session_state[f'download_ranking_{i}'] = False


            with download_cols[2]:
                #flag
                if f'download_returns_{i}' not in st.session_state:
                    st.session_state[f'download_returns_{i}'] = False
                #button to flag
                if st.button('Download Returns',key=f'returns_button_{i}'):
                    st.session_state[f'download_returns_{i}'] = True
                #on flag:
                if st.session_state[f'download_returns_{i}'] == True:
                    #user input form for date range matching
                    with st.form(f'download_returns_form_{i}'):
                        match_date_range = st.checkbox('Match Date Range')
                        download_returns_form_button = st.form_submit_button('Download')

                    if download_returns_form_button:
                        #creating dir if doesn't exist
                        if 'returns_dir_fp' not in st.session_state:
                            st.session_state.returns_dir_fp = f'{data_directory_filepath}/returns'
                        if 'returns' not in os.listdir(data_directory_filepath):
                            os.mkdir(st.session_state.returns_dir_fp)
                        #setting filename and modifying if already exists in dir
                        filename = '{}_{}_returns'.format(selected_ratio,type_of_indicator)
                        filename = af.check_dir_and_change_filename(filename,st.session_state.returns_dir_fp,'.csv')
                        filepath = f'{st.session_state.returns_dir_fp}/{filename}.csv'

                        returns_df_to_download = returns_df.copy()
                        #reducing to date range if checked
                        if match_date_range:
                            returns_df_to_download = returns_df_to_download.loc[start_date:end_date]
                        #downloading df as csv
                        returns_df_to_download.to_csv(filepath)

                        st.success(f'Downloaded Successfully!\n\nFile available at {filepath}')
                        #unflag to close on reload
                        st.session_state[f'download_returns_{i}'] = False

#warning for prompting user to submit the params form
else:
    st.warning('Please Submit the data and params form in the sidebar to load the app.')