import logging
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from models.database import db
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.error_handler import NotFoundError, BadRequestError

logger = logging.getLogger('app')


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise BadRequestError('Formato de data inválido. Use YYYY-MM-DD')


def _enrich(task):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def get_all_tasks():
    tasks = Task.query.options(
        joinedload(Task.user),
        joinedload(Task.category)
    ).all()
    return [_enrich(t) for t in tasks]


def get_task_by_id(task_id):
    task = Task.query.options(
        joinedload(Task.user),
        joinedload(Task.category)
    ).filter_by(id=task_id).first()
    if not task:
        raise NotFoundError('Task não encontrada')
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def create_task(payload):
    if payload.get('user_id') and not User.query.get(payload['user_id']):
        raise NotFoundError('Usuário não encontrado')
    if payload.get('category_id') and not Category.query.get(payload['category_id']):
        raise NotFoundError('Categoria não encontrada')

    tags = payload.get('tags', [])
    task = Task(
        title=payload['title'],
        description=payload.get('description', ''),
        status=payload.get('status', 'pending'),
        priority=payload.get('priority', 3),
        user_id=payload.get('user_id'),
        category_id=payload.get('category_id'),
        due_date=_parse_date(payload.get('due_date')),
        tags=','.join(tags) if tags else None,
    )
    db.session.add(task)
    db.session.commit()
    logger.info('Task created: %d - %s', task.id, task.title)
    return task.to_dict()


def update_task(task_id, payload):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')

    if payload.get('user_id') and not User.query.get(payload['user_id']):
        raise NotFoundError('Usuário não encontrado')
    if payload.get('category_id') and not Category.query.get(payload['category_id']):
        raise NotFoundError('Categoria não encontrada')

    for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id'):
        if field in payload:
            setattr(task, field, payload[field])

    if 'due_date' in payload:
        task.due_date = _parse_date(payload['due_date'])

    if 'tags' in payload:
        tags = payload['tags']
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    task.updated_at = _now_utc()
    db.session.commit()
    logger.info('Task updated: %d', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    db.session.delete(task)
    db.session.commit()
    logger.info('Task deleted: %d', task_id)


def search_tasks(query_str='', status='', priority='', user_id=''):
    q = Task.query
    if query_str:
        q = q.filter(db.or_(
            Task.title.like(f'%{query_str}%'),
            Task.description.like(f'%{query_str}%'),
        ))
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == int(priority))
    if user_id:
        q = q.filter(Task.user_id == int(user_id))
    return [t.to_dict() for t in q.all()]


def get_task_stats():
    total = Task.query.count()
    done = Task.query.filter_by(status='done').count()
    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())
    return {
        'total': total,
        'pending': Task.query.filter_by(status='pending').count(),
        'in_progress': Task.query.filter_by(status='in_progress').count(),
        'done': done,
        'cancelled': Task.query.filter_by(status='cancelled').count(),
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
