class NotRemovableException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "the element is not removable."
        super().__init__(error_message)
