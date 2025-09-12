import os
import sys

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from wheel.metadata import yield_lines


def create_session(resource_id: str, user_id: str) -> None:
    """Creates a new session for the specified user."""
    remote_app = agent_engines.get(resource_id)
    remote_session = remote_app.create_session(user_id=user_id)
    print("Created session:",remote_session)
    # print(f"  Session ID: {remote_session['id']}")
    # print(f"  User ID: {remote_session['user_id']}")
    # print(f"  App name: {remote_session['app_name']}")
    # print(f"  Last update time: {remote_session['last_update_time']}")
    print("\nUse this session ID with --session_id when sending messages.")

def send_message( user_id: str, session_id: str, message: str,remote_app) -> None:
    """Sends a message to the deployed agent."""
    # message=input("Enter >>")
    # remote_app = agent_engines.get(resource_id)

    print(f"Sending message to session {session_id}:")
    print(f"Message: {message}", "$$$$$$$$$$$$$$$")
    print("\nResponse:")
    for event in remote_app.stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
    ):
        res=event
        print(json.dumps(res,indent=4))
        res=res['content']['parts'][0]['text']

import json
def send_message_1(resource_id: str, user_id: str, session_id: str, message: str):
    # session = agent_engines.create_session(user_id="foo")
    remote_app = agent_engines.get(resource_id)

    request = {
        "user_id": user_id,
        "session_id": session_id,
        "message": {
            "role": "user",
            "parts": [{"text": message}]
        },
        "events": [],
        "artifacts": [],
        "authorizations": {}
    }
    request_json = json.dumps(request)

    for event in remote_app.streaming_agent_run_with_events(request_json=request_json):
        print(event['events'][0]['content']['parts'][0]['text'])
        # response=event['events'][0]['content']['parts'][0]['text']
    # print(response,"-------------->")
def send_message_2(user_id: str, session_id: str, message: str,remote_app):
    request = {
        "user_id": user_id,
        "session_id": session_id,
        "message": {
            "role": "user",
            "parts": [{"text": message}]
        },
        "events": [],
        "artifacts": [],
        "authorizations": {}
    }
    request_json = json.dumps(request)
    response= remote_app.streaming_agent_run_with_events(request_json=request_json)
    for i in response:
        print(i['events'][0]['content']['parts'][0]['text'])
    # print(yield_lines(response))
    # for event in remote_app.streaming_agent_run_with_events(request_json=request_json):
    #     print(event['events'][0]['content']['parts'][0]['text'])





if __name__ == "__main__":
    # create_session("7998507287419289600","12345")
    remote_app = agent_engines.get("<id>")
    send_message("12345","3953417752726732800","hi how are you",remote_app)