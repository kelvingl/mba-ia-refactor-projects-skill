from flask import Blueprint, request, jsonify
from src.controllers import task_controller
from src.schemas.task_schema import CreateTaskSchema, UpdateTaskSchema

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)
    return jsonify(task_controller.get_all_tasks(page=page, per_page=per_page)), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    return jsonify(task_controller.search_tasks(
        q=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.get_stats()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    payload = CreateTaskSchema().load(request.get_json(silent=True) or {})
    return jsonify(task_controller.create_task(payload)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    payload = UpdateTaskSchema().load(request.get_json(silent=True) or {})
    return jsonify(task_controller.update_task(task_id, payload)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return jsonify(task_controller.delete_task(task_id)), 200
