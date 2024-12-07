import time
import requests
import json

OLLAMA_SERVER_URL = "http://localhost:11434/v1/chat/completions"

def ask_completion(model, batch, temperature):
    data = {
        "model": model,
        "messages": [{"role": "user", "content": batch}],
        "temperature": temperature,
        "max_tokens": 200,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": [";"]
    }
    response = requests.post(f"{OLLAMA_SERVER_URL}", json=data)
    response.raise_for_status()
    result = response.json()
    return {
        "response": result["choices"][0]["message"]['content'],
        "usage": result.get("usage", {})
    }

def ask_chat(model, messages: list, temperature, n):
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 200,
        "n": n
    }
    response = requests.post(f"{OLLAMA_SERVER_URL}", json=data)
    response.raise_for_status()
    result = response.json()
    response_clean = [choice["message"]["content"] for choice in result["choices"]]
    if n == 1:
        response_clean = response_clean[0]
    return {
        "response": response_clean,
        "usage": result.get("usage", {})
    }

def ask_llm(model: str, batch: list, temperature: float, n: int):
    n_repeat = 0
    while True:
        try:
            response = ask_completion(model, batch, temperature)
            break
        except requests.exceptions.RequestException as e:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for RequestException: {e}", end="\n")
            time.sleep(1)
            continue
        except json.decoder.JSONDecodeError:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for JSONDecodeError", end="\n")
            time.sleep(1)
            continue
        except Exception as e:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for exception: {e}", end="\n")
            time.sleep(1)
            continue

    return response
