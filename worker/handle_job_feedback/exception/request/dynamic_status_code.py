class DynamicStatusCode(Exception):
    def __init__(self, code, msg:str) -> None:
        self.code = code
        super().__init__(msg)

    def get_code(self):
        return self.code
