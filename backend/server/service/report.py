from dao.report import report_dao
from model.report import Report
from service.computation import computation_service

class ReportService:
    # currently only create_report is used
    def create_report(self, node_id, summary, detail):
        computation = computation_service.get_latest_by_node(node_id)
        if not computation:
            pass

        error_log = computation.error_description
        optimized_error = computation.optimized_error_description
        fb_id = computation.function_block_id
        current_max_report_id = report_dao.find_max_report_id_by_node_id(node_id)
        new_report_id = current_max_report_id + 1

        report = Report(
            node_id=node_id,
            report_id=new_report_id, 
            summary=summary,
            detail=detail,
            error_log=error_log,
            optimized_error=optimized_error,
            fb_id=fb_id
        )
        report_dao.insert(report)
        return report
     
    def get_report_info(self, node_id, report_id):
        return report_dao.find_by_node_and_report_id(node_id, report_id)
 
    def get_report_info_by_node_id(self, node_id):
        return report_dao.find_by_node_id(node_id)
    
    def update_report(node_id, report_id, summary, detail):
        report = ReportService.get_report_info(node_id, report_id)
        if not report:
            return None
        attrs_dict = {
            'summary': summary,
            'detail': detail
        }
        report_dao.update(node_id, report_id, attrs_dict)
        return report
    
    def delete_report(node_id, report_id):
        report_dao.delete_by_node_and_report_id(node_id, report_id)

    # Additional methods can be added as needed


report_service = ReportService()