import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import chardet
import os
import glob

st.set_page_config(layout="wide")

# location
folder_path = r"C:\Users\haile\Desktop\Bit by Bit Compliance\PureCoin\Raw Transactions"
file_list = glob.glob(os.path.join(folder_path + "/*.csv"))
            
# grab csv files from folder
main_dataframe = pd.DataFrame()
li = []

for i in range(len(file_list)):
    file_name = (file_list[i])
    df = pd.read_csv(file_list[i], sep=";", encoding='ISO-8859-1')
    li.append(df)

# merge files into one
frame = pd.concat(li, axis=0, ignore_index=True)

# Server Time pd.to_datetime
frame['Server Time'] = pd.to_datetime(frame['Server Time'], format = '%Y-%m-%d %H:%M:%S')

# sort by Server Time
frame = frame.sort_values(by = 'Server Time', ascending = True)

# drop duplicates
frame = frame.drop_duplicates()

# drop columns and create main_df
main_df = frame[['Server Time', 'Type', 'Cash Amount', 'Crypto Amount', 'Terminal SN', 'Local Transaction Id', 'Remote Transaction Id',
                       'Destination Address', 'Identity', 'Identity First Name', 'Identity Last Name']].copy()

# make lowercase and remove spaces from column names
main_df.columns = main_df.columns.str.replace(' ', '_')
main_df.columns = map(str.lower, main_df.columns)

# new df with server_time not as index
main_noindex_df = main_df.sort_values(by='server_time')
main_noindex_df['server_time'] = pd.to_datetime(main_noindex_df['server_time'], format = '%Y-%m-%d %H:%M:%S')

# set server_time as index
main_df.set_index('server_time', inplace=True)

# sort by ascending time (index)
main_df = main_df.sort_index()

    
# NAVIGATION
sidebar = st.sidebar.header('Navigation')
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options = ['Raw Data', 'Customer Agg. Volumes', 'CTR Scanner', 'Shared Wallet Scanner']
    )


# RAW DATA PAGE
if selected == 'Raw Data':

# title and file names
    st.title('Raw Data')
    for i in range(len(file_list)):
        st.write(file_list[i])

# main_df print
    st.subheader('Transactions')
    st.write(main_df.shape)
    st.dataframe(main_df)

# date range select = start_date_input and end_date_input
    min_start_date = main_df.index.min()
    max_end_date = main_df.index.max()
    start_date_input = st.sidebar.date_input('Start Date', min_start_date, min_value = min_start_date, max_value = max_end_date)
    end_date_input = st.sidebar.date_input('End Date', max_end_date, min_value = min_start_date, max_value = max_end_date)

# validation
    if start_date_input < end_date_input:
        st.sidebar.success('Start Date: `%s`\n\nEnd Date: `%s`' % (start_date_input, end_date_input))
    else:
        st.sidebar.error('Error: End date must fall after start date.')

# pd.Timestamp inputs
    start_date_input_fixed = pd.to_datetime(start_date_input) - datetime.timedelta(days=1)
    end_date_input_fixed = pd.to_datetime(end_date_input) + datetime.timedelta(days=1)

# submit filtering and print new df = time_filtered_df
    submit_button = st.sidebar.button('Filter')
    
    if submit_button:
        time_filtered_df = main_noindex_df.copy()
        time_filtered_df = time_filtered_df.loc[(time_filtered_df['server_time'] >= start_date_input_fixed) & 
                                                (time_filtered_df['server_time'] <= end_date_input_fixed)]
        time_filtered_df.set_index('server_time', inplace=True)

        st.subheader('Filtered Transactions')
        st.write(time_filtered_df.shape)
        st.dataframe(time_filtered_df)
        
# download as a csv
        @st.cache
        def convert_df_to_csv(df):
            return df.to_csv().encode('utf-8')

        st.download_button(
            label = 'Download as CSV',
            data=convert_df_to_csv(time_filtered_df),
            file_name='filtered_transactions.csv',
            mime='text/csv',
        )
    
    
# CUSTOME AGG. VOLUMES PAGE
if selected == 'Customer Agg. Volumes':
    st.title('Customer Agg. Volumes')
    
# customer buys
    customer_buys = main_noindex_df[main_noindex_df.type=="BUY"].groupby(['identity', 'identity_first_name', 'identity_last_name'], as_index=False).agg(
        tx_total = ('cash_amount', 'sum'), last_transacted = ('server_time', 'max'))

# customer buys format   = customer_buys_df  
    customer_buys_df = customer_buys.copy()
    customer_buys_df.set_index('identity', inplace=True)
    customer_buys_df['last_transacted'] = pd.to_datetime(customer_buys_df['last_transacted']).dt.date
    customer_buys_df = customer_buys_df.sort_values(by='last_transacted', ascending=False)
    
# customer sells
    customer_sells = main_noindex_df[main_noindex_df.type=="SELL"].groupby(['identity', 'identity_first_name', 'identity_last_name'], as_index=False).agg(
        tx_total = ('cash_amount', 'sum'), last_transacted = ('server_time', 'max'))

# customer sells format = customer_sells_df 
    customer_sells_df = customer_sells.copy()
    customer_sells_df.set_index('identity', inplace=True)
    customer_sells_df['last_transacted'] = pd.to_datetime(customer_sells_df['last_transacted']).dt.date
    customer_sells_df = customer_sells_df.sort_values(by='last_transacted', ascending=False)
    
# unfiltered dfs print
    col1,col2 = st.columns([2,2])
                                  
    col1.subheader('Customer Buys')
    col1.write(customer_buys_df.shape)
    col1.dataframe(customer_buys_df)
    
    col2.subheader('Customer Sells')
    col2.write(customer_sells_df.shape)
    col2.dataframe(customer_sells_df)
    
# min date last_transacted select = last_transacted_date_input
    min_start_date = main_df.index.min()
    max_end_date = main_df.index.max()
    last_transacted_date_input = st.sidebar.date_input('Min Date Last Transacted', max_end_date, min_value = min_start_date, max_value = max_end_date)
    
# pd.Timestamp inputs
    last_transacted_date_input = pd.to_datetime(last_transacted_date_input)
    
# min tx_total select = last_transacted_amount_input
    last_transacted_amount_input = st.sidebar.slider('Min Transaction Total', min_value = 0, max_value = 50000, value = 10000)

# submit filtering and print new df = filtered_buys and filtered_sells
    agg_total_submit_button = st.sidebar.button('Filter')
    if agg_total_submit_button:
        filtered_buys = customer_buys_df.loc[(customer_buys_df['last_transacted'] >= last_transacted_date_input)
                                   & (customer_buys_df['tx_total'] >= last_transacted_amount_input)]
        filtered_buys = filtered_buys.sort_values(by='tx_total', ascending=False)
        
        filtered_sells = customer_sells_df.loc[(customer_sells_df['last_transacted'] >= last_transacted_date_input)
                                   & (customer_sells_df['tx_total'] >= last_transacted_amount_input)]
        filtered_sells = customer_sells_df.sort_values(by='tx_total', ascending=False)
        
        col1.subheader('Filtered Buys')
        col1.write(filtered_buys.shape)
        col1.dataframe(filtered_buys)
    
        col2.subheader('Filtered Sells')
        col2.write(filtered_sells.shape)
        col2.dataframe(filtered_sells)


# CTR SCANNER PAGE
if selected == 'CTR Scanner':
    st.title('CTR Scanner')
    
    ctrs = main_noindex_df.groupby(['identity', 'identity_first_name', 'identity_last_name', pd.Grouper(freq='1D', key = 'server_time')]).agg(
        tx_total = ('cash_amount', 'sum'))

# ctrs format = ctr_df   
    ctr_df = ctrs.copy()
    ctr_df.reset_index(inplace=True)
    ctr_df.set_index('identity', inplace=True)
    ctr_df['server_time'] = pd.to_datetime(ctr_df['server_time']).dt.date
    ctr_df.rename({'server_time': 'date'}, axis = "columns", inplace = True)
    ctr_df = ctr_df.sort_values(by='date', ascending=False)    

# ctr_df print
    st.subheader('All Totals')
    st.write(ctr_df.shape)
    st.dataframe(ctr_df, 900)
    
# date range select = ctr_start_date_input and ctr_end_date_input
    min_start_date = main_df.index.min()
    max_end_date = main_df.index.max()
    ctr_start_date_input = st.sidebar.date_input('Start Date', min_start_date, min_value = min_start_date, max_value = max_end_date)
    ctr_end_date_input = st.sidebar.date_input('End Date', max_end_date, min_value = min_start_date, max_value = max_end_date)

# validation
    if ctr_start_date_input < ctr_end_date_input:
        st.sidebar.success('Start Date: `%s`\n\nEnd Date: `%s`' % (ctr_start_date_input, ctr_end_date_input))
    else:
        st.sidebar.error('Error: End date must fall after start date.')

# pd.Timestamp inputs
    ctr_start_date_input = pd.to_datetime(ctr_start_date_input)
    ctr_end_date_input = pd.to_datetime(ctr_end_date_input)
    
# tx_total slider
    amount_select = st.sidebar.slider('Transaction Total', min_value = 2000, max_value = 20000, value = [10001, 20000])
    amount_slider_max = amount_select[1]
    amount_slider_min = amount_select[0]
    
# submit filtering and print new df = filtered_ctrs
    ctr_submit_button = st.sidebar.button('Filter')
    
    if ctr_submit_button:
        filtered_ctrs = ctr_df.loc[(ctr_df['date'] >= ctr_start_date_input) & (ctr_df['date'] <= ctr_end_date_input) 
                                   & (ctr_df['tx_total'] <= amount_slider_max) & (ctr_df['tx_total'] >= amount_slider_min)]
        filtered_ctrs = filtered_ctrs.sort_values(by='date', ascending=False)
        
        st.subheader('Filtered Totals')
        st.write(filtered_ctrs.shape)
        st.dataframe(filtered_ctrs, 900)
        
# download as a csv
        @st.cache
        def convert_df_to_csv(df):
            return df.to_csv().encode('utf-8')

        st.download_button(
            label = 'Download as CSV',
            data=convert_df_to_csv(filtered_ctrs),
            file_name='filtered_ctrs.csv',
            mime='text/csv',
        )


# SHARED WALLER SCANNER PAGE
if selected == 'Shared Wallet Scanner':
    st.title('Shared Wallet Scanner')

# sw_main_noindex copy of main_noindex_df
    sw_main_noindex_copy = main_noindex_df[['destination_address', 'identity', 'cash_amount', 'server_time']].copy()
    
# shared_wallets
    shared_wallets = sw_main_noindex_copy.groupby(['destination_address']).agg(
        count = ('identity', 'nunique'), identities = ('identity', 'unique'), shared_total = ('cash_amount', 'sum'), last_transacted = ('server_time', 'max'))
    
# remove single identity counts
    shared_wallets = shared_wallets.loc[(shared_wallets['count'] > 1)]

# shared_wallets format = shared_wallets_df                                                                    
    shared_wallets_df = shared_wallets.copy()
    shared_wallets_df['last_transacted'] = pd.to_datetime(shared_wallets_df['last_transacted']).dt.date
    shared_wallets_df = shared_wallets_df.sort_values(by='last_transacted', ascending=False)
        
# shared_wallets_df print
    st.subheader('Shared Wallets')
    st.write(shared_wallets_df.shape)
    st.dataframe(shared_wallets_df)
       
# min date last_transacted select = shared_wallet_date input
    min_start_date = main_df.index.min()
    max_end_date = main_df.index.max()
    shared_wallet_date_input = st.sidebar.date_input('Min Date Last Transacted', max_end_date, min_value = min_start_date, max_value = max_end_date)
    
# pd.Timestamp inputs
    shared_wallet_date_input = pd.to_datetime(shared_wallet_date_input)
    
# min shared_total select
    shared_wallet_amount_input = st.sidebar.slider('Min Transaction Total', min_value = 0, max_value = 20000, value = 2000)
    
# submit filtering and print new df = filtered_shared_wallets
    shared_wallets_submit_button = st.sidebar.button('Filter')
    if shared_wallets_submit_button:
        filtered_shared_wallets = shared_wallets_df.loc[(shared_wallets_df['last_transacted'] >= shared_wallet_date_input)
                                   & (shared_wallets_df['shared_total'] >= shared_wallet_amount_input)]
        filtered_shared_wallets = filtered_shared_wallets.sort_values(by='shared_total', ascending=False)
        
        st.subheader('Filtered Shared Wallets')
        st.write(filtered_shared_wallets.shape)
        st.dataframe(filtered_shared_wallets)

    
    
    
    