import sqlite3
import os
import ast
import re

def get_db_path(database):
    """Generate the path for the SQLite database."""
    return os.path.join('./dataset/spider/database', database, f"{database}.sqlite")

def execute_query(database, query):
    """Execute a given SQL query on the specified database and return the result."""
    db_path = get_db_path(database)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    connection.close()
    return result

def get_columns(database, table):
    """Retrieve column names of the specified table from the database."""
    if database == 'hospital_1' and table == 'Procedure':
        print(table)
    query = f"PRAGMA table_info({table})"
    columns = execute_query(database, query)
    return [column[1] for column in columns]

def get_unique_values(database, table, column):
    """Retrieve unique values from the specified column of the table."""
    column = f'"{column}"'  
    query = f"SELECT DISTINCT {column} FROM {table}"
    values = execute_query(database, query)
    values = [item[0] for item in values]
    if len(values) > 5:
        return values[0:5]
    else:
        return values
    
def res_to_list(res):
    """ Transform list-like string generated by LLM to list.   """
    if type(res) == list:
        res = ast.literal_eval(res[0])
        return res
    else:
        try:
            result = ast.literal_eval(res)
        except:
            formatted_string = re.sub(r'(\w+)', r'"\1"', res)
            result = ast.literal_eval(formatted_string)

        return result