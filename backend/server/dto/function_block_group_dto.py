from dto import Dto
from model.function_block_group import FunctionBlockGroup
from model.function_block_v1 import FunctionBlockV1
from typing import List


class FunctionBlockGroupDto(Dto):
    def __init__(
        self,
        function_block_group: FunctionBlockGroup,
        function_block_v1_list: List[FunctionBlockV1]
    ) -> None:
        super().__init__()
        self.function_block_group = function_block_group
        self.function_block_v1_list = function_block_v1_list

    def to_dict(self):
        function_block_group_dict = self.function_block_group.to_dict()
        function_block_group_dict['functionBlockList'] = [
            function_block_v1 for function_block_v1 in self.function_block_v1_list
        ]
        return function_block_group_dict
