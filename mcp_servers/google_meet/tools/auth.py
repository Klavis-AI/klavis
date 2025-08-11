from contextvars import ContextVar

auth_token_context: ContextVar[str] = ContextVar('auth_token')
# We're using a ContextVar here to store the auth token for each async request. 
# This way, even if requests overlap, each one gets its own token without mixing them up.


def get_auth_token() -> str:
    """
    Grab the token from the current context, clean it up, and check if it's valid. 
    If something's wrong, we throw an error to stop things early.
    """
    try:
        token = auth_token_context.get()
        token = token.strip()
        if not token:
            raise RuntimeError("Missing OAuth access token. Pass a valid token in the x-auth-token header.")
        if len(token) < 10:
            raise RuntimeError("Invalid access token format. Token is too short.")
        if len(token) > 4096:
            raise RuntimeError("Invalid access token format. Token is too long.")
        if not all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~:/?#[]@!$&'()*+,;=" for c in token):
            raise RuntimeError("Invalid access token format. Token contains invalid characters.")
        return token
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")
