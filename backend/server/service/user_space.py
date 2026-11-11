
from waiter.user_space_waiter import UserSpaceWaiter

class UserSpaceService:

    def get_upload_info(self, user_id, prefix, file_name, file_size):
        waiter = UserSpaceWaiter(user_id)
        return waiter.fetch_upload_info(prefix, file_name, file_size)

    def get_download_info(self, user_id, prefix, file_name):
        waiter = UserSpaceWaiter(user_id)
        return waiter.fetch_download_info(prefix, file_name)

    def list_folder(self, user_id, prefix):
        waiter = UserSpaceWaiter(user_id)
        file_list = waiter.list_folder(prefix)
        return file_list

    def collect_file(self, user_id, prefix, file_name):
        waiter = UserSpaceWaiter(user_id)
        waiter.collect_file(user_id, prefix, file_name)

    def delete_file(self, user_id, prefix, file_name):
        waiter = UserSpaceWaiter(user_id)
        waiter.delete_file(prefix, file_name)

    def delete_folder(self, user_id, prefix, folder_name):
        waiter = UserSpaceWaiter(user_id)
        waiter.delete_folder(prefix, folder_name)

    def get_file_information(self, user_id, prefix, file_name):
        waiter = UserSpaceWaiter(user_id)
        return waiter.get_file_information(prefix, file_name)

user_space_service = UserSpaceService()
