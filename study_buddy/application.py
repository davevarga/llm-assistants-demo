import os
import time
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

import logging
logging.basicConfig(level=logging.INFO)


load_dotenv() # Import variables from .env file
api_key=os.getenv("OPENAI_API_KEY")
model=os.getenv("OPENAI_MODEL")

# Associate with the correct assistant in backend
assis_id = "asst_D4D6LIn0KHUNXSXXXvhH3JKW"

# Add your file path for document
file_path = './knowledge_base/public_perception_of_autonomous_vehicles.pdf'

# Create a new session
client = OpenAI(api_key=api_key)

if "file_id_list" not in st.session_state:
    st.session_state.file_ids_list = []

if "start_chat" not in st.session_state:
    st.session_state .start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Set up our front end page
st.set_page_config(
    page_title="Study Buddy - Chat and Learn",
    page_icon=":books:"
)

# Function definitions
def upload_file_openai(filepath):
    with open(filepath, "rb") as file:
        response = client.files.create(
            file=file, purpose="assistants")
    return response.id

file_uploaded = st.sidebar.file_uploader(
    "Upload a file to be transformed into embeddings",
    key="file_upload"
)

# Upload file button - store file id
if st.sidebar.button("Upload"):
    if file_uploaded is not None:
        with open(f"{file_uploaded.name}", "wb") as file:
            file.write(file_uploaded.getbuffer())
        another_file_id = upload_file_openai(f"{file_uploaded.name}")
        st.session_state.file_ids_list.append(another_file_id)
        st.sidebar.write(f"File ID:: {another_file_id}")

# Display file ids
if st.session_state.file_ids_list:
    st.sidebar.write("Uploaded File IDs:")
    for file_id in st.session_state.file_ids_list:
        st.sidebar.write(file_id)


