class DataDeleteException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "data deleted failed."
        super().__init__(error_message)
