"""
Test data factories
Used to generate various test data objects
"""
from datetime import datetime
from typing import Dict, Any


class UserFactory:
    """User data factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create user test data"""
        defaults = {
            'id': 1,
            'user_name': f'testuser_{datetime.now().timestamp()}',
            'email': f'test_{datetime.now().timestamp()}@example.com',
            'phone_number': '+1234567890',
            'password': 'testpass123',
            'password_hash': 'hashed_password',
            'created_time': datetime.now(),
            'disabled': False,
            'extend1': None
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_batch(count: int = 3, **kwargs) -> list:
        """Create users in batch"""
        return [UserFactory.create(id=i, **kwargs) for i in range(1, count + 1)]


class AnalysisFactory:
    """Analysis data factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create analysis test data"""
        defaults = {
            'id': 1,
            'name': f'Test Analysis {datetime.now().timestamp()}',
            'description': 'Test analysis description',
            'user_id': 1,
            'status': 'pending',
            'created_time': datetime.now(),
            'updated_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_batch(count: int = 3, **kwargs) -> list:
        """Create analyses in batch"""
        return [AnalysisFactory.create(id=i, **kwargs) for i in range(1, count + 1)]


class DataFactory:
    """Data file factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create data file test data"""
        defaults = {
            'id': 1,
            'name': f'test_data_{datetime.now().timestamp()}.csv',
            'file_path': '/test/path/test_data.csv',
            'file_size': 1024,
            'user_id': 1,
            'analysis_id': 1,
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class PipelineTemplateFactory:
    """Pipeline template factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create pipeline template test data"""
        defaults = {
            'id': 1,
            'name': f'Test Template {datetime.now().timestamp()}',
            'description': 'Test template description',
            'user_id': 1,
            'public': False,
            'created_time': datetime.now(),
            'updated_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class ComputationFactory:
    """Compute task factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create compute task test data"""
        defaults = {
            'id': 1,
            'analysis_id': 1,
            'user_id': 1,
            'status': 'pending',
            'progress': 0,
            'created_time': datetime.now(),
            'started_time': None,
            'finished_time': None
        }
        defaults.update(kwargs)
        return defaults


class NodeFactory:
    """Node factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create node test data"""
        defaults = {
            'id': 1,
            'analysis_id': 1,
            'name': f'Test Node {datetime.now().timestamp()}',
            'node_type': 'processing',
            'parameters': '{}',
            'position_x': 100,
            'position_y': 100,
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class EdgeFactory:
    """Edge factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create edge test data"""
        defaults = {
            'id': 1,
            'analysis_id': 1,
            'source_node_id': 1,
            'target_node_id': 2,
            'source_port': 'output',
            'target_port': 'input',
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class FigureFactory:
    """Figure factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create figure test data"""
        defaults = {
            'id': 1,
            'analysis_id': 1,
            'name': f'Test Figure {datetime.now().timestamp()}',
            'figure_type': 'plot',
            'file_path': '/test/path/figure.png',
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class ReportFactory:
    """Report factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create report test data"""
        defaults = {
            'id': 1,
            'analysis_id': 1,
            'name': f'Test Report {datetime.now().timestamp()}',
            'content': 'Test report content',
            'report_type': 'html',
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class ChatFactory:
    """Chat factory"""

    @staticmethod
    def create_session(**kwargs) -> Dict[str, Any]:
        """Create chat session test data"""
        defaults = {
            'id': 1,
            'user_id': 1,
            'analysis_id': 1,
            'title': f'Test Chat {datetime.now().timestamp()}',
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_message(**kwargs) -> Dict[str, Any]:
        """Create chat message test data"""
        defaults = {
            'id': 1,
            'session_id': 1,
            'user_id': 1,
            'role': 'user',
            'content': 'Test message',
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class APIKeyFactory:
    """API key factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create API key test data"""
        defaults = {
            'id': 1,
            'user_id': 1,
            'key': f'test_api_key_{datetime.now().timestamp()}',
            'name': 'Test API Key',
            'active': True,
            'created_time': datetime.now(),
            'expires_at': None
        }
        defaults.update(kwargs)
        return defaults


class ParamFileFactory:
    """Parameter file factory"""

    @staticmethod
    def create(**kwargs) -> Dict[str, Any]:
        """Create parameter file test data"""
        defaults = {
            'id': 1,
            'name': f'test_params_{datetime.now().timestamp()}.yaml',
            'content': 'param1: value1\nparam2: value2',
            'user_id': 1,
            'created_time': datetime.now()
        }
        defaults.update(kwargs)
        return defaults


# Export all factory classes
__all__ = [
    'UserFactory',
    'AnalysisFactory',
    'DataFactory',
    'PipelineTemplateFactory',
    'ComputationFactory',
    'NodeFactory',
    'EdgeFactory',
    'FigureFactory',
    'ReportFactory',
    'ChatFactory',
    'APIKeyFactory',
    'ParamFileFactory'
]
