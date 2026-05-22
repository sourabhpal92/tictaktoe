import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Set dark theme
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    body {
        background-color: #2F4F7F;
        color: #FFFFFF;
    }
    .sidebar .sidebar-content {
        background-color: #2F4F7F;
    }
    .main .block-container {
        background-color: #2F4F7F;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar filters
st.sidebar.title("Filters")
country_filter = st.sidebar.selectbox("Country", ["All"] + list(pd.read_csv("data.csv")["country"].unique()))
date_filter = st.sidebar.date_input("Date Range", value=[pd.to_datetime("2022-01-01"), pd.to_datetime("2022-12-31")])

# Upload CSV support
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    # Load uploaded CSV
    df = pd.read_csv(uploaded_file)
else:
    # Load default CSV
    df = pd.read_csv("data.csv")

# Apply filters
if country_filter != "All":
    df = df[df["country"] == country_filter]
df = df[(df["date"] >= pd.to_datetime(date_filter[0])) & (df["date"] <= pd.to_datetime(date_filter[1]))]

# KPI cards
st.title("KPIs")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Revenue", value=f"${df['revenue'].sum():,.2f}")
with col2:
    st.metric(label="Total Users", value=f"{df['users'].sum():,}")
with col3:
    st.metric(label="Average Revenue per User", value=f"${df['revenue'].sum() / df['users'].sum():,.2f}")

# Plotly charts
st.title("Charts")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["date"], y=df["revenue"], mode="lines", name="Revenue"))
fig.add_trace(go.Scatter(x=df["date"], y=df["users"], mode="lines", name="Users"))
fig.update_layout(title="Revenue and Users Over Time", xaxis_title="Date", yaxis_title="Value")
st.plotly_chart(fig, use_container_width=True)

# Search and filtering
st.title("Data")
search_term = st.text_input("Search")
if search_term:
    df_filtered = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
else:
    df_filtered = df
st.write(df_filtered)

# Download CSV button
@st.cache
def convert_df(df):
    return df.to_csv(index=False)
csv = convert_df(df_filtered)
st.download_button("Download CSV", csv, "data.csv", "text/csv")

# Responsive layout
st.set_option('deprecation.showPyplotGlobalUse', False)