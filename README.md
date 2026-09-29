# IP Lookup Chatbot with LangGraph and Azure OpenAI

A small Flask web app with a chat interface for questions about an IP address. The chat logic runs as a LangGraph graph: general questions go to an Azure OpenAI chat model, and requests for the IP's details are answered with live data from the IPStack API.

## How it works

1. When the page loads, the bot asks for an IP address. The first message must be a valid IPv4 or IPv6 address, and it is stored in the Flask session.
2. Every message after that goes through a one-node LangGraph `StateGraph` whose state holds the chat messages and the IP address.
3. If the message contains "details of my IP", the node looks the IP up with IPStack and returns the result.
4. Otherwise the message is sent to Azure OpenAI with a system prompt that tells the model to answer as an IP specialist.
5. If the model returns an empty answer, its answer contains "I'm sorry", or the call fails, the node falls back to the IPStack lookup.
6. Reloading the page clears the stored IP, so you can start again with a different address.

## Features

- Chat page built with Bootstrap 5 and plain JavaScript: dark theme, message bubbles and a loading spinner
- LangGraph state graph around an Azure OpenAI chat model
- IP geolocation lookup through the IPStack API
- IP address check and per-session storage with Flask sessions
- Keys and settings loaded from a `.env` file

## Tech stack

- Python, Flask
- LangGraph, LangChain (`langchain-core`, `langchain-openai`)
- Azure OpenAI
- IPStack API
- HTML, CSS, JavaScript, Bootstrap 5

## Project structure

```
.
├── app.py               # Flask routes, LangGraph graph and IPStack lookup
├── templates/
│   └── chatbot.html     # Chat page and client-side script
├── static/
│   └── css/style.css    # Chat page styles
├── requirements.txt
└── .env.example         # Environment variables to copy into .env
```

## Setup

You need Python 3.10 or newer, an Azure OpenAI resource with a chat model deployment, and an IPStack access key.

```bash
git clone https://github.com/Hamza-Tahirr/React-Chat-App-Using-LangGraph-Tools-Agents.git
cd React-Chat-App-Using-LangGraph-Tools-Agents

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values:

| Variable | Description |
| --- | --- |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Endpoint of your Azure OpenAI resource |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Name of the chat model deployment |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version, for example `2024-06-01` |
| `IPSTACK_API_KEY` | IPStack access key |
| `FLASK_SECRET_KEY` | Secret used to sign the Flask session cookie |

The app will not start without the four Azure OpenAI variables. If `IPSTACK_API_KEY` is missing, IP lookups return an error message instead. If `FLASK_SECRET_KEY` is missing, a random key is created at startup, so sessions reset whenever the app restarts.

## Run

```bash
python app.py
```

Then open http://127.0.0.1:5000. The app runs with Flask's debug mode turned on, so use it for local development only.

Example conversation:

1. Enter an IP address, for example `8.8.8.8`.
2. Ask a general question such as "What is the difference between IPv4 and IPv6?"
3. Type "Show me the details of my IP" to get the IPStack lookup for the address you entered.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
