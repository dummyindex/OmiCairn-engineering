class SSSRemoveFileException(Exception):
    def __init__(self, msg):
        error_message = msg or "remove file unsuccessfully."
        super().__init__(error_message)
