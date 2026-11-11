from datetime import datetime
import uuid
from sss.porter_factory import PorterFactory
from service.attached_data import attached_data_service
from llm.llm_interface import LlmInterface
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("FigureDescriptionService")


class FigureDescriptionService:
    def __init__(self):
        self.llm_interface = LlmInterface()
        self.porter = PorterFactory.create_porter()
    
    def generate_figure_description(self, figure_uuid, figure_name, node_name=None, user_id=None):
        """
        Generate a text description for a figure
        
        Args:
            figure_uuid: UUID of the figure
            figure_name: Name of the figure file
            node_name: Optional name of the node that created the figure
            user_id: User ID for tracking
        
        Returns:
            Response from GPT server
        """
        try:
            # Get figure URL
            figure_url = attached_data_service.get_figure_download_info(figure_uuid)
            if not figure_url:
                logger.error(f"Failed to get figure URL for {figure_uuid}")
                return None
            
            response = self.llm_interface.generate_figure_description(
                figure_url=figure_url,
                figure_uuid=figure_uuid,
                figure_name=figure_name,
                node_name=node_name,
                user_id=user_id
            )
            
            return response
        except Exception as e:
            logger.error(f"Error generating figure description: {e}")
            return None
    
    def batch_generate_descriptions(self, figures, user_id):
        """
        Generate descriptions for multiple figures
        
        Args:
            figures: List of figure dictionaries with uuid and name
            user_id: User ID for tracking
        
        Returns:
            Response from GPT server
        """
        try:
            # Add URLs to each figure
            processed_figures = []
            for fig in figures:
                figure_uuid = fig.get('figure_uuid')
                figure_url = attached_data_service.get_figure_download_info(figure_uuid)
                if figure_url:
                    processed_figures.append({
                        'figure_uuid': figure_uuid,
                        'figure_url': figure_url,
                        'figure_name': fig.get('figure_name', ''),
                        'node_name': fig.get('node_name', '')
                    })
                else:
                    logger.warning(f"Skipping figure {figure_uuid} - no URL found")
            
            if not processed_figures:
                return {
                    'status': 'error',
                    'message': 'No valid figures to process'
                }
            
            response = self.llm_interface.batch_generate_figure_descriptions(
                figures=processed_figures,
                user_id=user_id
            )
            
            return response
        except Exception as e:
            logger.error(f"Error in batch description generation: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_figure_description(self, figure_uuid):
        """
        Retrieve existing figure description from S3
        
        Args:
            figure_uuid: UUID of the figure
        
        Returns:
            Description text or None if not found
        """
        try:
            # Clean UUID if it has extension
            clean_uuid = figure_uuid.replace('.png', '') if figure_uuid.endswith('.png') else figure_uuid
            
            description_key = f"figure-descriptions/{clean_uuid}.txt"
            self.porter.set_operation_target(description_key)
            
            if self.porter.check_file():
                description_content = self.porter.fetch_file_stream()
                if description_content:
                    return description_content.decode('utf-8') if isinstance(description_content, bytes) else str(description_content)
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving figure description: {e}")
            return None
    
    def check_description_exists(self, figure_uuid):
        """
        Check if a description already exists for a figure
        
        Args:
            figure_uuid: UUID of the figure
        
        Returns:
            Boolean indicating if description exists
        """
        try:
            clean_uuid = figure_uuid.replace('.png', '') if figure_uuid.endswith('.png') else figure_uuid
            description_key = f"figure-descriptions/{clean_uuid}.txt"
            self.porter.set_operation_target(description_key)
            return self.porter.check_file()
        except Exception as e:
            logger.error(f"Error checking figure description: {e}")
            return False


figure_description_service = FigureDescriptionService()