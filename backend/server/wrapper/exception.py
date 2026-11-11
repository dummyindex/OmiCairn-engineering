import traceback
from functools import wraps

from exception.authority.token_invalid import TokenInvalidException
from exception.authority.login_error import LoginErrorException
from exception.authority.register_error import RegisterErrorException
from exception.authority.no_authority import NoAuthorityException

from exception.request.parameter_invalid import ParameterInvalidException

from exception.data_component.convert_to_component import ConvertToComponentException
from exception.data_component.confirm import DataComponentConfirmException
from exception.data_component.assemble import DataComponentAssembleException

from exception.data.confirm import DataConfirmException
from exception.data.data_fetch import DataFetchException

from exception.sss.upload_file import SSSUploadFileException
from exception.sss.fetch_file import SSSFetchFileException
from exception.sss.remove_file import SSSRemoveFileException
from exception.sss.copy_file import SSSCopyFileException

from exception.flow.not_removable import NotRemovableException

from exception.computation.enqueue import ComputationEnqueueException
from exception.computation.state import ComputationStateException
from exception.data.collect import DataCollectException
from exception.request.dynamic_status_code import DynamicStatusCode

from tool.response_manager import ResponseManager


def exception_wrapper(func):
    @wraps(func)
    def wrapped_function(self):
        try:
            return func(self)
        except (
            TokenInvalidException,
            NoAuthorityException
        ) as e:
            return ResponseManager.new_unauthorized_response(str(e))
        except (
            ParameterInvalidException,
            LoginErrorException,
            RegisterErrorException,
            ConvertToComponentException,
            DataConfirmException,
            DataComponentConfirmException,
            DataFetchException,
            DataComponentAssembleException,
            DataCollectException
        ) as e:
            return ResponseManager.new_bad_request_response(str(e))
        except (
            NotImplementedError,
            SSSFetchFileException,
            SSSUploadFileException,
            SSSRemoveFileException,
            SSSCopyFileException,
            NotRemovableException,
            ComputationEnqueueException,
            ComputationStateException
        ) as e:
            return ResponseManager.new_server_error_response(str(e))
        except DynamicStatusCode as e:
            return ResponseManager.new_dynamic_status_code_response(e.get_code(), str(e))
        except Exception as e:
            traceback.print_exc()
            return ResponseManager.new_server_error_response(str(e))
    return wrapped_function
