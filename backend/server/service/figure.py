from model.figure import Figure
from dao.figure import figure_dao
from datetime import datetime
import uuid
from sss.porter_factory import PorterFactory

class FigureService:
    def create_figure(self, computation_id, figure_name, suffix, node_id):
        now = datetime.now()
        figure_uuid = str(uuid.uuid4()) + "." + suffix
        figure = Figure(
            computation_id=computation_id,
            figure_name=figure_name,
            figure_uuid=figure_uuid,
            created_time=now,
            node_id=node_id
        )
        figure = figure_dao.insert(figure)
        thumbnail_key = f"figure/thumbnail-{figure_uuid}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(thumbnail_key)
        thumbnail_presigned_url = porter.get_presigned_post(10, 60 * 10)
        key = f"figure/{figure_uuid}"
        porter.set_operation_target(key)
        presigned_url = porter.get_presigned_post(10, 60 * 10)
        upload_info = {
            "id": figure.id,
            "computationId": computation_id,
            "figureName": figure_name,
            "figureUuid": figure_uuid,
            "createdTime": int(now.timestamp() * 1000),
            "nodeId": node_id,
            "key": key,
            "presignedUrl": presigned_url,
            "thumbnailKey": thumbnail_key,
            "thumbnailPresignedUrl": thumbnail_presigned_url
        }
        return upload_info
    
    def list_figures_by_computation_id(self, computation_id):
        figures = figure_dao.find_by_computation_id(computation_id)
        porter = PorterFactory.create_porter()
        result = [figure.to_dict() for figure in figures]
        for item in result:
            figureUuid = item["figureUuid"]
            porter.set_operation_target(f"figure/{figureUuid}")
            porter.set_operation_target(f"figure/thumbnail-{figureUuid}")
            item["thumbnailUrl"] = porter.get_presigned_url(300)
        return result
    
    def list_figures_by_node_id(self, node_id):
        figures = figure_dao.find_by_node_id(node_id)
        porter = PorterFactory.create_porter()
        result = [figure.to_dict() for figure in figures]
        for item in result:
            figureUuid = item["figureUuid"]
            porter.set_operation_target(f"figure/{figureUuid}")
            item["url"] = porter.get_presigned_url(300)
        return result
    
figure_service = FigureService()