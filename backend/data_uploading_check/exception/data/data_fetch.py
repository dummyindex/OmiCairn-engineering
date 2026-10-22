class DataFetchException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "data fetch failed."
        super().__init__(error_message)
