import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("creds.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
collection = db.collection("patients")


def fetch_documents():
    docs = collection.stream()
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")


def fetch_patient_data(email):
    docs = collection.where("email", "==", email).stream()

    for doc in docs:
        return (doc.id, doc.to_dict())


def update_patient_data(email, data):
    """
    Updates patient data by email. Adds new fields if they don't exist.

    :param email: The patient's email address.
    :param data: A dictionary of fields to update in the patient's document.
    :return: None
    """
    doc_id, patient_data = fetch_patient_data(email)

    if doc_id:
        collection.document(doc_id).set(data)
        print(f"Patient data for {email} updated successfully.")
    else:
        collection.add({**data, "email": email})
        print(f"New patient data created for {email}.")

    return data


data = {"height": 177.8, "weight": 55}

# Update patient data by email
# x = fetch_patient_data("testt@test.com")
# print(x)
# 1. reg complete -> ask extra details, scrape
# 2. pdf upload -> vlm
# 3. groq api rag
