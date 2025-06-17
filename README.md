# podman-mcp-server

Podman MCP Server uses the `podman-py` library to interface with Podman's API.

The created MCP server listens for JSON-RPC 2.0 requests, as specified by the MCP standard, and routes them to Podman tools.

## Installation

### Start Podman API Service

The `podman-py` library communicates with the Podman REST API, enable this service.

Open a terminal and run the following command. This will start the API service and keep it running in the background.

```
$ podman system service --time=0 &
```

### Python Environment Setup

Use the python virtual environmental setup for development purposes

```
# Clone the project

$ git clone https://github.com/mohanboddu/podman-mcp-server
$ cd podman-mcp-server

# Create and activate a virtual environment

$ python3 -m venv .venv
$ source .venv/bin/activate
```

### Installing Dependencies

This setup up uses two main libraries

* podman: The official client library for the Podman REST API.
* werkzeug: A robust WSGI utility library that we will use to easily handle the HTTP and JSON-RPC parts of our server.

Install them using pip:

```
$ pip install podman werkzeug
```

### Running the MCP Server

Execute the script with the virtual environment activated in the terminal:

```
python mcp_server.py
```

### Testing the running MCP Server

Once the server is running, you can now act as an MCP client by sending JSON-RPC requests using curl.

Open a new terminal and run:

```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' \
  http://127.0.0.1:4000
```

The server should respond with the JSON manifest of all available tools.
