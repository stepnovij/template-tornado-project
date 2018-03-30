import os

app_settings = {
    "default_handler_args": dict(status_code=404),
    "env": os.environ.get("ENV", "dev"),
    "port": os.environ.get("APP_PORT", "9000"),
}

proxy_path = {
    '/ai/text/evaluate_provider': os.environ.get("PROXY_URL", "https://www.google.com")
}