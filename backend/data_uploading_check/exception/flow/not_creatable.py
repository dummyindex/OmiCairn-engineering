class NotCreatableException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "the element is not creatable."
        super().__init__(error_message)
