import os

GPT_SERVER_HOST = os.environ.get("GPT_SERVER_HOST", "localhost")
GPT_SERVER_PORT = os.environ.get("GPT_SERVER_PORT", "5000")

GPT_WORKFLOW_SERVER_HOST = os.environ.get("GPT_WORKFLOW_SERVER_HOST", "localhost")
GPT_WORKFLOW_SERVER_PORT = os.environ.get("GPT_WORKFLOW_SERVER_PORT", "5000")

# Optional outbound HTTP proxy. Leave NETWORK_PROXY_HOST unset to connect directly.
NETWORK_PROXY_HOST = os.environ.get("NETWORK_PROXY_HOST")
NETWORK_PROXY_PORT = os.environ.get("NETWORK_PROXY_PORT")

if NETWORK_PROXY_HOST:
    _proxy_url = f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}" if NETWORK_PROXY_PORT else f"http://{NETWORK_PROXY_HOST}"
    PROXIES = {
        "http": _proxy_url,
        "https": _proxy_url
    }
else:
    PROXIES = None
