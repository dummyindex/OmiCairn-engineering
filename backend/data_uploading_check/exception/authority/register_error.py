class RegisterErrorException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "register error."
        super().__init__(error_message)
