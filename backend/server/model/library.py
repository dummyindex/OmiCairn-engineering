from db import alchemy_db as db


class Library(db.Model):
    __tablename__ = "library"
    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, comment='ID')
    library_name = db.Column(db.String(200))
    organism_id = db.Column(db.Integer)

    def to_dict(self):
        attrs_dict = dict()
        attrs_dict["id"] = self.id
        attrs_dict["library_name"] = self.library_name
        attrs_dict["organism_id"] = self.organism_id
        return attrs_dict
