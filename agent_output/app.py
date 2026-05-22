import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit import cache
import io

# Set page title and layout
st.set_page_config(layout='wide', page_title='Revenue Dashboard')

# Initialize sidebar filters
st.sidebar.title('Filters')
country_filter = st.sidebar.multiselect('Country', options=None, default=None)
start_date_filter = st.sidebar.date_input('Start Date')
end_date_filter = st.sidebar.date_input('End Date')

# Load data from uploaded CSV
uploaded_file = st.sidebar.file_uploader('Upload CSV File')
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.DataFrame(columns=['date', 'revenue', 'users', 'country'])

# Update country filter options if data is available
if not df.empty:
    country_filter_options = df['country'].unique()
    country_filter = st.sidebar.multiselect('Country', options=country_filter_options, default=None)

# Apply filters to data
@cache
def filter_data(df, country_filter, start_date_filter, end_date_filter):
    filtered_df = df.copy()
    if country_filter:
        filtered_df = filtered_df[filtered_df['country'].isin(country_filter)]
    if start_date_filter:
        filtered_df = filtered_df[filtered_df['date'] >= start_date_filter]
    if end_date_filter:
        filtered_df = filtered_df[filtered_df['date'] <= end_date_filter]
    return filtered_df

# Display KPI cards
def display_kpi_cards(filtered_df):
    col1, col2, col3 = st.columns(3)
    col1.metric(label='Total Revenue', value=f"${filtered_df['revenue'].sum():,.0f}")
    col2.metric(label='Total Users', value=f"{filtered_df['users'].sum():,.0f}")
    col3.metric(label='Average Revenue per User', value=f"${filtered_df['revenue'].sum() / filtered_df['users'].sum():,.2f}")

# Display Plotly charts
def display_charts(filtered_df):
    revenue_line_chart = px.line(filtered_df, x='date', y='revenue', title='Revenue Over Time')
    users_line_chart = px.line(filtered_df, x='date', y='users', title='Users Over Time')
    country_bar_chart = px.bar(filtered_df.groupby('country')['revenue'].sum().reset_index(), x='country', y='revenue', title='Revenue by Country')
    
    col1, col2 = st.columns(2)
    col1.plotly_chart(revenue_line_chart, use_container_width=True)
    col2.plotly_chart(users_line_chart, use_container_width=True)
    st.plotly_chart(country_bar_chart, use_container_width=True)

# Main app logic
st.title('Revenue Dashboard')
if not df.empty:
    filtered_df = filter_data(df, country_filter, start_date_filter, end_date_filter)
    display_kpi_cards(filtered_df)
    display_charts(filtered_df)
    st.subheader('Data Table')
    st.write(filtered_df)

# Download CSV button
def download_csv(df):
    csv = df.to_csv(index=False)
    st.download_button('Download CSV', csv, 'revenue_data.csv', 'text/csv')

if not df.empty:
    download_csv(filtered_df)