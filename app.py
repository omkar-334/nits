import json
import os
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

from agent import extract_agent, format_patient_data, llm, question_agent
from db import fetch_patient_data, update_patient_data
from prompts import query_system

load_dotenv()
ngrok.set_auth_token(os.getenv("NGROK_TOKEN"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_json(file_path):
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        return data
    except:
        return None


def write_json(file_path, data):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file)


def update_json(file_path, data):
    existing_data = read_json(file_path)

    for key, value in data.items():
        existing_data[key] = value

    write_json(file_path, existing_data)


def all_full(data):
    if not data:
        return False
    for value in data.values():
        if isinstance(value, str):
            if value.strip() == "":
                return False
        elif value in [None, "", 0, False]:
            return False
    return True


@app.post("/extract")
async def query(email: str, response: Optional[str] = None):
    print(response)
    file_path = f"{email}.json"
    data = read_json(file_path)

    if all_full(data):
        query = f"""
        Here is the patient's data = {format_patient_data(data)}  
        Here is the patient's question = {response}"""

        result = await llm(query, query_system)
        return {"question": result}
    #######

    if not response or response.strip() == "":
        doc_id, data = fetch_patient_data(email)
        if data:
            write_json(file_path, data)

    else:
        results = await extract_agent(response)
        print(results)
        if results:
            update_json(file_path, results)

    data = read_json(file_path)
    print(data)
    if all_full(data):
        write_json(file_path, data)
        update_patient_data(email, data)
        return {"question": "please feel free to ask me any questions"}

    question_json = await question_agent(data)

    return question_json


# Main entry point
if __name__ == "__main__":
    # Start an ngrok tunnel on port 8000
    public_url = ngrok.connect(8000)
    print(f" * ngrok tunnel available at {public_url}")

    # Run the FastAPI app on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
