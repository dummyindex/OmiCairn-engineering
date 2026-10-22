from datetime import datetime, timedelta
from dao.library import library_dao
from dao.organism import organism_dao
from model.organism import Organism
from model.library import Library
import gseapy as gp
from constants.gseapy import ORGANISM_LIST


class GseapyService:

    def library_name_list_get(self, organism_name: str):
        now = datetime.now()
        organism: Organism = organism_dao.find_by_organism_name(organism_name)
        latest_update_time: datetime = organism.latest_update_time
        delta_duration: timedelta = now - latest_update_time
        if delta_duration.total_seconds() > 60 * 60 * 24:
            library_name_list = gp.get_library_name(organism=organism_name)
            library_dao.delete_by_organism_id(organism.id)
            library_list = [
                Library(
                    library_name=library_name,
                    organism_id=organism.id
                )
                for library_name in library_name_list
            ]
            library_dao.insert_list(library_list)
            organism_dao.update_latest_update_time(
                organism_id=organism.id,
                latest_update_time=now
            )
            return library_name_list
        else:
            library_list = library_dao.find_by_organism_id(organism.id)
            return [library.library_name for library in library_list]

    def whole_library_name_list_get(self):
        result = []
        for organism in ORGANISM_LIST:
            result += self.library_name_list_get(organism_name=organism)
        return result

gseapy_service = GseapyService()
