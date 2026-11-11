class NotOperatableException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "This operation is not allowed on this object."
        super().__init__(error_message)
