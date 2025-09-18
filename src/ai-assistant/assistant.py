# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Banking-Assistant Chatbot manages all user queries using AI Agents
"""

import atexit
from datetime import datetime, timedelta
import logging
import os
import json

import bcrypt
import jwt
import requests
from flask import Flask, jsonify, request
from requests.exceptions import HTTPError, RequestException

from adk_util import get_or_create_adk_session

from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.propagate import set_global_textmap
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.instrumentation.flask import FlaskInstrumentor


def create_app():
    """Flask application factory to create instances
    of the AI-Assistant Flask App
    """
    app = Flask(__name__)
    # Set up logging
    app.logger.handlers = logging.getLogger('gunicorn.error').handlers
    app.logger.setLevel(logging.getLogger('gunicorn.error').level)
    app.logger.info('Starting frontend service.')

    # Disabling unused-variable for lines with route decorated functions
    # as pylint thinks they are unused
    # pylint: disable=unused-variable

    @app.route('/version', methods=['GET'])
    def version():
        """
        Service version endpoint
        """
        return app.config['VERSION'], 200

    @app.route('/ready', methods=['GET'])
    def readiness():
        """
        Readiness probe
        """
        return 'ok', 200
    
    @app.route('/chatget', methods=['GET'])
    def chatget():
        """
        Handles chat requests using the GET method.
        Data is expected in the URL's query string, e.g., /chat?message=hello_world
        """
        # Use request.args to get data from URL query parameters
        message = request.args.get('message')

        app.logger.info(f"******Request Received for chatget.. -->  {message}")
    
        # Check if the 'message' parameter exists in the URL
        if message:
            print(f"Received message in GET: {message}")
            
            # Return a success response with the received message
            return jsonify({"status": "success", "received_message": message}), 200
        else:
            # Return an error response if the 'message' parameter is missing
            return jsonify({"status": "error", "message": "Missing 'message' in query parameters"}), 400

    @app.route('/chat', methods=['POST'])
    def chat():
        # Get the JSON data from the request
        data = request.get_json()
        
        # app.logger.info(f"Request Received.. -->  {data}")
        app.logger.info(f"******Request Received for chat.. -->  {data}")
        
        # message = request.args.get('message')
        message = data['message']
        app.logger.info(f"$$$$$Received message in POST Request::: {message}")

        # Check if the 'message' key exists in the JSON data
        if message:
            # Extract the message and print it to the console
            # message = data['message']
            app.logger.info(f"####Received message in POST Request: {message}")
            
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ')[1] if auth_header else None
            app.logger.info(f"Token from Cookie: {token}")

            token_data = decode_token(token, app.config['PUBLIC_KEY'])
            display_name = token_data['name']
            username = token_data['user']
            account_id = token_data['acct']

            app.logger.info(f"User Details from Token: {display_name}, {username}, {account_id}")

            res = call_agent_v1(token, data, token_data)

            # agent_response = res.json()
            # app.logger.info(f"----Raw Response from AI Agent: {agent_response}")
            app.logger.info(f"----Raw Response from AI Agent: {res}")

            # parsed_response = _parse_agent_response(agent_response)
            parsed_response = _parse_agent_response(res)

            app.logger.info(f"----Parsed Response to UI: {parsed_response}")
            

            app.logger.info(f"----WITH JSONIFY Parsed Response to UI: {jsonify(parsed_response)}")

            return jsonify(parsed_response)
            
            # Return a success response
            # return jsonify({"status": "success", "received_message": message}), 200
            # return jsonify({"response": f"I am a virtual assistant. You said: {message}"}), 200

            # return res

        else:
            # Return an error response if the message is missing
            return jsonify({"response": "Please say something....."}), 400

    def call_agent():
        """Calls the AI Agent to handle user queries"""
        try:
            app.logger.info(f"Calling Banking AI-Agent : {query}")
            hed = {'Authorization': 'Bearer ' + token,
                    'content-type': 'application/json'}
            app.logger.info(f"URL for BANKING_AGENT: {app.config['AI_AGENT_URI']}")
            resp = requests.post(url=app.config["AI_AGENT_URI"],
                                    data=json.dumps(query),
                                    headers=hed,
                                    timeout=app.config['BACKEND_TIMEOUT']*5) # Increased timeout for AI
            resp.raise_for_status()
            # TODO - TO BE REMOVED
            app.logger.info(f"Response From Agent: {resp.json}")
            app.logger.info(f"Response From Agent in JSON Format: {jsonify(resp.json())}")
            app.logger.info(f"###Response From Agent: {resp.text}")
            
            return jsonify(resp.json())
        except (RequestException, HTTPError) as err:
            app.logger.error('Error calling ai-assistant: %s', str(err))
            return jsonify({'error': 'ai service unavailable'}), 500

    def call_agent_v1(token, query, user_info):
        """
        Calls the AI Agent to handle user queries.
        
        Args:
            token (str): The authorization token.
            query (dict): The user query in JSON format.
            user_info (dict): Decoded user information from the token.
            
        Returns:
            tuple: A tuple containing the JSON response and HTTP status code.
        """
        try:
            app.logger.info(f"Calling Banking AI-Agent : {query}")
            # Create a session-specific conversation ID.
            # A simple approach is to use the user's username and account ID.
            user_id = user_info.get('user')
            session_id = user_info.get('acct')

            session_id = get_or_create_adk_session(
                                                        base_url="http://banking-agent:80",
                                                        app_name="banking-agent",
                                                        user_id=user_id,
                                                        session_id=session_id)
            
            app.logger.info(f"*****Using ADK Session ID: {session_id} *********")
            
            # Construct the payload for the ADK /run endpoint.
            agent_payload = {
                "app_name": "banking-agent",
                "user_id": user_id,
                "session_id": session_id,
                "new_message": {
                    "role": "user",
                    "parts": [{"text": query.get('message')}]
                },
                "user_info": user_info # Pass user info for the agent's tools
            }

            app.logger.info(f"Calling Banking AI-Agent with payload: {agent_payload}")
            hed = {'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'}
            
            AI_BANKING_AGENT_URI = app.config["AI_BANKING_AGENT_URI"]
            app.logger.info(f"URL : {AI_BANKING_AGENT_URI}")

            resp = requests.post(url=AI_BANKING_AGENT_URI, data=json.dumps(agent_payload),
                                headers=hed,
                                timeout=app.config['BACKEND_TIMEOUT'] * 5)  # Increased timeout for AI
            resp.raise_for_status()
            
            # TODO - TO BE REMOVED
            # app.logger.info(f"Response From Agent: {resp.json}")
            # app.logger.info(f"Response From Agent in JSON Format: {jsonify(resp.json())}")
            app.logger.info(f"###Response From Agent: {resp.text}")
            # return jsonify(resp.json())
            return resp.json()
        except (RequestException, HTTPError) as err:
            app.logger.error('Error calling ai-assistant: %s', str(err))
            return jsonify({'error': 'ai service unavailable'}), 500

    def _parse_agent_response(agent_response):
        """
        Parses the raw response from the ADK agent to extract the text.

        Args:
            agent_response (list): The JSON response from the agent.

        Returns:
            dict: A dictionary with a single "response" key for the UI.
        """
        try:
            # The agent's text is in the first part of the first content object.
            text_response = agent_response[0]['content']['parts'][0]['text']
            # Clean up newlines for better display
            text_response = text_response.strip()
            return {"response": text_response}
            # return jsonify({"response": text_response}), 200
        except (IndexError, KeyError, TypeError) as e:
            app.logger.error(f"Error parsing agent response: {e}")
            app.logger.error(f"Unexpected agent response format: {agent_response}")
            # Provide a fallback response
            return {"response": "I'm sorry, I received an unexpected response. Please try again."}

    def decode_token(token, public_key):
        """Decodes token with public key"""
        return jwt.decode(algorithms=['RS256'],
                        jwt=token,
                        key=public_key,
                        options={"verify_signature": True})



    @atexit.register
    def _shutdown():
        """Executed when web app is terminated."""
        app.logger.info("Stopping ai-assistant.")

    # Set up logger
    app.logger.handlers = logging.getLogger('gunicorn.error').handlers
    app.logger.setLevel(logging.getLogger('gunicorn.error').level)
    app.logger.info('Starting ai-assistant.')

    # Set up tracing and export spans to Cloud Trace.
    if os.environ['ENABLE_TRACING'] == "true":
        app.logger.info("✅ Tracing enabled.")
        # Set up tracing and export spans to Cloud Trace
        trace.set_tracer_provider(TracerProvider())
        cloud_trace_exporter = CloudTraceSpanExporter()
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(cloud_trace_exporter)
        )
        set_global_textmap(CloudTraceFormatPropagator())
        FlaskInstrumentor().instrument_app(app)
    else:
        app.logger.info("🚫 Tracing disabled.")

    app.config['VERSION'] = os.environ.get('VERSION')
    app.config['EXPIRY_SECONDS'] = int(os.environ.get('TOKEN_EXPIRY_SECONDS'))
    app.config['PRIVATE_KEY'] = open(os.environ.get('PRIV_KEY_PATH'), 'r').read()
    app.config['PUBLIC_KEY'] = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    app.config['TOKEN_NAME'] = 'token'
    # timeout in seconds for calls to the backend
    app.config['BACKEND_TIMEOUT'] = int(os.getenv('BACKEND_TIMEOUT', '4'))
    banking_agent_addr = os.environ.get('AI_BANKING_AGENT_URI_ADDR', 'banking-agent:80')
    app.config["AI_BANKING_AGENT_URI"] = 'http://{}/run'.format(
        banking_agent_addr)
    
    app.logger.info(f"************** At Startup AI_BANKING_AGENT_URI: {app.config['AI_BANKING_AGENT_URI']}")
    return app




if __name__ == "__main__":
    # Create an instance of flask server when called directly
    AIASSISTANT = create_app()
    AIASSISTANT.run()
