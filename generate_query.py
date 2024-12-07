import pickle
import argparse
from llm.chatgpt import ask_llm, init_chatgpt
from utils.chat2sql import get_columns, get_unique_values
from utils.enums import LLM
import time

def load_databases(file_path):
    """Load databases from the pickle file."""
    with open(file_path, 'rb') as file:
        return pickle.load(file)

def get_columns_and_values(database, tables):
    """Retrieve columns and unique values for each table in the database."""
    columns_dic = {}
    for table in tables:
        columns = get_columns(database, table)
        columns_value = {}
        for col in columns:
            try:
                columns_value[col] = get_unique_values(database, table, col)
            except:
                print(f"Error processing table: {table}")
        columns_dic[table] = columns_value
    return columns_dic

def generate_prompt(columns_dic, num_queries):
    """Generate the prompt for the LLM based on the database dictionary."""
    return f"""Generate {num_queries} natural language queries based on the dictionary of the database {columns_dic}. The structure is:
    {{
        "table1": {{
            "column1": ["value1", "value2"],
            "column2": ["value3"]
        }},
        "table2": {{
            ...
        }}
    }}
    You should generate fuzzy queries that do not specify column values or use another naming style if available.
    You should not specify table names. For example, a possible output is: "Select all the colleges in Texas"."""

def process_databases(args):
    """Process all databases and generate queries using the LLM."""
    db_dic = {}
    init_chatgpt(args.openai_api_key)
    databases = load_databases(args.tables_path)
    for database, tables in databases.items():
        if tables:
            columns_dic = get_columns_and_values(database, tables)
            prompt = generate_prompt(columns_dic, args.num_queries)
            try:            
                resp = ask_llm(args.model, [prompt], args.temperature, args.n)
                # time.sleep(1)
                db_dic[database] = resp['response']

            except Exception as e:
                if 'RateLimitError' in str(e):
                    print(f"Rate limit hit for {database}.")
                else:
                    print(f"Error processing {database}: {e}")
                    
    return db_dic

def main(args):
    """Main function to load databases, process them and generate queries."""
    db_dic = process_databases(args)
    return db_dic

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--openai_api_key", type=str)
    parser.add_argument("--model", type=str, choices=[LLM.TEXT_DAVINCI_003, 
                                                      LLM.GPT_35_TURBO,
                                                      LLM.GPT_35_TURBO_0613,
                                                      LLM.GPT_35_TURBO_16K,
                                                      LLM.GPT_4], 
                        default=LLM.GPT_35_TURBO)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--num_queries", type=int, default=1)
    parser.add_argument("--tables_path", type=str, default="./dataset/valid_tables.pkl")
    args = parser.parse_args()
    db_dic = main(args)
    
    with open(f'./dataset/fuzzy_queries_{args.num_queries}.pkl','wb') as file:
        pickle.dump(db_dic, file)