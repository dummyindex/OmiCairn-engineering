from db import alchemy_db as db
from model.organism import Organism
from typing import List


class OrganismDao:
    def insert(self, organism: Organism) -> None:
        db.session.add(organism)
        db.session.flush()

    def find_by_id(self, id) -> Organism:
        return Organism.query.filter(
            Organism.id == id
        ).first()

    def find_by_organism_name(self, organism_name) -> Organism:
        return Organism.query.filter(
            Organism.organism_name == organism_name
        ).first()

    def find_all(self) -> List[Organism]:
        return Organism.query.all()

    def update_latest_update_time(self, organism_id, latest_update_time) -> None:
        Organism.query.filter(
            Organism.id == organism_id
        ).update({"latest_update_time": latest_update_time})


organism_dao = OrganismDao()
