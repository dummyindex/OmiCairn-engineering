class DataComponentAssembleException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "data component assemble failed."
        super().__init__(error_message)
