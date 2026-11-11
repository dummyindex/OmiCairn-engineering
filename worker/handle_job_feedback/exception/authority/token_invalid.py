class TokenInvalidException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "token is invalid."
        super().__init__(error_message)
