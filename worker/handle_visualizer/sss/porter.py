from abc import ABC, abstractmethod


class Porter(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_bucket_name(self):
        pass

    @abstractmethod
    def get_object_key(self):
        pass

    @abstractmethod
    def set_headers(self, headers):
        pass

    @abstractmethod
    def set_metadata(self, key, value):
        pass

    @abstractmethod
    def remove_metadata(self, key):
        pass

    @abstractmethod
    def set_operation_target(self, object_key):
        pass

    @abstractmethod
    def save_file(self, file_path):
        pass

    @abstractmethod
    def save_file_text(self, text):
        pass

    @abstractmethod
    def save_file_stream(self, file_stream):
        pass

    @abstractmethod
    def fetch_file(self, file_path):
        pass

    @abstractmethod
    def fetch_file_stream(self):
        pass

    @abstractmethod
    def check_file(self):
        pass

    @abstractmethod
    def remove_file(self):
        pass

    @abstractmethod
    def copy_file(self, source_object_key):
        pass

    @abstractmethod
    def list_files(self, start_after: str = '', max_keys: int = 1000, recursive=False):
        pass

    @abstractmethod
    def get_head(self, object_key = None):
        pass

    @abstractmethod
    def update_metadata(self, object_key = None, metadata = None):
        pass

    @abstractmethod
    def get_file_info(self):
        pass

    @abstractmethod
    def get_presigned_url(self, expiration):
        pass

    @abstractmethod
    def get_presigned_post(self, expiration, fields=None):
        pass

    @abstractmethod
    def get_multipart_upload_presigned_post(self, file_size, expiration):
        pass
