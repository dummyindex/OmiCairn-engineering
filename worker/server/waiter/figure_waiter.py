from sss.porter_factory import PorterFactory
from constants.sss import FIGURE_FOLDER_PREFIX


class FigureWaiter:
    def __init__(self, figure_uuid) -> None:
        self.porter = PorterFactory.create_porter()
        self.figure_uuid = figure_uuid
        self.object_key = f"{FIGURE_FOLDER_PREFIX}/{figure_uuid}"
        self.porter.set_operation_target(self.object_key)

    def check_file(self):
        return self.porter.check_file()

    def get_download_info_with_suffix(self, suffix):
        new_object_key = f"{self.object_key}.{suffix}"
        new_porter = PorterFactory.create_porter()
        new_porter.set_operation_target(new_object_key)
        new_porter.copy_file(self.porter.get_bucket_name(), self.object_key)
        return new_porter.get_presigned_url(60 * 60)

    def get_download_info(self):
        return self.porter.get_presigned_url(60 * 60)
