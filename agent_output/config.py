import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

def get_snowflake_credentials():
    """
    Retrieves Snowflake credentials from Streamlit secrets (production)
    or environment variables (.env for local development).
    """
    credentials = {}

    # Try Streamlit secrets first (for deployment)
    if hasattr(st, 'secrets') and st.secrets:
        # Check if st.secrets is populated, st.secrets.get() returns None if key not found
        credentials['account'] = st.secrets.get('SNOWFLAKE_ACCOUNT')
        credentials['user'] = st.secrets.get('SNOWFLAKE_USER')
        credentials['password'] = st.secrets.get('SNOWFLAKE_PASSWORD')
        credentials['role'] = st.secrets.get('SNOWFLAKE_ROLE')
        credentials['warehouse'] = st.secrets.get('SNOWFLAKE_WAREHOUSE')
        credentials['database'] = st.secrets.get('SNOWFLAKE_DATABASE')
        credentials['schema'] = st.secrets.get('SNOWFLAKE_SCHEMA')
    
    # Fallback to environment variables (for local development via .env or system env)
    if not credentials.get('account'):
        credentials['account'] = os.getenv('SNOWFLAKE_ACCOUNT')
        credentials['user'] = os.getenv('SNOWFLAKE_USER')
        credentials['password'] = os.getenv('SNOWFLAKE_PASSWORD')
        credentials['role'] = os.getenv('SNOWFLAKE_ROLE')
        credentials['warehouse'] = os.getenv('SNOWFLAKE_WAREHOUSE')
        credentials['database'] = os.getenv('SNOWFLAKE_DATABASE')
        credentials['schema'] = os.getenv('SNOWFLAKE_SCHEMA')

    # Basic validation for required credentials
    if not all([credentials.get('account'), credentials.get('user'), credentials.get('password')]):
        return None
    
    return credentials