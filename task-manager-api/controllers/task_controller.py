import logging
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from models.database import db
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.error_handler import NotFoundError, ForbiddenError

logger = logging.getLogger(__name__)


def _ensure_owner_or_admin(current_user, task):
    if current_user["role"] != "admin" and task.user_id != current_user["id"]:
        raise ForbiddenError("Acesso a tarefa de outro usuário")


def get_all_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for task in tasks:
        data = task.to_dict()
        data["user_name"] = task.user.name if task.user else None
        data["category_name"] = task.category.name if task.category else None
        result.append(data)
    return result


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    return task.to_dict()


def create_task(current_user, payload):
    if payload.get("category_id") and not Category.query.get(payload["category_id"]):
        raise NotFoundError("Categoria não encontrada")

    task = Task(
        title=payload["title"],
        description=payload.get("description", ""),
        status=payload.get("status", "pending"),
        priority=payload.get("priority", 3),
        user_id=current_user["id"],
        category_id=payload.get("category_id"),
        due_date=payload.get("due_date"),
        tags=",".join(payload["tags"]) if payload.get("tags") else None,
    )
    try:
        db.session.add(task)
        db.session.commit()
        logger.info("Task criada: %d - %s", task.id, task.title)
        return task.to_dict()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def update_task(current_user, task_id, payload):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    _ensure_owner_or_admin(current_user, task)

    if "title" in payload:
        task.title = payload["title"]
    if "description" in payload:
        task.description = payload["description"]
    if "status" in payload:
        task.status = payload["status"]
    if "priority" in payload:
        task.priority = payload["priority"]
    if "category_id" in payload:
        if payload["category_id"] and not Category.query.get(payload["category_id"]):
            raise NotFoundError("Categoria não encontrada")
        task.category_id = payload["category_id"]
    if "due_date" in payload:
        task.due_date = payload["due_date"]
    if "tags" in payload:
        task.tags = ",".join(payload["tags"]) if payload["tags"] else None

    try:
        db.session.commit()
        logger.info("Task atualizada: %d", task_id)
        return task.to_dict()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def delete_task(current_user, task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    _ensure_owner_or_admin(current_user, task)
    try:
        db.session.delete(task)
        db.session.commit()
        logger.info("Task deletada: %d", task_id)
    except SQLAlchemyError:
        db.session.rollback()
        raise


def search_tasks(query_str, status, priority, user_id):
    query = Task.query
    if query_str:
        query = query.filter(
            db.or_(
                Task.title.ilike(f"%{query_str}%"),
                Task.description.ilike(f"%{query_str}%"),
            )
        )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == int(priority))
    if user_id:
        query = query.filter(Task.user_id == int(user_id))
    return [t.to_dict() for t in query.all()]


def get_stats():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    total = Task.query.count()
    done = Task.query.filter_by(status="done").count()
    overdue_count = Task.query.filter(
        Task.due_date < now,
        Task.status.notin_(["done", "cancelled"]),
    ).count()
    return {
        "total": total,
        "pending": Task.query.filter_by(status="pending").count(),
        "in_progress": Task.query.filter_by(status="in_progress").count(),
        "done": done,
        "cancelled": Task.query.filter_by(status="cancelled").count(),
        "overdue": overdue_count,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }
