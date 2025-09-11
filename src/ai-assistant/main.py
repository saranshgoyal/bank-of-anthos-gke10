# Copyright 2024 Google LLC
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

import os
import logging
from flask import Flask, request, jsonify

# TODO: Import generated gRPC stubs for Bank of Anthos services
# from gen import ...

# TODO: Import Gemini client library
# from google.cloud import aiplatform
# import vertexai
# from vertexai.generative_models import GenerativeModel

# --- Boilerplate Setup ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Initialize Vertex AI
# try:
#     project_id = os.environ.get("PROJECT_ID")
#     location = os.environ.get("REGION", "us-central1")
#     vertexai.init(project=project_id, location=location)
#     model = GenerativeModel("gemini-1.0-pro")
#     logger.info("Vertex AI initialized successfully.")
# except Exception as e:
#     logger.error(f"Error initializing Vertex AI: {e}")
#     model = None

# --- Helper Functions ---

def get_intent_from_gemini(user_message: str) -> dict:
    """
    Uses Gemini to parse the user's message and extract intent and entities.
    """
    logger.info(f"Getting intent for message: '{user_message}'")

    # --- MOCK IMPLEMENTATION ---
    # Replace this with the actual Gemini call.
    logger.warning("Using MOCK implementation for Gemini. Replace for production.")
    if "balance" in user_message.lower():
        return {"intent": "get_balance", "entities": {}}
    elif "transaction" in user_message.lower():
        return {"intent": "list_transactions", "entities": {"limit": 5}}
    elif "send" in user_message.lower() and ("$" in user_message or "to" in user_message):
        amount = 25.0 # default
        for word in user_message.split():
            if word.startswith('$'):
                try:
                    amount = float(word[1:])
                except ValueError:
                    pass
        return {"intent": "send_money", "entities": {"amount": amount, "recipient": "friend"}}
    else:
        return {"intent": "unknown", "entities": {}}
    # --- END MOCK ---

def execute_action(intent_data: dict, auth_token: str) -> str:
    """
    Calls the appropriate Bank of Anthos microservice based on the intent.
    """
    intent = intent_data.get("intent")
    entities = intent_data.get("entities", {})
    logger.info(f"Executing action for intent: '{intent}' with entities: {entities}")

    # TODO: Set up gRPC channels to other services using their k8s service names.
    # balancereader_channel = grpc.insecure_channel(os.environ.get("BALANCE_READER_SERVICE_ADDR"))

    if intent == "get_balance":
        # TODO: Call balancereader service via gRPC
        return "Your checking account balance is $1,234.56. (mocked)"

    elif intent == "list_transactions":
        # TODO: Call transactionhistory service via gRPC
        return "Here are your last 5 transactions: ... (mocked)"

    elif intent == "send_money":
        # TODO: Call accounts service via gRPC
        amount = entities.get('amount', 0)
        recipient = entities.get('recipient', 'unknown')
        return f"Transaction initiated to send ${amount} to {recipient}. (mocked)"

    elif intent == "unknown":
        return "I'm sorry, I don't understand. I can check balances, list transactions, or send money."

    else:
        return "I'm sorry, something went wrong processing your request."

# --- API Endpoint ---

@app.route("/chat", methods=["POST"])
def chat():
    """
    Main endpoint to handle user chat messages.
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Invalid request. 'message' is required."}), 400

    user_message = data["message"]
    auth_token = request.headers.get("Authorization", "Bearer FAKE_JWT_TOKEN")

    # 1. Get intent from Gemini (or mock)
    intent_data = get_intent_from_gemini(user_message)
    if "error" in intent_data:
        return jsonify({"response": intent_data["error"]}), 500

    # 2. Execute the corresponding action (or mock)
    response_message = execute_action(intent_data, auth_token)

    # 3. Return the response to the user
    return jsonify({"response": response_message})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)