from marshmallow import Schema, fields, validate


class CreateCategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default='')
    color = fields.Str(load_default='#000000')


class UpdateCategorySchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()
    color = fields.Str()
