import os

GPT_SERVER_HOST = os.environ.get("GPT_SERVER_HOST")
GPT_SERVER_PORT = os.environ.get("GPT_SERVER_PORT")

GPT_WORKFLOW_SERVER_HOST = os.environ.get("GPT_WORKFLOW_SERVER_HOST")
GPT_WORKFLOW_SERVER_PORT = os.environ.get("GPT_WORKFLOW_SERVER_PORT")

NETWORK_PROXY_HOST = os.environ.get("NETWORK_PROXY_HOST")
NETWORK_PROXY_PORT = os.environ.get("NETWORK_PROXY_PORT")

# Optional outbound HTTP proxy; requests uses no proxy when unset.
PROXIES = {
    "http": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}",
    "https": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}"
} if NETWORK_PROXY_HOST and NETWORK_PROXY_PORT else None
