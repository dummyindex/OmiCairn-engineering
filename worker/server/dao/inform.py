from db import alchemy_db as db
from constants.common import LONG_TEXT_MAX_LEN
from model.inform import Inform


class InformDao:

    def insert_inform(self, inform: Inform) -> Inform:
        if inform.payload is not None and len(inform.payload) > LONG_TEXT_MAX_LEN:
            inform.payload = inform.payload[:LONG_TEXT_MAX_LEN]
        db.session.add(inform)
        db.session.flush()
        return inform


inform_dao = InformDao()
