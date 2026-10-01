from marshmallow import Schema, fields, validate


class CreateCategorySchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(load_default="")
    color = fields.Str(
        load_default="#000000",
        validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$", error="Cor deve estar no formato #RRGGBB"),
    )


class UpdateCategorySchema(Schema):
    name = fields.Str()
    description = fields.Str()
    color = fields.Str(
        validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$", error="Cor deve estar no formato #RRGGBB"),
    )
