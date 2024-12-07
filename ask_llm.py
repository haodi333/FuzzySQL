import argparse
import pickle
import ast
from llm.chatgpt import init_chatgpt, ask_llm
from utils.enums import LLM
from utils.chat2sql import get_columns, get_unique_values


def parse_args():
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--question_folder", type=str,  default = './dataset/')
    parser.add_argument("--question_file", type=str,  default = 'fuzzy_queries_1.pkl')
    parser.add_argument("--openai_api_key", type=str)
    parser.add_argument("--model", type=str, choices=[LLM.TEXT_DAVINCI_003, LLM.GPT_35_TURBO, 
                                                      LLM.GPT_35_TURBO_0613, LLM.GPT_35_TURBO_16K, 
                                                      LLM.GPT_4], default=LLM.GPT_35_TURBO)
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
        return f"User's query is : {question}. Based on user's query, identify the related tables from {db}. Only return the tables' names, do not reply any other texts. Reply tables' names as a list. For example, a possible output maybe ['college','expert']"
    elif columns:
        return f"User's query is : {question}. Based on user's query, identify the related columns {columns}. Only return the columns' name, do not reply any other texts. Reply columns' name as a list, For example, a possible output maybe ['college','expert']"
    return f"User's query is : {question}. Based on user's query, generate the proper SQL. The following dictionary contains all related tables, columns and their unique values. {related_columns} Only return the SQL, do not reply any other texts."

def get_related_tables(question, args, db, tables):
    """Get related tables from LLM."""
    prompt = generate_prompt(question, db, related_tables=True)
    batch = [prompt]
    res = ask_llm(args.model, batch, args.temperature, args.n)
    related_tables = ast.literal_eval(res['response'][0])
    return related_tables

def get_related_columns(question, args, database, related_tables):
    """Get related columns for each table."""
    related_columns_dic = {}
    for table in related_tables:
        columns = get_columns(database, table)
        prompt = generate_prompt(question, database, columns=columns)
        batch = [prompt]
        res = ask_llm(args.model, batch, args.temperature, args.n)
        related_columns = ast.literal_eval(res['response'][0])
        columns_value = {col: get_unique_values(database, table, col) for col in related_columns}
        related_columns_dic[table] = columns_value
    return related_columns_dic

def generate_sql(question, args, related_columns_dic,database):
    """Generate the SQL query from LLM."""
    prompt = generate_prompt(question, database, related_columns = related_columns_dic)
    batch = [prompt]
    res = ask_llm(args.model, batch, args.temperature, args.n)
    return res['response']

def main():
    result= {}
    args = parse_args()
    assert args.model in LLM.BATCH_FORWARD or (args.model not in LLM.BATCH_FORWARD and args.batch_size == 1), \
        f"{args.model} doesn't support batch_size > 1"

    #  question = 'Select all the colleges in Texas.'
    init_chatgpt(args.openai_api_key)
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
            related_tables = get_related_tables(question, args, db, tables)
            # Step 2: Get related columns
            related_columns_dic = get_related_columns(question, args, database, related_tables)
            # Step 3: Generate SQL
            sql = generate_sql(question, args, related_columns_dic,db)
            result[database][question] = sql
    with open(args.output_folder + 'output_' + args.model + '_' + args.question_file + '.pkl', 'wb') as file:
        pickle.dump(result, file)

if __name__ == '__main__':
    main()
