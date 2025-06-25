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
            # Handle different return types from run() method
            if hasattr(container, 'short_id'):
                # Container object returned directly
                return {
                    "id": container.short_id,
                    "name": container.name,
                    "status": "running" if detach else "created",
                    "image": image
                }
            else:
                # Handle cases where container ID is returned as string
                container_id = str(container)
                container_obj = self.client.containers.get(container_id)
                return {
                    "id": container_obj.short_id,
                    "name": container_obj.name,
                    "status": "running" if detach else "created",
                    "image": image
                }
        except Exception as e:
            return {"error": str(e)}

    def create_container(self, image, command=None, name=None):
        """
        Creates a new container without starting it.
        :param image: The image to use (e.g., 'docker.io/library/alpine').
        :param command: The command to run inside the container.
        :param name: Optional name for the container.
        :return: Info about the newly created container.
        """
        try:
            container = self.client.containers.create(
                image=image,
                command=command,
                name=name
            )
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "created",
                "image": image
            }
        except Exception as e:
            return {"error": str(e)}

    def start_container(self, container_id):
        """
        Starts a stopped container.
        :param container_id: The ID or name of the container to start.
        :return: A dictionary confirming the action.
        """
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "started"
            }
        except Exception as e:
            return {"error": str(e)}

    def stop_container(self, container_id):
        """
        Stops a running container.
        :param container_id: The ID or name of the container to stop.
        :return: A dictionary confirming the action.
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "stopped"
            }
        except Exception as e:
            return {"error": str(e)}

    def restart_container(self, container_id):
        """
        Restarts a container.
        :param container_id: The ID or name of the container to restart.
        :return: A dictionary confirming the action.
        """
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "restarted"
            }
        except Exception as e:
            return {"error": str(e)}

    def remove_container(self, container_id, force=False):
        """
        Removes a container.
        :param container_id: The ID or name of the container to remove.
        :param force: If True, forcefully removes the container even if running.
        :return: A dictionary confirming the action.
        """
        try:
            container = self.client.containers.get(container_id)
            container_name = container.name
            container_short_id = container.short_id
            container.remove(force=force)
            return {
                "id": container_short_id,
                "name": container_name,
                "status": "removed"
            }
        except Exception as e:
            return {"error": str(e)}

    def pause_container(self, container_id):
        """
        Pauses a running container.
        :param container_id: The ID or name of the container to pause.
        :return: A dictionary confirming the action.
        """
        try:
            container = self.client.containers.get(container_id)
            container.pause()
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "paused"
            }
        except Exception as e:
            return {"error": str(e)}

    def unpause_container(self, container_id):
        """
        Unpauses a paused container.
        :param container_id: The ID or name of the container to unpause.
        :return: A dictionary confirming the action.
        """
        try:
            container = self.client.containers.get(container_id)
            container.unpause()
            return {
                "id": container.short_id,
                "name": container.name,
                "status": "unpaused"
            }
        except Exception as e:
            return {"error": str(e)}

    def get_container_logs(self, container_id, tail="all", since=None, follow=False):
        """
        Gets logs from a container.
        :param container_id: The ID or name of the container.
        :param tail: Number of lines to show from end of logs (default: "all").
        :param since: Show logs since timestamp or duration (e.g., "1h").
        :param follow: Follow log output (default: False).
        :return: Container logs as a string.
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, since=since, follow=follow)
            if isinstance(logs, bytes):
                return {"logs": logs.decode('utf-8')}
            return {"logs": str(logs)}
        except Exception as e:
            return {"error": str(e)}

    def exec_command(self, container_id, command, workdir=None):
        """
        Executes a command in a running container.
        :param container_id: The ID or name of the container.
        :param command: The command to execute.
        :param workdir: Working directory for the command.
        :return: The command output.
        """
        try:
            container = self.client.containers.get(container_id)
            if workdir:
                result = container.exec_run(command, workdir=workdir)
            else:
                result = container.exec_run(command)

            # Handle different result types
            if hasattr(result, 'exit_code') and hasattr(result, 'output'):
                output = result.output.decode('utf-8') if isinstance(result.output, bytes) else str(result.output)
                return {
                    "exit_code": result.exit_code,
                    "output": output
                }
            elif isinstance(result, tuple) and len(result) >= 2:
                # Handle tuple return (exit_code, output)
                exit_code, output = result[0], result[1]
                output_str = output.decode('utf-8') if isinstance(output, bytes) else str(output)
                return {
                    "exit_code": exit_code,
                    "output": output_str
                }
            else:
                return {"error": "Unexpected result format from exec_run"}
        except Exception as e:
            return {"error": str(e)}

    def list_images(self, all=False):
        """
        Lists container images.
        :param all: If True, shows all images including intermediate ones.
        :return: A list of images with their basic info.
        """
        try:
            images = self.client.images.list(all=all)
            return [
                {
                    "id": img.short_id,
                    "tags": img.tags,
                    "size": img.attrs.get('Size', 0),
                    "created": img.attrs.get('Created', '')
                }
                for img in images
            ]
        except Exception as e:
            return {"error": str(e)}

    def pull_image(self, repository, tag="latest"):
        """
        Pulls an image from a registry.
        :param repository: The repository name (e.g., 'alpine').
        :param tag: The tag to pull (default: 'latest').
        :return: Info about the pulled image.
        """
        try:
            result = self.client.images.pull(repository, tag=tag)
            # Handle different return types from pull()
            if isinstance(result, list) and len(result) > 0:
                image = result[0]  # Get first image from list
            else:
                image = result

            if hasattr(image, 'short_id'):
                return {
                    "id": image.short_id,
                    "tags": image.tags if hasattr(image, 'tags') else [],
                    "status": "pulled"
                }
            else:
                # If we can't get image details, just return success
                return {
                    "repository": repository,
                    "tag": tag,
                    "status": "pulled"
                }
        except Exception as e:
            return {"error": str(e)}

    def remove_image(self, image_id, force=False):
        """
        Removes an image.
        :param image_id: The ID or name of the image to remove.
        :param force: If True, forcefully removes the image.
        :return: A dictionary confirming the action.
        """
        try:
            image = self.client.images.get(image_id)
            image_tags = image.tags
            image_short_id = image.short_id
            self.client.images.remove(image_id, force=force)
            return {
                "id": image_short_id,
                "tags": image_tags,
                "status": "removed"
            }
        except Exception as e:
            return {"error": str(e)}

    def get_system_info(self):
        """
        Gets Podman system information.
        :return: System information dictionary.
        """
        try:
            info = self.client.info()
            return info
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
                "description": "Lists Podman containers.",
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
                        },
                        "detach": {
                            "type": "boolean",
                            "description": "Run container in background (default: True)."
                        }
                    },
                    "required": ["image"]
                }
            },
            "create_container": {
                "description": "Create a new container without starting it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image": {
                            "type": "string",
                            "description": "The container image to use."
                        },
                        "command": {
                            "type": "string",
                            "description": "The command to execute in the container."
                        },
                        "name": {
                            "type": "string",
                            "description": "Optional name for the container."
                        }
                    },
                    "required": ["image"]
                }
            },
            "start_container": {
                "description": "Start a stopped container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container to start."
                        }
                    },
                    "required": ["container_id"]
                }
            },
            "stop_container": {
                "description": "Stop a running container.",
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
            },
            "restart_container": {
                "description": "Restart a container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container to restart."
                        }
                    },
                    "required": ["container_id"]
                }
            },
            "remove_container": {
                "description": "Remove a container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container to remove."
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force removal even if running (default: False)."
                        }
                    },
                    "required": ["container_id"]
                }
            },
            "pause_container": {
                "description": "Pause a running container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container to pause."
                        }
                    },
                    "required": ["container_id"]
                }
            },
            "unpause_container": {
                "description": "Unpause a paused container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container to unpause."
                        }
                    },
                    "required": ["container_id"]
                }
            },
            "get_container_logs": {
                "description": "Get logs from a container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container."
                        },
                        "tail": {
                            "type": "string",
                            "description": "Number of lines to show from end (default: 'all')."
                        },
                        "since": {
                            "type": "string",
                            "description": "Show logs since timestamp or duration."
                        },
                        "follow": {
                            "type": "boolean",
                            "description": "Follow log output (default: False)."
                        }
                    },
                    "required": ["container_id"]
                }
            },
            "exec_command": {
                "description": "Execute a command in a running container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "The ID or name of the container."
                        },
                        "command": {
                            "type": "string",
                            "description": "The command to execute."
                        },
                        "workdir": {
                            "type": "string",
                            "description": "Working directory for the command."
                        }
                    },
                    "required": ["container_id", "command"]
                }
            },
            "list_images": {
                "description": "List container images.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "Show all images including intermediate ones (default: False)."
                        }
                    }
                }
            },
            "pull_image": {
                "description": "Pull an image from a registry.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "The repository name (e.g., 'alpine')."
                        },
                        "tag": {
                            "type": "string",
                            "description": "The tag to pull (default: 'latest')."
                        }
                    },
                    "required": ["repository"]
                }
            },
            "remove_image": {
                "description": "Remove an image.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string",
                            "description": "The ID or name of the image to remove."
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force removal (default: False)."
                        }
                    },
                    "required": ["image_id"]
                }
            },
            "get_system_info": {
                "description": "Get Podman system information.",
                "parameters": {
                    "type": "object",
                    "properties": {}
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
