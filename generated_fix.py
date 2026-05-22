import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from streamlit import caching
import io
from datetime import datetime
import numpy as np

# Function to load data
@caching.st.memo
def load_data(file):
    return pd.read_csv(file)

# Function to filter data
def filter_data(df, date_range, country_list):
    filtered_df = df[(df['date'] >= date_range[0]) & (df['date'] <= date_range[1])]
    if len(country_list) > 0:
        filtered_df = filtered_df[filtered_df['country'].isin(country_list)]
    return filtered_df

# Function to plot revenue over time
def plot_revenue_over_time(df):
    fig = px.line(df, x='date', y='revenue', color='country', title='Revenue Over Time')
    fig.update_layout(xaxis_title='Date', yaxis_title='Revenue')
    return fig

# Function to plot users over time
def plot_users_over_time(df):
    fig = px.line(df, x='date', y='users', color='country', title='Users Over Time')
    fig.update_layout(xaxis_title='Date', yaxis_title='Users')
    return fig

# Main function
def main():
    # Set page configuration
    st.set_page_config(page_title='Revenue Dashboard', page_icon=':bar_chart:', layout='wide')

    # Set sidebar configuration
    st.sidebar.image('https://raw.githubusercontent.com/streamlit/streamlit/develop/logo/index.png', width=100)
    st.sidebar.markdown('## Revenue Dashboard')

    # Upload CSV file
    uploaded_file = st.sidebar.file_uploader('Upload CSV file', type=['csv'])

    # Load sample data if no file is uploaded
    if uploaded_file is None:
        df = load_data('https://raw.githubusercontent.com/streamlit/demo-plotly/main/data.csv')
    else:
        df = load_data(uploaded_file)

    # Display KPI cards
    col1, col2, col3 = st.columns(3)
    col1.metric('Total Revenue', f'${df["revenue"].sum():,}')
    col2.metric('Total Users', f'{df["users"].sum():,}')
    col3.metric('Countries', f'{len(df["country"].unique())}')

    # Display filters
    date_range = st.sidebar.date_input('Select Date Range', [df['date'].min(), df['date'].max()])
    country_list = st.sidebar.multiselect('Select Countries', df['country'].unique())

    # Filter data
    filtered_df = filter_data(df, date_range, country_list)

    # Display search and filtering
    search_term = st.sidebar.text_input('Search for countries')
    filtered_df = filtered_df[filtered_df['country'].str.contains(search_term, case=False)]

    # Display plots
    col1, col2 = st.columns(2)
    col1.plotly_chart(plot_revenue_over_time(filtered_df))
    col2.plotly_chart(plot_users_over_time(filtered_df))

    # Download CSV button
    @st.cache
    def convert_df(df):
        return df.to_csv(index=False)
    csv = convert_df(filtered_df)
    st.download_button('Download CSV', csv, 'revenue_dashboard.csv', 'text/csv', key='download-csv')

if __name__ == '__main__':
    main()