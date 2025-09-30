import os
import json
from openai import OpenAI

def upload_json_and_store_param(json_path: str) -> str:
    """
    Uploads the given JSON file to OpenAI and stores the file_id in a param file named after the input json.
    Returns the param filename.
    """
    client = OpenAI()
    with open(json_path, "rb") as file_content:
        uploaded_file = client.files.create(
            file=file_content,
            purpose="assistants"
        )
    param_filename = os.path.splitext(os.path.basename(json_path))[0] + "_param.json"
    with open(param_filename, "w", encoding="utf-8") as f:
        json.dump({"id": uploaded_file.id}, f, indent=4)
    return param_filename

def get_file_id_from_param(param_filename: str) -> str:
    """
    Reads the file_id from the given param file.
    Returns the file_id as a string.
    """
    with open(param_filename, "r", encoding="utf-8") as f:
        param = json.load(f)
    return param["id"]

def attach_file_to_vector_store(file_id: str, vector_store_id: str) -> None:
    """
    Attaches the given file_id to the specified vector store.
    """
    client = OpenAI()
    # Correct usage: pass as keyword arguments
    vector_store_file = client.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=file_id
    )
    print(f"Attached file {file_id} to vector store {vector_store_id}. Response: {vector_store_file}")


def main():
    json_path = "allrounds.json"
    #param_file = upload_json_and_store_param(json_path)
    #print(f"Param file created: {param_file}")
    file_id = get_file_id_from_param("allrounds_param.json")
    print(f"File ID from param file: {file_id}")
    vs_id = get_file_id_from_param("vectorstore.json")
    print(f"VS ID from param file: {vs_id}")
    attach_file_to_vector_store(file_id, vs_id)

if __name__ == "__main__":
    main()