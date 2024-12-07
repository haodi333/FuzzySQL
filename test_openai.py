import pickle
from utils.chat2sql import execute_query

import argparse
from llm.chatgpt import init_chatgpt, ask_llm
from utils.enums import LLM
from utils.chat2sql import get_columns, get_unique_values


def parse_args():
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--question_file", type=str,  default = 'fuzzy_queries_1.pkl')
    parser.add_argument("--model", type=str, choices=[LLM.TEXT_DAVINCI_003, LLM.GPT_35_TURBO, 
                                                      LLM.GPT_35_TURBO_0613, LLM.GPT_35_TURBO_16K, 
                                                      LLM.GPT_4], default=LLM.GPT_35_TURBO)
    parser.add_argument("--output_folder", type=str, default=r'./dataset/')
    return parser.parse_args()

args = parse_args()

with open(args.output_folder + 'output_' + args.model + '_' + args.question_file, 'rb') as file:
    sql_dic = pickle.load(file)

correct_count = 0
errors = []

for database, queries in sql_dic.items():
    sql = list(queries.values())[0][0]
    try:
        execute_query(database, sql)
        correct_count += 1
    except Exception as e:
        errors.append([database, list(queries.items())[0], str(e)])

total_queries = len(sql_dic)
correct_rate = correct_count / total_queries * 100
print(f"Correct rate: {correct_rate:.2f}%")

with open('results/correct_' + args.model + '_' + args.question_file + '.pkl', 'wb') as correct_file:
    pickle.dump(errors, correct_file) 

with open('results/errors_' + args.model + '_' + args.question_file + '.pkl', 'wb') as error_file:
    pickle.dump(errors, error_file) 
