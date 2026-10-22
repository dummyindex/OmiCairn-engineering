class DataComponentConfirmException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "data component confirmed failed."
        super().__init__(error_message)
