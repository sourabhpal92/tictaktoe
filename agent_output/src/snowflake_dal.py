import snowflake.connector
import pandas as pd
import logging
from tenacity import retry, wait_fixed, stop_after_attempt, after_log

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SnowflakeConnector:
    """
    A class to manage connections and interactions with Snowflake.
    """
    def __init__(self):
        self._conn = None
        self.connection_params = {}

    def is_connected(self):
        return self._conn is not None

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3), after=after_log(logger, logging.WARNING))
    def connect(self, account, user, password, warehouse=None, database=None, schema=None, role=None):
        """
        Establishes a connection to Snowflake.
        Raises an exception if connection fails after retries.
        """
        try:
            self._conn = snowflake.connector.connect(
                user=user,
                password=password,
                account=account,
                warehouse=warehouse,
                database=database,
                schema=schema,
                role=role,
                autocommit=True # Ensure transactions are automatically committed
            )
            self.connection_params = {
                "account": account,
                "user": user,
                "warehouse": warehouse,
                "database": database,
                "schema": schema,
                "role": role
            }
            logger.info("Successfully connected to Snowflake.")
            return True
        except snowflake.connector.errors.ProgrammingError as e:
            logger.error(f"Snowflake connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Snowflake: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during Snowflake connection: {e}")
            raise ConnectionError(f"An unexpected error occurred: {e}")

    def disconnect(self):
        """
        Closes the Snowflake connection if it exists.
        """
        if self._conn:
            self._conn.close()
            self._conn = None
            self.connection_params = {}
            logger.info("Disconnected from Snowflake.")

    def execute_query(self, sql_query, fetch_results=True, query_timeout=300):
        """
        Executes a SQL query and optionally fetches results as a Pandas DataFrame.
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Snowflake. Please connect first.")

        try:
            with self._conn.cursor() as cur:
                cur.execute(sql_query, timeout=query_timeout)
                if fetch_results:
                    df = cur.fetch_pandas_all()
                    logger.info(f"Query executed successfully, fetched {len(df)} rows.")
                    return df
                logger.info("Query executed successfully (no results fetched).")
                return None
        except snowflake.connector.errors.ProgrammingError as e:
            logger.error(f"Snowflake query execution failed: {e}")
            raise ValueError(f"SQL Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during query execution: {e}")
            raise RuntimeError(f"An unexpected error occurred: {e}")

    def get_metadata(self, metadata_type):
        """
        Fetches available metadata (warehouses, databases, schemas, roles).
        """
        if not self.is_connected():
            return []

        query = ""
        if metadata_type == 'warehouses':
            query = "SHOW WAREHOUSES"
        elif metadata_type == 'databases':
            query = "SHOW DATABASES"
        elif metadata_type == 'schemas':
            query = f"SHOW SCHEMAS IN DATABASE {self.connection_params.get('database', 'SNOWFLAKE')}"
        elif metadata_type == 'roles':
            query = "SHOW ROLES"
        else:
            return []

        try:
            df = self.execute_query(query)
            if df is not None:
                # Standardize column names for metadata fetching
                if metadata_type == 'warehouses' or metadata_type == 'databases' or metadata_type == 'schemas' or metadata_type == 'roles':
                    # All these SHOW commands result in a 'name' column for the entity
                    # or 'DATABASE_NAME' / 'SCHEMA_NAME' etc.
                    # We'll try to get the 'name' column or a relevant one.
                    cols = df.columns.str.upper().tolist()
                    if 'NAME' in cols:
                        return df['name'].tolist()
                    elif 'DATABASE_NAME' in cols:
                        return df['database_name'].tolist()
                    elif 'SCHEMA_NAME' in cols:
                        return df['schema_name'].tolist()
                    else:
                        logger.warning(f"Could not find 'name' or relevant column for {metadata_type} metadata.")
                        return []
            return []
        except Exception as e:
            logger.error(f"Failed to fetch {metadata_type}: {e}")
            return []

    def set_context(self, warehouse=None, database=None, schema=None, role=None):
        """
        Sets the active warehouse, database, schema, or role for the current session.
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Snowflake. Please connect first to set context.")

        commands = []
        if warehouse and self.connection_params.get('warehouse') != warehouse:
            commands.append(f"USE WAREHOUSE {warehouse}")
            self.connection_params['warehouse'] = warehouse
        if database and self.connection_params.get('database') != database:
            commands.append(f"USE DATABASE {database}")
            self.connection_params['database'] = database
        if schema and self.connection_params.get('schema') != schema:
            commands.append(f"USE SCHEMA {schema}")
            self.connection_params['schema'] = schema
        if role and self.connection_params.get('role') != role:
            commands.append(f"USE ROLE {role}")
            self.connection_params['role'] = role

        try:
            if commands:
                for cmd in commands:
                    self.execute_query(cmd, fetch_results=False)
                logger.info(f"Snowflake context updated: {', '.join(commands)}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set Snowflake context: {e}")
            raise RuntimeError(f"Failed to set Snowflake context: {e}")