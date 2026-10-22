class DataCollectException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "data collected failed."
        super().__init__(error_message)
