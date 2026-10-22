class ComputationStateException(Exception):
    def __init__(self, msg=None):
        error_message = msg or "computation state error."
        super().__init__(error_message)
