from dao.node import node_dao
from service.computation import computation_service
from service.attached_data import attached_data_service
from sss.porter_factory import PorterFactory
from llm.llm_interface import LlmInterface
from log.logger_factory import logger_factory
from db import alchemy_db
import uuid
import time

logger = logger_factory.create_logger("Branch Report Service")

def trim_node_histories(node_histories, max_total_tokens=100000):
    if not node_histories:
        return []
    
    def estimate_tokens(obj):
        if isinstance(obj, str):
            return len(obj.split()) * 1.3
        elif isinstance(obj, (int, float)):
            return 1
        elif isinstance(obj, bool):
            return 1
        elif obj is None:
            return 1
        elif isinstance(obj, list):
            return sum(estimate_tokens(item) for item in obj)
        elif isinstance(obj, dict):
            return sum(estimate_tokens(k) + estimate_tokens(v) for k, v in obj.items())
        else:
            return len(str(obj).split()) * 1.3
    
    def trim_history_item(history_item, max_tokens):
        if not history_item:
            return history_item
            
        trimmed = {}
        current_tokens = 0
        
        priority_fields = [
            ('node', lambda x: {
                'id': x.get('id'),
                'name': x.get('name'),
                'type': x.get('type'),
                'state': x.get('state'),
                'computationParams': x.get('computationParams', {}),
                'tag': x.get('tag')
            }),
            ('latestComputation', lambda x: {
                'id': x.get('id'),
                'computationState': x.get('computationState'),
                'duration': x.get('duration'),
                'errorDescription': x.get('errorDescription'),
                'computationParams': x.get('computationParams', {})
            } if x else None),
            ('computationCount', lambda x: x),
            ('data', lambda x: {
                'id': x.get('id'),
                'name': x.get('name'),
                'state': x.get('state'),
                'species': x.get('species'),
                'description': x.get('description')
            } if x else None),
            ('figureList', lambda x: x[:5] if isinstance(x, list) else x),
            ('dataset_stats', lambda x: x),
            ('computationLog', lambda x: None)
        ]
        
        for field_name, field_processor in priority_fields:
            if field_name in history_item:
                processed_field = field_processor(history_item[field_name])
                field_tokens = estimate_tokens(processed_field)
                
                if current_tokens + field_tokens <= max_tokens:
                    trimmed[field_name] = processed_field
                    current_tokens += field_tokens
                elif field_name in ['node', 'latestComputation']:
                    minimal_field = {'id': history_item[field_name].get('id')} if history_item[field_name] else None
                    minimal_tokens = estimate_tokens(minimal_field)
                    if current_tokens + minimal_tokens <= max_tokens:
                        trimmed[field_name] = minimal_field
                        current_tokens += minimal_tokens
                
                if current_tokens >= max_tokens * 0.95:
                    break
        
        return trimmed
    
    total_tokens = sum(estimate_tokens(history) for history in node_histories)
    
    if total_tokens <= max_total_tokens:
        return node_histories
    
    tokens_per_history = max_total_tokens // len(node_histories)
    min_tokens_per_history = 1000
    
    if tokens_per_history < min_tokens_per_history:
        num_histories_to_keep = max(1, max_total_tokens // min_tokens_per_history)
        node_histories = node_histories[-num_histories_to_keep:]
        tokens_per_history = max_total_tokens // len(node_histories)
    
    trimmed_histories = []
    for history_item in node_histories:
        trimmed_item = trim_history_item(history_item, tokens_per_history)
        if trimmed_item:
            trimmed_histories.append(trimmed_item)

    return trimmed_histories

def get_images_from_s3(figure_list):
    porter = PorterFactory.create_porter()
    figure_image_list = []
    for figure in figure_list:
        key = figure.get('key')
        figure_name = figure.get('name')
        
        try:
            porter.set_operation_target(key)
            image_data = porter.fetch_file_stream()
            figure_image_list.append((figure_name, image_data))
        except Exception as e:
            logger.error(f"Failed to fetch image {figure_name} from S3: {e}")
            continue
    
    return figure_image_list

class BranchReportService:
    
    def generate_branch_report(self, analysis_id, branch_nodes, report_node, user_id, model):
        node_histories = self._build_node_histories(branch_nodes)
        node_figures = self._get_node_figures(branch_nodes)
        report_uuid = uuid.uuid4().hex
        
        llm_interface = LlmInterface()
        response = llm_interface.generate_branch_report(
            analysis_id=analysis_id,
            branch_nodes=branch_nodes, 
            node_histories=node_histories,
            node_figures=node_figures,
            report_uuid=report_uuid,
            report_node=report_node,
            user_id=user_id,
            model=model
        )
        
        if response.status_code == 200:
            self._handle_report_completion(report_uuid, report_node, model)
        else:
            logger.warning(f"Report generation failed with status code: {response.status_code}")

        return response
    
    def generate_branch_report_automated(self, analysis_id, branch_nodes, report_node, user_id, model):
        node_histories = self._build_node_histories(branch_nodes)
        node_figures = self._get_node_figure_descriptions(branch_nodes)
        report_uuid = uuid.uuid4().hex
        
        llm_interface = LlmInterface()
        response = llm_interface.generate_branch_report_automated(
            analysis_id=analysis_id,
            branch_nodes=branch_nodes, 
            node_histories=node_histories,
            node_figures=node_figures,
            report_uuid=report_uuid,
            report_node=report_node,
            user_id=user_id,
            model=model
        )
        
        if response.status_code == 200:
            self._handle_report_completion(report_uuid, report_node, model)
        else:
            logger.warning(f"Automated report generation failed with status code: {response.status_code}")
            
        return response
    
    def select_figures_automated(self, analysis_id, branch_nodes, user_id, model):
        node_histories = self._build_node_histories(branch_nodes)
        node_figures = self._get_node_figure_descriptions(branch_nodes)
        
        llm_interface = LlmInterface()
        response = llm_interface.select_figures_automated(
            analysis_id=analysis_id,
            branch_nodes=branch_nodes, 
            node_histories=node_histories,
            node_figures=node_figures,
            user_id=user_id,
            model=model
        )
        
        return response
    
    def _build_node_histories(self, branch_nodes):
        node_histories = []
        try: 
            last_branch_node = branch_nodes[-1] if branch_nodes else None
            last_branch_node_id = last_branch_node.get("id") if last_branch_node else None
            node_histories = computation_service.get_former_computation_history(last_branch_node_id)

        except Exception as e:
            logger.error(f"Failed to get computation history: {e}")
        
        return trim_node_histories(node_histories)
    
    def _get_node_figures(self, branch_nodes):
        node_figures = []
        
        if not branch_nodes:
            return node_figures
        
        try: 
            for branch_node in branch_nodes:
                node_id = branch_node.get("id")
                node_name = branch_node.get("name")
                node_static_figures = branch_node.get("figures", [])

                if not node_id or not node_static_figures:
                    continue
                figure_urls = []
                for figure in node_static_figures:
                    chart_uuid = figure.get("figureUuid")

                    if chart_uuid:
                        figure_url = attached_data_service.get_figure_download_info(chart_uuid)
                        if figure_url:
                            figure_urls.append({
                                'chart_uuid': chart_uuid,
                                'chart_name': figure.get("figureName"),
                                'figure_url': figure_url
                            })

                node_figures.append({
                    "nodeId": int(node_id),
                    "nodeName": node_name,
                    "figures": figure_urls
                })
        except Exception as e:
            logger.error(f"Failed to get figures from computation history: {e}")
            
        return node_figures
    
    def _get_node_figure_descriptions(self, branch_nodes):
        node_figures = []
        
        if not branch_nodes:
            return node_figures
        
        porter = PorterFactory.create_porter()
        
        try:
            for branch_node in branch_nodes:
                node_id = branch_node.get("id")
                node_name = branch_node.get("name")
                node_static_figures = branch_node.get("figures", [])

                if not node_id or not node_static_figures:
                    continue
                    
                figure_data_list = []
                for figure in node_static_figures:
                    chart_uuid = figure.get("figureUuid")

                    if chart_uuid:
                        clean_uuid = chart_uuid.replace('.png', '') if chart_uuid.endswith('.png') else chart_uuid
                        figure_url = attached_data_service.get_figure_download_info(chart_uuid)

                        figure_description = None
                        try:
                            description_key = f"figure-descriptions/{clean_uuid}.txt"
                            porter.set_operation_target(description_key)
                            if porter.check_file():
                                description_content = porter.fetch_file_stream()

                                if description_content:
                                    figure_description = description_content.decode('utf-8') if isinstance(description_content, bytes) else str(description_content)
                            else:
                                logger.warning(f"[reporter automation] Description file not found for figure {chart_uuid}")
                        except Exception as e:
                            logger.info(f"[reporter automation] Failed to fetch description for figure {chart_uuid}: {e}")
                        
                        if figure_url:
                            figure_data_list.append({
                                'chart_uuid': chart_uuid,
                                'chart_name': figure.get("figureName"),
                                'figure_url': figure_url,
                                'figure_description': figure_description or f"No description available for {figure.get('figureName', 'this figure')}"
                            })
                node_figures.append({
                    "nodeId": int(node_id),
                    "nodeName": node_name,
                    "figures": figure_data_list
                })
        except Exception as e:
            logger.info(f"[reporter automation] Failed to get figure descriptions: {e}")
            
        return node_figures
    
    def _handle_report_completion(self, report_uuid, report_node, model):
        try:
            zip_s3_key = f'workflow-report/{report_uuid}/branch_report_{report_uuid}.zip'
            txt_s3_key = f'workflow-report/{report_uuid}/branch_report_{report_uuid}.txt'
            md_s3_key = f'workflow-report/{report_uuid}/branch_report_{report_uuid}.md'
            
            porter = PorterFactory.create_porter()
            file_found, _ = self._wait_for_report_file_multiple_formats(porter, zip_s3_key, txt_s3_key, md_s3_key)
            
            if file_found and report_node and report_node.get('id'):
                self._update_report_node_state(report_node.get('id'), report_uuid, model, state='finished')
            elif not file_found:
                logger.warning(f"Report file not found in S3 after maximum attempts")
                self._update_report_node_state(report_node.get('id'), report_uuid, model, state='failed')                
        except Exception as e:
            logger.error(f"Error checking report file or updating node state: {e}", exc_info=True)
    
    def _wait_for_report_file_multiple_formats(self, porter, zip_s3_key, txt_s3_key, md_s3_key, max_attempts=60, sleep_interval=20):
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            try:
                porter.set_operation_target(zip_s3_key)
                if porter.check_file():
                    logger.info(f"Report file found (ZIP) on attempt {attempt}")
                    return True, zip_s3_key
            except Exception:
                pass
            
            # Check TXT format (fallback)
            try:
                porter.set_operation_target(txt_s3_key)
                if porter.check_file():
                    logger.info(f"Report file found (TXT) on attempt {attempt}")
                    return True, txt_s3_key
            except Exception:
                pass
            
            # Check MD format (fallback)
            try:
                porter.set_operation_target(md_s3_key)
                if porter.check_file():
                    logger.info(f"Report file found (MD) on attempt {attempt}")
                    return True, md_s3_key
            except Exception:
                pass
            
            if attempt < max_attempts:
                time.sleep(sleep_interval)
                    
        logger.warning(f"Report file not found after {max_attempts} attempts")
        return False, None
    
    def _update_report_node_state(self, report_node_id, report_uuid, model, state):
        try:
            current_node = node_dao.find_by_id(report_node_id)
            if not current_node:
                logger.error(f"Node {report_node_id} not found")
                return
            
            from service.flow import flow_service
            
            flow_service.edit_node(report_node_id, {
                'state': state,
                'report_uuid': report_uuid,
                'report_model': model
            })
            
            alchemy_db.session.commit()
            
            # Verify the update
            updated_node = node_dao.find_by_id(report_node_id)
            if updated_node and updated_node.state == state:
                logger.info(f"Updated report node {report_node_id} to {state}")
            else:
                logger.error(f"Failed to update report node {report_node_id} state")
                
        except Exception as e:
            logger.error(f"Error updating report node state: {e}", exc_info=True)
            try:
                alchemy_db.session.rollback()
            except Exception:
                pass
    
    def get_branch_report_presigned_url(self, report_id):
        try:
            porter = PorterFactory.create_porter()
            
            zip_path = f'branch_report_{report_id}.zip'
            zip_s3_key = f'workflow-report/{report_id}/{zip_path}'
            
            porter.set_operation_target(zip_s3_key)
            if porter.check_file():
                presigned_url = porter.get_presigned_url(3600)
                logger.info(f"Generated presigned URL for ZIP report: {report_id}")
                return presigned_url
            
            # Fallback to MD format (legacy)
            md_path = f'branch_report_{report_id}.md'
            md_s3_key = f'workflow-report/{report_id}/{md_path}'
            
            porter.set_operation_target(md_s3_key)
            if porter.check_file():
                presigned_url = porter.get_presigned_url(3600)
                logger.info(f"Generated presigned URL for MD report: {report_id}")
                return presigned_url
            
            logger.warning(f"No report file found for report_id: {report_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

branch_report_service = BranchReportService()