import re
from marshmallow import Schema, fields, validate, validates, ValidationError

VALID_ROLES = ('user', 'admin', 'manager')
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


class CreateUserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=4))
    role = fields.Str(load_default='user', validate=validate.OneOf(VALID_ROLES))

    @validates('email')
    def validate_email(self, value):
        if not _EMAIL_RE.match(value):
            raise ValidationError('Email inválido')


class UpdateUserSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1))
    email = fields.Str()
    password = fields.Str(validate=validate.Length(min=4))
    role = fields.Str(validate=validate.OneOf(VALID_ROLES))
    active = fields.Bool()

    @validates('email')
    def validate_email(self, value):
        if not _EMAIL_RE.match(value):
            raise ValidationError('Email inválido')
