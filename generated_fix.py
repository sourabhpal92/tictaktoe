import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title='Revenue Dashboard',
    page_icon=':bar_chart:',
    layout='wide'
)

# Load data
@st.cache(allow_output_mutation=True)
def load_data():
    return pd.DataFrame({
        'date': np.arange('2022-01-01', '2022-01-31', dtype='datetime64'),
        'revenue': np.random.randint(1000, 10000, size=31),
        'users': np.random.randint(100, 1000, size=31),
        'country': np.random.choice(['USA', 'Canada', 'Mexico'], size=31)
    })

# Main function
def main():
    data = load_data()

    # Create sidebar filters
    with st.sidebar:
        st.markdown('# Revenue Dashboard')
        st.subheader('Filters')
        start_date = st.date_input('Start Date', min_value=data['date'].min(), max_value=data['date'].max(), value=data['date'].min())
        end_date = st.date_input('End Date', min_value=data['date'].min(), max_value=data['date'].max(), value=data['date'].max())
        country = st.multiselect('Country', data['country'].unique())

        # Upload CSV file
        uploaded_file = st.file_uploader("Upload CSV file", type='csv')

        # Download CSV file
        with st.form("download_form"):
            st.write("Download CSV")
            @st.cache
            def convert_df(data):
                return data.to_csv().encode('utf-8')
            csv = convert_df(data)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name='data.csv',
                mime='text/csv',
            )

    # Filter data based on sidebar filters
    filtered_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    if country:
        filtered_data = filtered_data[filtered_data['country'].isin(country)]

    # Plotly charts
    st.subheader('KPI Cards')
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${filtered_data['revenue'].sum():,.2f}")
    col2.metric("Total Users", f"{filtered_data['users'].sum():,}")
    col3.metric("Average Revenue per User", f"${(filtered_data['revenue'].sum() / filtered_data['users'].sum()):,.2f}")

    st.subheader('Revenue Over Time')
    revenue_over_time = px.line(filtered_data, x='date', y='revenue')
    revenue_over_time.update_layout(xaxis_title='Date', yaxis_title='Revenue')
    st.plotly_chart(revenue_over_time, use_container_width=True)

    st.subheader('Users Over Time')
    users_over_time = px.line(filtered_data, x='date', y='users')
    users_over_time.update_layout(xaxis_title='Date', yaxis_title='Users')
    st.plotly_chart(users_over_time, use_container_width=True)

    st.subheader('Revenue by Country')
    revenue_by_country = filtered_data.groupby('country')['revenue'].sum().reset_index()
    revenue_by_country = px.bar(revenue_by_country, x='country', y='revenue')
    revenue_by_country.update_layout(xaxis_title='Country', yaxis_title='Revenue')
    st.plotly_chart(revenue_by_country, use_container_width=True)

    # Upload CSV support
    if uploaded_file is not None:
        uploaded_data = pd.read_csv(uploaded_file)
        st.subheader('Uploaded Data')
        st.write(uploaded_data)

    # Search and filtering
    st.subheader('Search and Filtering')
    search_term = st.text_input('Search')
    filtered_data = filtered_data[filtered_data.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

    # Responsive layout
    st.subheader('Data')
    st.write(filtered_data)

if __name__ == "__main__":
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.set_option('theme', 'dark')
    main()