from flask import Blueprint, request, jsonify
import controllers.report_controller as report_ctrl
from middlewares.error_handler import BadRequestError

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_ctrl.get_summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    return jsonify(report_ctrl.get_user_report(user_id)), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(report_ctrl.get_all_categories()), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json(silent=True) or {}
    if not data.get('name'):
        raise BadRequestError('Nome é obrigatório')
    return jsonify(report_ctrl.create_category(data)), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json(silent=True) or {}
    return jsonify(report_ctrl.update_category(cat_id, data)), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    report_ctrl.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
