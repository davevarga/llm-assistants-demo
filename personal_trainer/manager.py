import os
import json
import time

import requests
import openai
import logging
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
news_api_key = os.getenv("NEWS_API_KEY")


def get_news(topic):
    url = (
        f"https://newsapi.org/v2/everything?q={topic}&"
        f"apiKey={news_api_key}&pageSize=5&language=en"
    )
    try:
        # Fetch the response from the API
        response = requests.get(url)
        if response.status_code == 200:
            news = json.dumps(response.json(), indent=4)
            news_json = json.loads(news)

            # Loop through all the fields
            status = news_json["status"]
            total_results = news_json["totalResults"]
            articles = news_json["articles"]
            final_news = []

            for article in articles:
                title_description = (
                    f"Title: {article["title"]}",
                    f"Author: {article["author"]}",
                    f"Source: {article["source"]["name"]}",
                    f"Description: {article["description"]}",
                    f"URL: {article["url"]}"
                )
                description = article["description"]
                content = article["content"]
                final_news.append(title_description)

            return final_news

        else: return [] # If there was a status code error

    except requests.exceptions.RequestException as e:
        logging.error("Error occurred during API request", e)


class AssistantManager:
    # Static fields for stateful assistants
    thread_id = "thread_zfD8RYk0m5SOwTapYEdABABU"   # Your thread id
    assistant_id = "asst_uc47iWEjt4OvMPCsPHQKKr9F"  # Your assistant's id

    def __init__(self, model: str = model):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        # Retrieve assistant and thread id if they exist
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def create_assistant(self, name, instructions, tools):
        if not AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools,
                model=self.model
            )
            AssistantManager.assistant_id = self.assistant.id
            logging.info(f"Assistant created with ID: {self.assistant.id}")

        # No duplicate assistants are allowed.
        else: logging.error(f"Assistant with ID: {AssistantManager.assistant_id} already exists")

    def create_thread(self):
        if not AssistantManager.thread_id:
            self.thread = self.client.beta.threads.create()
            AssistantManager.thread_id = self.thread.id
            logging.info(f"Thread created with ID: {self.thread.id}")
        else: logging.error(f"Thread with ID: {AssistantManager.thread_id} already exists")

    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )
            logging.info(f"Message added to thread with ID: {self.thread.id}")

        # If thread does not exist
        else: logging.error(f"There is no thread to add the message")

    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions
            )
            logging.info(f"Assistant run with ID: {self.assistant.id}")

    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []

            last_message = messages.data[0]
            response = last_message.content[0].text.value
            summary.append(response)
            self.summary = "\n".join(summary)
            logging.info(f"Message content published")

    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            # Interpret function calling from the llm
            if func_name == "get_news":
                output = get_news(topic=arguments["topic"])
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                # Submitting outputs back to the assistant
                tool_outputs.append({"tool_call_id": action["id"],"output": final_str})
                logging.info(f"Submitting output from function: {func_name}"
                             f" with id: {action["id"]} back to the Assistant")
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread.id,
                    run_id=self.run.id,
                    tool_outputs=tool_outputs
                )

    def get_summary(self):
        return self.summary

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id,
                )

                if run_status.status == "completed":
                    self.process_message()
                    break
                # Delegate function calling
                elif run_status.status == "requires_action":
                    self.call_required_functions(
                        run_status.required_action.submit_tool_outputs.model_dump())

    def run_steps(self):
        return self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id,
            run_id=self.run.id,
        )


if __name__ == "__main__":
    manager = AssistantManager()

    # Create streamlit interface
    st.title("News Summerizer")
    with st.form(key="user_input_form"):
        instructions = st.text_input("Enter topic")
        submit_button = st.form_submit_button(label="Run Assistant")

        # h
        if submit_button:
            manager.create_assistant(
                name="News Summerizer",
                instructions=f"You are a personal article summarizer Assistant,"
                             f"who knows how to take a list of article's titles and"
                             f"descriptions and then write a short summary of all the new articles",
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "get_news",
                        "description": "Get the list of articles/news for the given function parameters",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "topic":{
                                    "type": "string",
                                    "description": "The topic of the news, e.g. bitcoin"
                                }
                            },
                            "required": ["topic"],
                        }
                    }
                }]
            )
            # Add the message and run the assistant
            manager.create_thread()
            manager.add_message_to_thread(
                role="user",
                content=f"Summarize the news on this topic: {instructions}"
            )
            manager.run_assistant(instructions="Summarize the news")

            # Wait for completions and process message
            manager.wait_for_completion()
            summary = manager.get_summary()
            st.write(summary)
            st.text("Run Steps")
            st.code(manager.run_steps(), line_numbers=True)