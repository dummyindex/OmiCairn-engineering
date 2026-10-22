from log.logger_factory import logger_factory
from sss.porter_factory import PorterFactory
import json
import os
from PIL import Image

logger = logger_factory.create_logger("attached_data_service")

def get_image_extension(file_path):
    """
    Given an image file path, return the correct image extension (e.g. 'jpg', 'png', without the dot).
    """
    with Image.open(file_path) as img:
        fmt = img.format.lower()
        # Pillow usually reports JPEG as 'jpeg'; convert it to 'jpg' as needed
        if fmt == 'jpeg':
            return 'jpg'
        return fmt
    
def fix_image_extension(file_path):
    """
    Given an image file path, return the corrected file path.
    """
    # if the file already has an extension, leave it unchanged
    if '.' in os.path.basename(file_path):
        return file_path
    ext = get_image_extension(file_path)
    if ext == 'jpg':
        ext = 'jpeg'
    new_file_path = file_path + '.' + ext
    if new_file_path != file_path:
        os.rename(file_path, new_file_path)
        logger.info(f"Renamed {file_path} to {new_file_path}")
    return new_file_path

def generate_thumbnail(image_path: str, thumbnail_path: str, max_side_length=128):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            if width >= height:
                new_width = max_side_length
                new_height = int(height * max_side_length / width)
            else:
                new_height = max_side_length
                new_width = int(width * max_side_length / height)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            img.save(thumbnail_path)
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        raise

class AttachedDataService:

    def check_thumbnail(self, figure_uuid: str):
        porter = PorterFactory.create_porter()
        object_key = f"figure/thumbnail-{figure_uuid}"
        porter.set_operation_target(object_key)
        return porter.check_file()
    
    def fix_thumbnail(self, figure_uuid: str):
        porter = PorterFactory.create_porter()
        object_key = f"figure/{figure_uuid}"
        porter.set_operation_target(object_key)
        workshop_path = os.path.join("/tmp", "figure-workshop")
        if not os.path.exists(workshop_path):
            os.makedirs(workshop_path)
        raw_path = os.path.join(workshop_path, figure_uuid)
        porter.fetch_file(raw_path)
        new_raw_path = fix_image_extension(raw_path)
        new_raw_name = os.path.basename(new_raw_path)
        thumbnail_path = os.path.join(workshop_path, f"thumbnail-{new_raw_name}")
        generate_thumbnail(new_raw_path, thumbnail_path)
        porter.set_operation_target(f"figure/thumbnail-{figure_uuid}")
        porter.save_file(thumbnail_path)
        os.remove(thumbnail_path)
        os.remove(new_raw_path)

    def get_figure_download_info(self, figure_uuid: str, thumbnail: bool = False):
        porter = PorterFactory.create_porter()
        if thumbnail:
            if not self.check_thumbnail(figure_uuid):
                self.fix_thumbnail(figure_uuid)
            porter.set_operation_target(f"figure/thumbnail-{figure_uuid}")
        else:
            porter.set_operation_target(f"figure/{figure_uuid}")
        return porter.get_presigned_url(60 * 60)
    
    def get_tag_list(self, space_type, space_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{space_type}/{space_id}/tag-list")
        try:
            logger.info(f"Fetching tag list for {space_type}/{space_id}")
            tag_list_file_bytes = porter.fetch_file_stream()
            logger.info(f"Fetched tag list bytes: {tag_list_file_bytes}")
            tag_list_str = tag_list_file_bytes.decode("utf-8")
            logger.info(f"Tag list string: {tag_list_str}")
            return json.loads(tag_list_str)
        except:
            return dict()

attached_data_service = AttachedDataService()