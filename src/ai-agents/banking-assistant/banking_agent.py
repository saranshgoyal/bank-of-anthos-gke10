# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# @title Import necessary libraries
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# @title Define the get_balance Tool
def get_balance() -> str:
    """
    Gets the current balance for the user's checking account.    
    """
    logger.info("Executing tool: get_balance")
    # TODO: Set up gRPC channel and call balancereader service.
    # This is where you would make the real gRPC call.
    return "Your checking account balance is $1,234.56. (mocked)"


# @title Define the list_transactions Tool
def list_transactions(limit: int = 5) -> str:
    """
    Lists the most recent transactions for the user, up to a specified limit.
    """
    logger.info(f"Executing tool: list_transactions with limit={limit}")
    # TODO: Set up gRPC channel and call transactionhistory service.
    return f"Here are your last {limit} transactions: ... (mocked)"

# @title Define the send_money Tool
def send_money(amount: float, recipient: str) -> str:
    """
    Sends a specified amount of money to a recipient.

    Args:
        amount: The numeric amount of money to send.
        recipient: The name or account number of the person to send money to.
        
    """

    # {"account_num": "9099791699", "routing_num": "808889588" }
    #account=%7B%22account_num%22%3A+%229099791699%22%2C+%22routing_num%22%3A+%22808889588%22+%7D&external_account_num=&external_routing_num=&external_label=&amount=25&uuid=ed6bb2f2-6ef0-4e12-ab48-78eb622e2398

    logger.info(f"Executing tool: send_money with amount=${amount}, recipient='{recipient}'")
    # TODO: Set up gRPC channel and call accounts service.
    return f"Transaction initiated to send ${amount} to {recipient}. (mocked)"


# @title Define the get_weather Tool
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {city} ---") # Log tool execution
    city_normalized = city.lower().replace(" ", "") # Basic normalization

    # Mock weather data
    mock_weather_db = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "tokyo": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."}

# # Example tool usage (optional test)
# print(get_weather("New York"))
# print(get_weather("Paris"))

# @title Define the Weather Agent

# --- Agent Initialization ---
# Use one of the model constants defined earlier
MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"
AGENT_MODEL = MODEL_GEMINI_2_5_FLASH


root_agent = Agent(
    name="banking_agent",
    model=AGENT_MODEL, # Can be a string for Gemini or a LiteLlm object
    description="Provides answer questions about the Banking Related Services.",
    instruction="You are a friendly and helpful banking assistant." 
                 " Understand the user inputs and use the available tools to assist." 
                 " If you don't have the required tools to fulfill the request," 
                 " simply say that you cannot process this request.",
    tools=[get_balance, list_transactions, send_money],
)

# Sample queries to test the agent: 

# # Agent will give weather information for the specified cities.
# # What's the weather in Tokyo?
# # What is the weather like in London?
# # Tell me the weather in New York?

# # Agent will not have information for the specified city.
# # How about Paris?  