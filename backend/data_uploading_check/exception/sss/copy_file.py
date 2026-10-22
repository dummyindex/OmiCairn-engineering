class SSSCopyFileException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "copy file unsuccessfully."
        super().__init__(error_message)
