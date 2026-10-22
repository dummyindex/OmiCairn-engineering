class SSSUploadFileException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "save file unsuccessfully."
        super().__init__(error_message)
