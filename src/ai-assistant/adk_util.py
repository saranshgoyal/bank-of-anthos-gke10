import requests
import json
from requests.exceptions import RequestException, HTTPError

def get_or_create_adk_session(base_url, app_name, user_id, session_id):
    """
    Checks for an existing ADK session and creates one if it doesn't exist.

    This function leverages the ADK's ability to implicitly create a session
    when the /run endpoint is called with a new session_id. It first
    attempts to get the session details to check for existence and then
    creates it if a 404 is returned.

    Args:
        base_url (str): The base URL of the ADK server (e.g., 'http://34.74.228.2').
        app_name (str): The name of the ADK agent application.
        user_id (str): The unique identifier for the user.
        session_id (str): The desired session identifier.

    Returns:
        str: The session ID if successful, otherwise None.
    """
    # The API path to check for an existing session
    session_path = f"/apps/{app_name}/users/{user_id}/sessions/{session_id}"
    session_url = f"{base_url}{session_path}"

    try:
        # First, try to get the session to see if it exists
        print(f"Checking for existing session at: {session_url}")
        response = requests.get(session_url)
        
        if response.status_code == 200:
            print(f"Session with ID '{session_id}' already exists.")
            return session_id
        elif response.status_code == 404:
            # Session not found, proceed to create it
            print(f"Session with ID '{session_id}' not found. Creating a new one...")
            
            # The URL to create the session is the same as the GET endpoint
            # but uses a POST request. The body can be empty or contain initial state.
            create_response = requests.post(
                url=session_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps({"state": {}}) # Optional initial state
            )
            create_response.raise_for_status() # Raise an exception for bad status codes
            
            print(f"Session '{session_id}' created successfully.")
            return session_id
        else:
            # Handle other HTTP errors
            print(f"Error checking for session: {response.status_code} - {response.text}")
            return None

    except HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except RequestException as e:
        print(f"An error occurred: {e}")
        return None
