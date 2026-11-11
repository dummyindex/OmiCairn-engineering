from flask_sqlalchemy import SQLAlchemy

alchemy_db: SQLAlchemy = SQLAlchemy()

class SerializableModel(alchemy_db.Model):
    __abstract__ = True

    def _underscore_to_camelcase(underscore_str):
        words = underscore_str.split('_')
        camelcase_str = words[0] + ''.join(word.capitalize() for word in words[1:])
        return camelcase_str

    def to_dict(self):
        return {self._underscore_to_camelcase(c.name): getattr(self, c.name, None) for c in self.__table__.columns}
