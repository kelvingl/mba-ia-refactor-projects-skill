from flask import Blueprint, request, jsonify
import controllers.task_controller as task_ctrl
from schemas.task_schema import CreateTaskSchema, UpdateTaskSchema

task_bp = Blueprint('tasks', __name__)

_create_schema = CreateTaskSchema()
_update_schema = UpdateTaskSchema()


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_ctrl.get_all_tasks()), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    return jsonify(task_ctrl.search_tasks(
        query_str=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_ctrl.get_task_stats()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_ctrl.get_task_by_id(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    payload = _create_schema.load(request.get_json(silent=True) or {})
    return jsonify(task_ctrl.create_task(payload)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    payload = _update_schema.load(request.get_json(silent=True) or {})
    return jsonify(task_ctrl.update_task(task_id, payload)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task_ctrl.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200
