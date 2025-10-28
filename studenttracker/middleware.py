class PrefixMiddleware:
    """Keep Flask aware of a deployment prefix (e.g., /app) when present."""

    def __init__(self, app, default_prefix=""):
        self.app = app
        self.default_prefix = default_prefix.rstrip("/") if default_prefix else ""

    def __call__(self, environ, start_response):
        header_prefix = environ.get("HTTP_X_SCRIPT_NAME") or environ.get("HTTP_X_FORWARDED_PREFIX") or ""
        active_prefix = header_prefix or self.default_prefix
        if not active_prefix:
            return self.app(environ, start_response)

        cleaned_prefix = active_prefix.rstrip("/")
        path_info = environ.get("PATH_INFO", "")

        if cleaned_prefix and path_info.startswith(cleaned_prefix):
            environ["SCRIPT_NAME"] = cleaned_prefix
            environ["PATH_INFO"] = path_info[len(cleaned_prefix):] or "/"
        else:
            environ["SCRIPT_NAME"] = cleaned_prefix

        environ.setdefault("HTTP_X_FORWARDED_PREFIX", environ["SCRIPT_NAME"])

        return self.app(environ, start_response)
