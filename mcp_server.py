# mcp_server.py

import json
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from podman import PodmanClient
from podman.domain import containers_manager

# This class will hold all our Podman-related functions
class PodmanTools:
    """A collection of methods to be exposed as MCP tools."""

    def __init__(self):
        self.client = PodmanClient()

    def list_containers(self, all=False):
        """
        Lists containers.
        :param all: If True, shows all containers. Otherwise, only running.
        :return: A list of containers with their basic info.
        """
        try:
            containers = self.client.containers.list(all=all)
            return [
                {
                    "id": c.short_id,
                    "name": c.name,
                    "image": c.image,
                    "status": c.status
                }
                for c in containers
            ]
        except Exception as e:
            return {"error": str(e)}

    def inspect_container(self, container_id):
        """
        Returns detailed information about a specific container.
        :param container_id: The ID or name of the container.
        :return: A dictionary with the container's details.
        """
        try:
            container = self.client.containers.get(container_id)
            return container.attrs
        except Exception as e:
            return {"error": str(e)}

    def run_container(self, image, command=None, detach=True):
        """
        Creates and runs a new container.
        :param image: The image to run (e.g., 'docker.io/library/alpine').
        :param command: The command to run inside the container.
        :param detach: Whether to run the container in the background.
        :return: Info about the newly created container.
        """
        try:
            container = self.client.containers.run(
                image=image,
                command=command,
                detach=detach
            )
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "created",
                "image": image
            }
        except Exception as e:
            return {"error": str(e)}

    def stop_container(self, container_id):
        """
        Stops a running container.
        :param container_id: The ID or name of the container to stop.
        :return: A dcitionary confirming the action.
        """
        try:
            # Get the container object using its ID or name
            container = self.client.containers.get(container_id)
            # Stop the container
            container.stop()
            # Return a confirmation message
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "stopped"
            }
        except Exception as e:
            return {"error": str(e)}


class MCPHandler:
    """Handles MCP JSON-RPC requests and routes them to the right tool."""

    def __init__(self):
        self.podman_tools = PodmanTools()
        # This manifest describes the tools our server provides.
        # An MCP client would first call 'tools/list' to get this.
        self.tools_manifest = {
            "list_containers": {
                "description": "Lists Docker containers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "Show all containers (default: False)."
                        }
                    }
                }
            },
            "inspect_container": {
                "description": "Inspect a specific container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container."
                        }
                    },
                    "required": ["container_id"]
                }
            },
            "run_container": {
                "description": "Run a new container from an image.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image": {
                            "type": "string",
                            "description": "The container image to run (e.g., 'alpine')."
                        },
                        "command": {
                            "type": "string",
                            "description": "The command to execute in the container."
                        }
                    },
                    "required": ["image"]
                }
            },
            "stop_container": {
                "description": "Stop a specific running container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container to stop."
                        }
                    },
                    "required": ["container_id"]
                }
            }
        }

    def handle_request(self, request_data):
        """
        Parses a JSON-RPC request and executes the corresponding method.
        """
        try:
            # Basic validation of the JSON-RPC request structure
            if "method" not in request_data or "jsonrpc" not in request_data:
                return self._create_error_response(-32600, "Invalid Request", request_data.get("id"))

            method_name = request_data["method"]
            params = request_data.get("params", {})
            request_id = request_data.get("id")

            # Handle the standard MCP discovery method
            if method_name == "tools/list":
                return self._create_success_response(self.tools_manifest, request_id)

            # Find the corresponding method in our PodmanTools class
            method_to_call = getattr(self.podman_tools, method_name, None)

            if callable(method_to_call):
                # Call the method with the provided parameters
                result = method_to_call(**params)
                return self._create_success_response(result, request_id)
            else:
                return self._create_error_response(-32601, "Method not found", request_id)

        except Exception as e:
            return self._create_error_response(-32603, f"Internal error: {e}", request_data.get("id"))

    def _create_success_response(self, result, req_id):
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": req_id
        }

    def _create_error_response(self, code, message, req_id):
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": req_id
        }

# Create a global handler instance
mcp_handler = MCPHandler()

@Request.application
def application(request: Request):
    """The main WSGI application to handle incoming HTTP requests."""
    if request.method == 'POST':
        try:
            # Decode the JSON payload from the request body
            request_data = json.loads(request.data)
            # Pass the data to our handler
            response_data = mcp_handler.handle_request(request_data)
            return Response(json.dumps(response_data), mimetype='application/json')
        except json.JSONDecodeError:
            error_resp = mcp_handler._create_error_response(-32700, "Parse error", None)
            return Response(json.dumps(error_resp), status=400, mimetype='application/json')
    else:
        # MCP typically uses POST
        return Response("MCP Server for Podman. Please use POST with a JSON-RPC payload.", status=405)

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 4000
    print(f"Starting Podman MCP Server at http://{host}:{port}")
    run_simple(host, port, application)
