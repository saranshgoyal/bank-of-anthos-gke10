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

import bcrypt
import jwt
from flask import Flask, jsonify, request

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
            

            # Return a success response
            # return jsonify({"status": "success", "received_message": message}), 200
            return jsonify({"response": f"I am a virtual assistant. You said: {message}"}), 200

        else:
            # Return an error response if the message is missing
            return jsonify({"response": "Please say something....."}), 400

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
    return app


if __name__ == "__main__":
    # Create an instance of flask server when called directly
    AIASSISTANT = create_app()
    AIASSISTANT.run()
