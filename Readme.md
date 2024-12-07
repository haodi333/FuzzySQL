# Fuzzy-SQL: Transform Natural Language to precise SQL queries

## Background

Studies on natural language (NL) to SQL have drawn much attention with the rise of LLMs. However, most studies focus on exploring fixed patterns of prompts, while overlooking practical applications. Since users may not be experts in designing such prompts and often provide only a fuzzy description of their intentions, it is essential to address this problem. We should help users achieve their goals without requiring them to cost much time on searching for fixed prompt patterns.

## Case

Let's consider the following case. We have a `college` table

```
"college_id"	"name_full"						"city"			"state"	"country"

"abilchrist"	"Abilene Christian University"	"Abilene"		"TX"	"USA"
"adelphi"		"Adelphi University"			"Garden City"	"NY"	"USA"
"adrianmi"		"Adrian College"				"Adrian"		"MI"	"USA"
"akron"			"University of Akron"			"Akron"			"OH"	"USA"
"alabama"		"University of Alabama"			"Tuscaloosa"	"AL"	"USA"
```

A fresh user may ask like: 

```
"Select all the colleges in Texas".
```

However, LLM will not output an expected query since it lack the information of the table. On the other hand, it is impossible to input a whole table to LLM. Therefore, we need a framework to transform user's NL-query to a stronger query that is enough for LLM to generate correct SQL.

Specifically, above NL-query lack some key information for generating a SQL, including:

1. **Bias in column values.** For example, the column `state` contains state abbreviations for the locations of the colleges. But this naming convention is not reported to LLM. this can lead to incorrect or incomplete queries.
2. **Lack of specificity with the tables and their columns.** User does not specify which tables or columns he is referring to, making it challenging to generate accurate SQL.

By addressing these two problems,a perfect query should be: 

```
Select the results in column 'name_full' with column 'state' takes the value of 'TX' in table 'college'.
```

Let's have a test. The following two examples are input to `Qwen:3B` which does not have any knowledge about our database.

```
####Ask####

Change the user's query to SQL and return the SQL only.
Query: Select all the colleges in Texas

####Answer####

SELECT name_full
FROM college;

####Ask####

Change the user's query to SQL and return the SQL only.
Query: Select the results in column 'name_full' with column 'state' takes the value of 'TX' in table 'college'.

####Answer####

SELECT name_full
FROM college
WHERE state = 'TX';
```

Interestingly, this small model is able to change the perfect query to correct SQL. Therefore, we can try to transform user's query to a perfect query.

## Framework

![framework](E:\future_posts\FuzzySQL\framework.png)

Explaining: This framework contains 3 modules. We only need to input a weak prompt that makes a fuzzy description of our idea.

1. Identify tables. The `identify_tables` function provides names of all tables in the database. Its return is assembled with a defined `temp prompt1` and input to `LLM`.
2. `LLM` outputs the selected table names. They are input to `identify_columns` function which returns names of all columns in each table. Then the return of function is assembled with a defined `temp prompt2` and input to `LLM`.
3. The related columns are input to `identify_columns_values` function which returns unique values of each column. The the return of function is assembled with a defined `temp prompt3` and input to `LLM`. `LLM` finally output the strong prompt.

For example, `'activity_1'` is a database from [Spider](https://yale-lily.github.io/spider) dataset, which contains the following tables:

1. **Activity** has two columns, with each `actid` corresponding to an `activity_name`.

![](E:\future_posts\FuzzySQL\activity.png)

2. **Faculty_Participates_in** has two columns, with each `FacID` represents a unique faculty member. This table can be connected with **Activity** by `actid`.

![](E:\future_posts\FuzzySQL\faculty_participates.png)

3. **Participates_in** has two columns, with each `stuid` represents a unique student. This table can be connected with **Activity** by `actid`.

![](E:\future_posts\FuzzySQL\participate_in.png)

4. **Faculty** has eight columns. This table can be connected with **Faculty_Participates_in** by `FacID`.

![](E:\future_posts\FuzzySQL\faculty.png)

5. **Student** has eight columns. This table can be connected with **Participates_in** by `StuID`.

![](E:\future_posts\FuzzySQL\student.png)

We can utilize LLM to generate fuzzy natural language queries. The prompt can be set as

```
Generate natural language queries based on the dictionary of the database {db_dic['activity_1']}. The structure is:
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
You should not specify table names. For example, a possible output is: "Select all the colleges in Texas".
```

Here `db_dic` is preprocessed as a dictionary of databases containing all tables and unique column values for each database. The output of GPT-4 is

```
1. Show all activities available for participation.
2. List all students who participate in extreme sports.
3. Find faculty members who participate in outdoor activities.
4. Show all students who are majoring in sports-related fields.
5. List all faculty members who are professors.
6. Find students who are under 20 years old.
7. Show all activities that involve water sports.
8. List faculty members who are advisors for students.
9. Find students who are from cities starting with the letter "P".
10. Show all activities that involve physical fitness.
```

These queries are suitable with our goal, like query 2 mentioned 'extreme sports', which is a fuzzy description of values of `activity_name` in **Activity**. 

## Usage

This repository contains both OpenAI and Ollama codes of FuzzySQL implementation.

1. Download [Spider](https://yale-lily.github.io/spider) dataset and put it in `./dataset/`.

2. Get valid tables. This is necessary because Spider dataset contains empty tables.

```
python get_valid_tables.py --data_dir ./dataset/spider/database --save_path ./dataset/valid_tables.pkl
```

3. Generate fuzzy queries by LLM. `num_queries` represents the number of queries for each database. The results will be saved in `./dataset/fuzzy_queries/_{num_queries}.pkl`. 

```
python generate_query.py --openai_api_key [your openai key] --model LLM.GPT_35_TURBO --num_queries 1
```

4. Run the OpenAI version of FuzzySQL.

```
python ask_llm.py --openai_api_key [your openai key] --question_file fuzzy_queries_1.pkl --model LLM.GPT_35_TURBO --output_folder r'./dataset/'
```

​	Or run the Ollama version.

```
python ask_ollama.py --question_file fuzzy_queries_1.pkl --model 'openchat:7b' --output_folder r'./dataset/'
```

5. Test the generated SQLs.

```
python test_openai.py --question_file fuzzy_queries_1.pkl --model 'openchat:7b' --output_folder r'./results/'
```

## Experimental result

Comapre the Correct rate of generated SQL . Some models cannot generate proper answers. Therefore, only models that can use this framework are listed here.

GPT-3.5-Turbo: 93.67%

Openchat:7b: 83.54%

qwen2.5-coder:7b: 90.51%