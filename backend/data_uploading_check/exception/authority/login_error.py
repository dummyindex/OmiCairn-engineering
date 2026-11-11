class LoginErrorException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "login error."
        super().__init__(error_message)
