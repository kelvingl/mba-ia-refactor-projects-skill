from flask import Blueprint, jsonify, request, g
from marshmallow import ValidationError as MarshmallowValidationError
from middlewares.error_handler import ValidationError
import controllers.task_controller as task_controller
from schemas.task_schema import CreateTaskSchema, UpdateTaskSchema

task_bp = Blueprint("tasks", __name__)

_create_schema = CreateTaskSchema()
_update_schema = UpdateTaskSchema()


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    result = task_controller.search_tasks(
        query_str=request.args.get("q", ""),
        status=request.args.get("status", ""),
        priority=request.args.get("priority", ""),
        user_id=request.args.get("user_id", ""),
    )
    return jsonify(result), 200


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    return jsonify(task_controller.get_stats()), 200


@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify(task_controller.get_all_tasks()), 200


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    try:
        payload = _create_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as e:
        raise ValidationError(str(e.messages))
    return jsonify(task_controller.create_task(g.current_user, payload)), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    try:
        payload = _update_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as e:
        raise ValidationError(str(e.messages))
    return jsonify(task_controller.update_task(g.current_user, task_id, payload)), 200


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_controller.delete_task(g.current_user, task_id)
    return jsonify({"message": "Task deletada com sucesso"}), 200
