from log.logger_factory import logger_factory
logger = logger_factory.create_logger("function_block_tool")

class FunctionBlockTool:

    @staticmethod
    def abstract_args_attr_dict_by_name(arguments: list, attr_name: str):
        attr_dict = {}
        for arg in arguments:
            attr_dict[arg["name"]] = arg[attr_name] if attr_name in arg else None
        return attr_dict

    @staticmethod
    def complete_arg(arg: dict):
        for key in ("name", "render_type"):
            if arg.get(key, None) is None:
                raise Exception(f"{key} is lacked")
        recombined_arg = {
            key: arg[key] for key in arg.keys()
        }
        recombined_arg["optional"] = recombined_arg.get("optional", True)
        recombined_arg["default_value"] = recombined_arg.get("default_value", None)
        recombined_arg["value_type"] = recombined_arg.get("value_type", None)
        recombined_arg["options"] = recombined_arg.get("options", None)
        recombined_arg["description"] = recombined_arg.get("description", "no description")
        return recombined_arg

    @staticmethod
    def complete_args(args: list):
        return [
            FunctionBlockTool.complete_arg(arg) for arg in args
        ]
    