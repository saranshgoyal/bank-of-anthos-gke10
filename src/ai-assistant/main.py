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
import json
from flask import Flask, request, jsonify

# TODO: Import generated gRPC stubs for Bank of Anthos services
# from gen import ...

# Import ADK and Gemini client libraries
from google.adk.agents import Agent
# from google.adk.tools import tool
import vertexai
from vertexai.generative_models import GenerativeModel

# --- Boilerplate Setup ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Agent Tools ---
# The ADK will use the function's docstring to understand what the tool does.
# The type hints (e.g., amount: float) are used to generate the tool's schema.


GOOGLE_GENAI_USE_VERTEXAI=True

def get_balance() -> str:
    """Gets the current balance for the user's checking account."""
    logger.info("Executing tool: get_balance")
    # TODO: Set up gRPC channel and call balancereader service.
    # This is where you would make the real gRPC call.
    return "Your checking account balance is $1,234.56. (mocked)"


def list_transactions(limit: int = 5) -> str:
    """Lists the most recent transactions for the user, up to a specified limit."""
    logger.info(f"Executing tool: list_transactions with limit={limit}")
    # TODO: Set up gRPC channel and call transactionhistory service.
    return f"Here are your last {limit} transactions: ... (mocked)"


def send_money(amount: float, recipient: str) -> str:
    """
    Sends a specified amount of money to a recipient.

    Args:
        amount: The numeric amount of money to send.
        recipient: The name or account number of the person to send money to.
    """
    logger.info(f"Executing tool: send_money with amount=${amount}, recipient='{recipient}'")
    # TODO: Set up gRPC channel and call accounts service.
    return f"Transaction initiated to send ${amount} to {recipient}. (mocked)"

# --- Agent Initialization ---
# Use one of the model constants defined earlier
MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"
AGENT_MODEL = MODEL_GEMINI_2_5_FLASH

try:
    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("REGION", "us-central1")
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(
        AGENT_MODEL,
        # Pass instructions to the model, not the agent
        system_instruction="You are a friendly and helpful banking assistant. Understand the user inputs and use the available tools to assist. If you don't have the required tools to fulfill the request, simply say that you cannot process this request."
    )
    # Create an agent with our defined tools
    agent = Agent(
        name="banking-assistant",
        model=model,
        description=(
        "Agent to answer questions about the Banking Related Services."),
        tools=[get_balance, list_transactions, send_money],
    )

    logger.info("Vertex AI and ADK Agent initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing Vertex AI or Agent: {e}")
    root_agent = None # Set agent to None if initialization fails

# --- API Endpoint ---

@app.route("/chat", methods=["POST"])
def chat():
    """Main endpoint to handle user chat messages using the ADK Agent."""
    if not agent:
        return jsonify({"error": "Agent not initialized. Check logs for details."}), 503

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Invalid request. 'message' is required."}), 400

    user_message = data["message"]
    logger.info(f"Received message: '{user_message}'")

    # Let the agent handle the entire reasoning process
    try:
        response_message = agent.run(user_message)
        logger.info(f"Agent response: '{response_message}'")
        return jsonify({"response": response_message})
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)