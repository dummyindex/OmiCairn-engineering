class ConvertToComponentException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "convert to component failed."
        super().__init__(error_message)
