import uuid


class CommonGenerator:

    @staticmethod
    def generate_uuid():
        return uuid.uuid4().hex
