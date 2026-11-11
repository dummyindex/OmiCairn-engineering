class NoAuthorityException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "no authority."
        super().__init__(error_message)
