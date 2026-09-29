import ipaddress
import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai.chat_models.azure import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Annotated
from typing_extensions import TypedDict

# Load environment variables
load_dotenv()

# Azure OpenAI settings
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
IPSTACK_API_KEY = os.getenv("IPSTACK_API_KEY")

# Ensure the API key is loaded
if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_DEPLOYMENT_NAME or not AZURE_OPENAI_API_VERSION:
    raise ValueError("Azure OpenAI API credentials are missing in .env file.")

# Define a state structure for LangGraph
class State(TypedDict):
    messages: Annotated[list, add_messages]
    ip_address: str  # Ensure ip_address is included in the state

# Initialize LangGraph state graph
graph_builder = StateGraph(State)

# Define the system prompt for Azure OpenAI
SYSTEM_PROMPT = "You are an IP specialist and you will answer the given prompt by using your knowledge."

# Initialize AzureChatOpenAI model
llm = AzureChatOpenAI(
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    openai_api_key=AZURE_OPENAI_API_KEY,
    openai_api_version=AZURE_OPENAI_API_VERSION
)

# Flask app initialization
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(24)

# Function to fetch IP details using IPStack API
def fetch_ip_details(ip_address: str):
    if not IPSTACK_API_KEY:
        return {"error": "IPSTACK_API_KEY is not set"}
    try:
        response = requests.get(
            f"https://api.ipstack.com/{ip_address}",
            params={"access_key": IPSTACK_API_KEY},
            timeout=10,
        )
    except requests.RequestException:
        return {"error": "Failed to fetch IP details"}
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch IP details"}

# Answer with the LLM, or fall back to an IPStack lookup for the user's IP
def chatbot(state: State):
    user_message = state["messages"][-1].content

    if "details of my ip" in user_message.lower():
        ip_address = state["ip_address"]
        ip_details = fetch_ip_details(ip_address)
        return {"messages": [AIMessage(content=str(ip_details))]}

    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)]
        llm_response = llm.invoke(messages)

        if not llm_response.content or "I'm sorry" in llm_response.content:
            ip_address = state["ip_address"]
            ip_details = fetch_ip_details(ip_address)
            return {"messages": [AIMessage(content=str(ip_details))]}

        return {"messages": [AIMessage(content=llm_response.content)]}

    except Exception as e:
        print(f"Error occurred: {e}")
        ip_address = state["ip_address"]
        ip_details = fetch_ip_details(ip_address)
        return {"messages": [AIMessage(content=str(ip_details))]}

# Add chatbot node to LangGraph
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph
graph = graph_builder.compile()

# Flask route for chatbot page
@app.route('/')
def index():
    # The page always starts by asking for an IP, so drop any old one
    session.pop('ip_address', None)
    return render_template('chatbot.html')

# Flask route to handle user input (AJAX call)
@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form.get('message', '').strip()

    if 'ip_address' not in session:
        # First interaction: Ask for the user's IP
        try:
            ipaddress.ip_address(user_input)
        except ValueError:
            return jsonify({'response': "That doesn't look like a valid IP address. Please try again."})
        session['ip_address'] = user_input  # Store the provided IP address in session
        response_message = "Ask me anything about your IP."
    else:
        # If IP is already provided, proceed with chatbot logic
        ip_address = session['ip_address']
        result = graph.invoke(
            {"messages": [HumanMessage(content=user_input)], "ip_address": ip_address}
        )
        response_message = result["messages"][-1].content

    return jsonify({'response': response_message})

if __name__ == '__main__':
    app.run(debug=True)
