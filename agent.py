import asyncio
import json

from dotenv import load_dotenv
from strictjson import strict_json_async

from prompts import extract_prompt, system_prompt, user_prompt, user_response

load_dotenv()


async def llm(system_prompt: str, user_prompt: str) -> str:
    import os

    from groq import AsyncGroq

    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    chat_completion = await client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=0.3,
        max_tokens=360,
        top_p=1,
        stop=None,
        stream=False,
    )

    return chat_completion.choices[0].message.content


fields = {
    "height": "The height of the patient in centimeters, type:str|None",
    "weight": "The weight of the patient in kilograms, type:str|None",
    "condition": "The condition the patient is experiencing, type:str|None",
    "symptoms": "The symptoms the patient is experiencing, type:str|None",
    "personalHistory": "The personal history of the patient, type:str|None",
    "medicalHistory": "The medical history of the patient, type:str|None",
    "allergies": "The allergies the patient has, type:str|None",
    "medications": "The medications the patient is taking, type:str|None",
    "familyHistory": "The family history of the patient, type:str|None",
}


def format_patient_data(data):
    formatted_string = (
        f"Patient Name: {data.get('name', 'N/A')}\n"
        f"Email: {data.get('email', 'N/A')}\n"
        f"Gender: {data.get('gender', 'N/A')}\n"
        f"Date of Birth: {data.get('dateOfBirth', 'N/A')}\n"
        f"Height: {data.get('height', 'N/A')} cm\n"
        f"Weight: {data.get('weight', 'N/A')} kg\n"
        f"Condition: {data.get('condition', 'N/A')}\n"
        f"Symptoms: {data.get('symptoms', 'N/A')}\n"
        f"Personal History: {data.get('personalHistory', 'N/A')}\n"
        f"Medical History: {data.get('medicalHistory', 'N/A')}\n"
        f"Family History: {data.get('familyHistory', 'N/A')}\n"
        f"Allergies: {data.get('allergies', 'N/A')}\n"
        f"Medications: {data.get('medications', 'N/A')}\n"
    )
    return formatted_string


async def question_agent(data):
    global system_prompt, user_prompt
    user_prompt = user_prompt.format(format_patient_data(data))

    result = await strict_json_async(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_format={
            "question": "question, type: str",
        },
        llm=llm,
    )
    print(result)
    return result


async def extract_agent(response):
    global extract_prompt, user_response, fields
    user_response = user_response.format(response)
    result = await strict_json_async(
        system_prompt=extract_prompt,
        user_prompt=user_response,
        output_format=fields,
        llm=llm,
    )
    result = {k: v for k, v in result.items() if v}
    return result
