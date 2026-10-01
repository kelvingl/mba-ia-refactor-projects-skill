import re
from marshmallow import Schema, fields, validate, validates, ValidationError

EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
VALID_ROLES = ("user", "admin", "manager")


def _validate_email(value):
    if not EMAIL_RE.match(value):
        raise ValidationError("Email inválido")


class CreateUserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Str(required=True, validate=_validate_email)
    password = fields.Str(required=True, validate=validate.Length(min=4))
    role = fields.Str(load_default="user", validate=validate.OneOf(VALID_ROLES))


class UpdateUserSchema(Schema):
    """Schema para usuário comum (sem campos de privilégio)."""
    name = fields.Str()
    email = fields.Str(validate=_validate_email)
    password = fields.Str(validate=validate.Length(min=4))


class AdminUpdateUserSchema(Schema):
    """Schema para admin (inclui campos de privilégio)."""
    name = fields.Str()
    email = fields.Str(validate=_validate_email)
    password = fields.Str(validate=validate.Length(min=4))
    role = fields.Str(validate=validate.OneOf(VALID_ROLES))
    active = fields.Bool()
