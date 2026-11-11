class ParameterInvalidException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "parameters are invalid."
        super().__init__(error_message)
