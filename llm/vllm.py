import time
import requests
import json
from utils.enums import LLM

VLLM_SERVER_URL = "http://127.0.0.1:5000"

def ask_completion(model, batch, temperature):
    data = {
        "model": model,
        "prompt": batch,
        "temperature": temperature,
        "max_tokens": 200,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": [";"]
    }
    response = requests.post(f"{VLLM_SERVER_URL}/generate", json=data)
    response.raise_for_status()
    result = response.json()
    return {
        "response": [choice["text"] for choice in result["choices"]],
        "usage": result["usage"]
    }

def ask_chat(model, messages: list, temperature, n):
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 200,
        "n": n
    }
    response = requests.post(f"{VLLM_SERVER_URL}/chat", json=data)
    response.raise_for_status()
    result = response.json()
    response_clean = [choice["message"]["content"] for choice in result["choices"]]
    if n == 1:
        response_clean = response_clean[0]
    return {
        "response": response_clean,
        "usage": result["usage"]
    }

def ask_llm(model: str, batch: list, temperature: float, n: int):
    n_repeat = 0
    while True:
        try:
            if model in LLM.TASK_COMPLETIONS:
                # TODO: self-consistency in this mode
                assert n == 1
                response = ask_completion(model, batch, temperature)
            elif model in LLM.TASK_CHAT:
                # batch size must be 1
                assert len(batch) == 1, "batch must be 1 in this mode"
                messages = [{"role": "user", "content": batch[0]}]
                response = ask_chat(model, messages, temperature, n)
                response['response'] = [response['response']]
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
