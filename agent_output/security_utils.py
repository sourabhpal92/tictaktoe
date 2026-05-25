import sqlparse

def validate_sql_query(query: str) -> tuple[bool, str]:
    """
    Performs basic validation on a SQL query to prevent multi-statement execution
    and detect common malicious keywords.
    """
    if not query:
        return False, "Query cannot be empty."

    # Parse the query to detect multiple statements
    parsed_statements = sqlparse.parse(query)
    if len(parsed_statements) > 1:
        return False, "Multi-statement execution is not allowed for security reasons."

    # Further check the first statement if it exists
    if not parsed_statements:
        return False, "Invalid SQL query structure."

    statement = parsed_statements[0]
    
    # Check for specific disallowed keywords in a case-insensitive manner
    # This list can be extended based on specific security requirements
    disallowed_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'MERGE']
    query_upper = query.upper()
    
    for keyword in disallowed_keywords:
        if keyword in query_upper:
            # Allow 'SELECT * FROM' where 'FROM' is a keyword, but not other DDL/DML
            if not (keyword == 'FROM' and 'SELECT' in query_upper):
                # Basic check: ensure the keyword isn't part of a valid table/column name.
                # This is a simple check, a more robust solution would involve AST analysis.
                # For this application, we prioritize strictness for security.
                return False, f"Keyword '{keyword}' is not allowed in queries."

    # Ensure it's primarily a SELECT statement
    # This is a very basic check. A more advanced parser would be needed for full validation.
    if not query_upper.strip().startswith('SELECT'):
        return False, "Only SELECT queries are allowed for data retrieval."
            
    return True, "Query is valid."