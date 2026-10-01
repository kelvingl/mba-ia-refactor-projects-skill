from flask import Blueprint, jsonify, request, g
from marshmallow import ValidationError as MarshmallowValidationError
from middlewares.error_handler import ValidationError
import controllers.category_controller as category_controller
import controllers.report_controller as report_controller
from schemas.category_schema import CreateCategorySchema, UpdateCategorySchema

report_bp = Blueprint("reports", __name__)

_create_cat_schema = CreateCategorySchema()
_update_cat_schema = UpdateCategorySchema()


@report_bp.route("/reports/summary", methods=["GET"])
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id):
    return jsonify(report_controller.user_report(g.current_user, user_id)), 200


@report_bp.route("/categories", methods=["GET"])
def get_categories():
    return jsonify(category_controller.get_all_categories()), 200


@report_bp.route("/categories", methods=["POST"])
def create_category():
    try:
        payload = _create_cat_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as e:
        raise ValidationError(str(e.messages))
    return jsonify(category_controller.create_category(payload)), 201


@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    try:
        payload = _update_cat_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as e:
        raise ValidationError(str(e.messages))
    return jsonify(category_controller.update_category(cat_id, payload)), 200


@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    category_controller.delete_category(cat_id)
    return jsonify({"message": "Categoria deletada"}), 200
