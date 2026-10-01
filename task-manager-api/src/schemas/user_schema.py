from marshmallow import Schema, fields, validate

VALID_ROLES = ('user', 'admin', 'manager')


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


class CreateUserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=4))
    role = fields.Str(load_default='user', validate=validate.OneOf(VALID_ROLES))


class UpdateUserSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    password = fields.Str(validate=validate.Length(min=4))
    role = fields.Str(validate=validate.OneOf(VALID_ROLES))
    active = fields.Bool()
