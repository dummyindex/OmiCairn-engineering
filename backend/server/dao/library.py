from db import alchemy_db as db
from model.library import Library
from typing import List


class LibraryDao:
    def insert(self, library: Library) -> None:
        db.session.add(library)
        db.session.flush()

    def find_by_id(self, id) -> Library:
        return Library.query.filter(
            Library.id == id
        ).first()

    def delete_by_organism_id(self, organism_id) -> None:
        Library.query.filter(
            Library.organism_id == organism_id
        ).delete()

    def find_by_organism_id(self, organism_id) -> List[Library]:
        return Library.query.filter(
            Library.organism_id == organism_id
        ).all()

    def insert_list(self, library_list: List[Library]) -> None:
        db.session.bulk_save_objects(library_list)
        db.session.flush()


library_dao = LibraryDao()
