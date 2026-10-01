from marshmallow import Schema, fields, validate

VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')


class CreateTaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(load_default='')
    status = fields.Str(load_default='pending', validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    user_id = fields.Int(load_default=None, allow_none=True)
    category_id = fields.Int(load_default=None, allow_none=True)
    due_date = fields.Str(load_default=None, allow_none=True)
    tags = fields.List(fields.Str(), load_default=[])


class UpdateTaskSchema(Schema):
    title = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str()
    status = fields.Str(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Int(validate=validate.Range(min=1, max=5))
    user_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
    due_date = fields.Str(allow_none=True)
    tags = fields.List(fields.Str())
