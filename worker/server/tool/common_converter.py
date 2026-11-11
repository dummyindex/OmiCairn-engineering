from sqlalchemy.engine.row import Row


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def convert_model_to_dict(model, camel_case=False):
    if isinstance(model, dict):
        return model

    if hasattr(model, '__table__'):
        columns = [column.name for column in model.__table__.columns]
    elif isinstance(model, Row):
        columns = model._fields
    else:
        raise ValueError(
            "Input is neither a SQLAlchemy model nor a dictionary")
    if camel_case:
        return {
            to_camel_case(column): getattr(model, column)
            for column in columns
        }
    return {
        column: getattr(model, column)
        for column in columns
    }
