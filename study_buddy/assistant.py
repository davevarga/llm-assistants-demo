import os
import time

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

# Upload file to the server
client = OpenAI(api_key=api_key)


def wait_for_run_completion(client, thread_id, run_id, sleep_interval):
    """
    Waits for a run to complete and print the elapsed time

    :param client: the object which handles the connection with the llm
    :param thread_id: where to post the response
    :param run_id: where to receive the response from
    :param sleep_interval:
    :return: the time elapsed until the run is completed
    """
    while True:
        try:
           run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
           if run.completed_at:
               elapsed_time = run.completed_at - run.created_at
               formatted_ellapsed_time = time.strftime(
                   "%H:%M:%S", time.gmtime(elapsed_time)
               )
               logging.info(f"Run completed in {formatted_ellapsed_time}")

               messages = client.beta.threads.messages.list(thread_id=thread_id)
               last_message = messages.data[0]
               response = last_message.content[0].text.value
               print(response)
               break

        except Exception as e:
            logging.error(f"Exception while waiting for the run to complete: {e}")
            break

        time.sleep(sleep_interval)


if __name__ == "__main__":
    # Create a new thread
    thread = client.beta.threads.create()

    # Upload the file to the mode
    crypto_file_object = client.files.create(
        file=open(file_path, "rb"),
        purpose="assistants"
    )

    # Upload the message to the thread
    message = "Give me a summary of the abstract of the paper that i have uploaded"
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message,
        attachments=[
            {"file_id": crypto_file_object.file_id, "tools":[{"type": "file_search"}]}
        ]
    )

    # Run assistant
    run = client.beta.threads.runs.create(
        assistant_id=assis_id,
        thread_id=thread.id,
        instructions="Please address the user as a royalty"
    )
    wait_for_run_completion(
        client=client,
        thread_id=thread.id,
        run_id=run.id,
        sleep_interval=1
    )