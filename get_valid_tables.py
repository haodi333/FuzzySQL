import os
import sqlite3
import pickle
import argparse

def get_tables_with_data(db_path):
    """Retrieve tables with non-empty content from a database."""
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        valid_tables = []
        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM {table[0]}")
                content = cursor.fetchall()
                # Decode content to UTF-8 with error handling
                for row in content:
                    row = [str(cell).encode('utf-8', errors='ignore').decode('utf-8') if isinstance(cell, str) else cell for cell in row]
                if content:
                    valid_tables.append(table[0])
            except Exception as e:
                print(f"Error reading table {table[0]} in {db_path}: {e}")
        return valid_tables
    except Exception as e:
        print(f"Error processing {db_path}: {e}")
        return []

def process_databases(db_dir):
    """Process all databases in the given directory and return a record of valid tables."""
    record = {}
    databases = os.listdir(db_dir)
    
    for db_name in databases:
        db_path = os.path.join(db_dir, db_name, f"{db_name}.sqlite")
        valid_tables = get_tables_with_data(db_path)
        if valid_tables:
            record[db_name] = valid_tables
            
    return record

def save_valid_tables(record, file_path):
    """Save the record of valid tables to a pickle file."""
    with open(file_path, 'wb') as file:
        pickle.dump(record, file)
    print(f"Valid tables are successfully saved at {file_path}.")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default=r'./dataset/spider/database')
    parser.add_argument("--save_path", type=str, default=r'./dataset/valid_tables.pkl')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    data_dir = args.data_dir
    save_path = args.save_path
    record = process_databases(data_dir)
    save_valid_tables(record, save_path)
