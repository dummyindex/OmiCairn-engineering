from db import alchemy_db as db


class Organism(db.Model):
    __tablename__ = "organism"
    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, comment='ID')
    organism_name = db.Column(db.String(45))
    latest_update_time = db.Column(db.DateTime)

    def to_dict(self):
        attrs_dict = dict()
        attrs_dict["id"] = self.id
        attrs_dict["organism_name"] = self.organism_name
        attrs_dict["latest_update_time"] = self.latest_update_time.timestamp() * \
            1000
        return attrs_dict
