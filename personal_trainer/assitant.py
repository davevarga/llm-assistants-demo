import os
import time
import openai
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO)

from dotenv import find_dotenv, load_dotenv
load_dotenv()

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


# Creat client
client = openai.OpenAI(api_key=os.getenv("API_KEY"))
model = os.getenv("OPENAI_MODEL")

if __name__ == "__main__":
    # Load the previous conversion
    assistant_id = os.getenv("ASSISTANT_ID")
    thread_id = os.getenv("THREAD_ID")
    news_api_key = os.getenv("NEWS_API_KEY")

    # Create a message
    message = "How much water should i dring in a day if i work out?"
    response = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    # Run our command
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Please address the user like a royalty.",
    )

    # Wait for completion
    wait_for_run_completion(client, thread_id, run.id, 1)

    run_step = client.beta.threads.runs.steps.list(
        thread_id=thread_id,
        run_id=run.id,
    )
    print(f"Steps: {run_step.data}")