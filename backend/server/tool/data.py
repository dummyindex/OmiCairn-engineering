from constants.data import DataListFetchMode
from exception.data.data_fetch import DataFetchException


class DataTool:
    @staticmethod
    def check_data_list_fetch_mode(mode):
        value_range = DataListFetchMode.__members__.values()
        if mode not in DataListFetchMode.__members__.values():
            raise DataFetchException(
                f"invalid mode. mode must be one of {value_range}"
            )
