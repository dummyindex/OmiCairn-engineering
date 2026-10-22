from dto import Dto
from collections import OrderedDict
class FunctionBlockSearchDTO(Dto):
    # Return type for search results
    def __init__(self, fb_id, fb_name, fb_alt_name, description, source):
        self.fb_id = fb_id
        self.fb_name = fb_name
        self.fb_alt_name = fb_alt_name
        self.description = description
        self.source = source
        # self.priority = priority
    def to_dict(self):
        return OrderedDict([
            ("fb_id", self.fb_id),
            ("fb_name", self.fb_name),
            ("fb_alt_name", self.fb_alt_name),
            ("description", self.description),
            ("source", self.source),
            # ("priority", self.priority)
        ])