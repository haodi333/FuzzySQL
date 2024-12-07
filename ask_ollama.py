import argparse
import pickle
import ast
from utils.enums import LLM
from utils.chat2sql import get_columns, get_unique_values, res_to_list
from llm.ollama import ask_llm


def parse_args():
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--question_folder", type=str,  default = './dataset/')
    parser.add_argument("--question_file", type=str,  default = 'fuzzy_queries_1.pkl')
    parser.add_argument("--model", type=str, choices=['wizardlm2:7b','llama2:13b','openchat:7b','smollm:1.7b','codellama:7b','sqlcoder:7b','deepseek-coder-v2:16b','phi'], default='openchat:7b')
    parser.add_argument("--start_index", type=int, default=0)
    parser.add_argument("--end_index", type=int, default=1000000)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--mini_index_path", type=str, default="")
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--n", type=int, default=1, help="Size of self-consistent set")
    parser.add_argument("--output_folder", type=str, default=r'./dataset/')
    return parser.parse_args()

def load_tables():
    """Load valid tables from pickle file."""
    with open("./dataset/valid_tables.pkl", 'rb') as file:
        return pickle.load(file)

def generate_prompt(question, db, related_tables=None, columns=None, related_columns = None):
    """Generate a prompt for querying the LLM."""
    if related_tables:
        return f"User's query is : {question} Based on user's query, identify the related tables from {db}. Reply tables' names as a list. Only return the tables' names, do not reply any other texts. For example, a possible output format maybe ['table1','table2']"
    elif columns:
        return f"User's query is : {question} Based on user's query, identify the related columns {columns}. Reply columns' name as a list. Only return the columns' name, do not reply any other texts. For example, a possible output format maybe ['column1','column2']"
    return f"User's query is : {question} Based on user's query, generate the proper SQL. The following dictionary contains all related tables, columns and their unique values. {related_columns} Only return the SQL, do not reply any other texts."

def get_related_tables(question, args, db, tables):
    """Get related tables from LLM."""
    prompt = generate_prompt(question, db, related_tables=True)
    res = ask_llm(args.model, prompt, args.temperature, args.n)
    related_tables = res_to_list(res['response'])
    return related_tables

def get_related_columns(question, args, database, related_tables):
    """Get related columns for each table."""
    related_columns_dic = {}
    for table in related_tables:
        columns = get_columns(database, table)
        prompt = generate_prompt(question, database, columns=columns)
        res = ask_llm(args.model, prompt, args.temperature, args.n)
        related_columns = res_to_list(res['response'])
        columns_value = {col: get_unique_values(database, table, col) for col in related_columns}
        related_columns_dic[table] = columns_value
    return related_columns_dic

def generate_sql(question, args, related_columns_dic,database):
    """Generate the SQL query from LLM."""
    prompt = generate_prompt(question, database, related_columns = related_columns_dic)
    res = ask_llm(args.model, prompt, args.temperature, args.n)
    return res['response']

def main():
    result= {}
    args = parse_args()

    with open(args.question_folder + args.question_file, 'rb') as file:
        question_file = pickle.load(file)
    tables = load_tables()
    for database in question_file.keys():
        db = tables[database]
        questions = question_file[database]
        questions = questions[0].split('\n')
        result[database] = {}
        for  question in questions:
            # Step 1: Get related tables
            try:
                related_tables = get_related_tables(question, args, db, tables)
                # if not set(related_tables).issubset(set(db)):
                #     # print(database)
                #     continue
                # Step 2: Get related columns
                related_columns_dic = get_related_columns(question, args, database, related_tables)
                # Step 3: Generate SQL
                sql = generate_sql(question, args, related_columns_dic,db)
                result[database][question] = sql
            except:
                print(f"Error occurs when executing on {database}")
                continue
    
    with open(args.output_folder + 'output_' + args.model.replace(':','-') + '_' + args.question_file, 'wb') as file:
        pickle.dump(result, file)

if __name__ == '__main__':
    main()
