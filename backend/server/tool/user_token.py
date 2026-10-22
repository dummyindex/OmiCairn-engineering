from datetime import datetime, timedelta

from tool.common_generator import CommonGenerator


class UserTokenTool:

    @staticmethod
    def generate_new_token_value():
        return CommonGenerator.generate_uuid()
