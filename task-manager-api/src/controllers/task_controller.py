import logging
from datetime import datetime, timezone
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from src.models.database import db
from src.models.task import Task
from src.models.user import User
from src.models.category import Category
from src.middlewares.error_handler import NotFoundError

logger = logging.getLogger(__name__)


def _serialize_task(task, include_relations=False):
    data = {**task.to_dict(), 'overdue': task.is_overdue()}
    if include_relations:
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
    return data


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    from src.middlewares.error_handler import ValidationError
    raise ValidationError("Formato de data inválido. Use YYYY-MM-DD")


def get_all_tasks(page=None, per_page=None):
    query = Task.query.options(joinedload(Task.user), joinedload(Task.category))
    if page and per_page:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return [_serialize_task(t, include_relations=True) for t in pagination.items]
    return [_serialize_task(t, include_relations=True) for t in query.all()]


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    return _serialize_task(task)


def create_task(payload):
    if payload.get('user_id'):
        if not User.query.get(payload['user_id']):
            raise NotFoundError("Usuário não encontrado")
    if payload.get('category_id'):
        if not Category.query.get(payload['category_id']):
            raise NotFoundError("Categoria não encontrada")
    task = Task()
    task.title = payload['title']
    task.description = payload.get('description', '')
    task.status = payload.get('status', 'pending')
    task.priority = payload.get('priority', 3)
    task.user_id = payload.get('user_id')
    task.category_id = payload.get('category_id')
    if payload.get('due_date'):
        task.due_date = _parse_date(payload['due_date']) if isinstance(payload['due_date'], str) else payload['due_date']
    tags = payload.get('tags', [])
    task.tags = ','.join(tags) if isinstance(tags, list) else tags
    db.session.add(task)
    db.session.commit()
    logger.info("Task created: %d %s", task.id, task.title)
    return task.to_dict()


def update_task(task_id, payload):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    if payload.get('user_id'):
        if not User.query.get(payload['user_id']):
            raise NotFoundError("Usuário não encontrado")
    if payload.get('category_id'):
        if not Category.query.get(payload['category_id']):
            raise NotFoundError("Categoria não encontrada")
    for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id'):
        if field in payload:
            setattr(task, field, payload[field])
    if 'due_date' in payload:
        val = payload['due_date']
        task.due_date = (_parse_date(val) if isinstance(val, str) else val) if val else None
    if 'tags' in payload:
        tags = payload['tags']
        task.tags = ','.join(tags) if isinstance(tags, list) else tags
    task.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
    logger.info("Task updated: %d", task.id)
    return task.to_dict()


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    db.session.delete(task)
    db.session.commit()
    logger.info("Task deleted: %d", task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(q='', status='', priority='', user_id=''):
    query = Task.query
    if q:
        query = query.filter(
            or_(Task.title.ilike(f'%{q}%'), Task.description.ilike(f'%{q}%'))
        )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == int(priority))
    if user_id:
        query = query.filter(Task.user_id == int(user_id))
    return [t.to_dict() for t in query.all()]


def get_stats():
    total = Task.query.count()
    done = Task.query.filter_by(status='done').count()
    overdue = sum(1 for t in Task.query.all() if t.is_overdue())
    return {
        'total': total,
        'pending': Task.query.filter_by(status='pending').count(),
        'in_progress': Task.query.filter_by(status='in_progress').count(),
        'done': done,
        'cancelled': Task.query.filter_by(status='cancelled').count(),
        'overdue': overdue,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
