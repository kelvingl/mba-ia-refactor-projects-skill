from datetime import datetime, date, time
from marshmallow import Schema, fields, validate, post_load, EXCLUDE

VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")


class CreateTaskSchema(Schema):
    class Meta:
        unknown = EXCLUDE  # user_id e outros campos não declarados são silenciosamente ignorados

    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(load_default="")
    status = fields.Str(load_default="pending", validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    category_id = fields.Int(load_default=None, allow_none=True)
    due_date = fields.Date(load_default=None, allow_none=True)
    tags = fields.List(fields.Str(), load_default=[])

    @post_load
    def coerce_date(self, data, **kwargs):
        if data.get("due_date") and isinstance(data["due_date"], date):
            data["due_date"] = datetime.combine(data["due_date"], time.min)
        return data


class UpdateTaskSchema(Schema):
    title = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str()
    status = fields.Str(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Int(validate=validate.Range(min=1, max=5))
    category_id = fields.Int(allow_none=True)
    due_date = fields.Date(allow_none=True)
    tags = fields.List(fields.Str())

    @post_load
    def coerce_date(self, data, **kwargs):
        if data.get("due_date") and isinstance(data["due_date"], date):
            data["due_date"] = datetime.combine(data["due_date"], time.min)
        return data
