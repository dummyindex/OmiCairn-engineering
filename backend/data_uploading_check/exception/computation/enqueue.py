class ComputationEnqueueException(Exception):
    def __init__(self, msg=None) -> None:
        error_message = msg or "enqueue computation unsuccessfully."
        super().__init__(error_message)
