from flask import Blueprint, request, jsonify
from src.controllers import category_controller
from src.schemas.category_schema import CreateCategorySchema, UpdateCategorySchema
from src.middlewares.auth import require_role

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_controller.get_all_categories()), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    payload = CreateCategorySchema().load(request.get_json(silent=True) or {})
    return jsonify(category_controller.create_category(payload)), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    payload = UpdateCategorySchema().load(request.get_json(silent=True) or {})
    return jsonify(category_controller.update_category(cat_id, payload)), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_role('admin')
def delete_category(cat_id):
    return jsonify(category_controller.delete_category(cat_id)), 200
