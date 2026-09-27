import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import subqueryload
from models.database import db
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.error_handler import NotFoundError

logger = logging.getLogger('app')


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    tasks_by_status = {
        'pending': Task.query.filter_by(status='pending').count(),
        'in_progress': Task.query.filter_by(status='in_progress').count(),
        'done': Task.query.filter_by(status='done').count(),
        'cancelled': Task.query.filter_by(status='cancelled').count(),
    }

    tasks_by_priority = {
        'critical': Task.query.filter_by(priority=1).count(),
        'high': Task.query.filter_by(priority=2).count(),
        'medium': Task.query.filter_by(priority=3).count(),
        'low': Task.query.filter_by(priority=4).count(),
        'minimal': Task.query.filter_by(priority=5).count(),
    }

    now = _now_utc()
    overdue_tasks = [t for t in Task.query.all() if t.is_overdue()]
    overdue_list = [
        {'id': t.id, 'title': t.title, 'due_date': str(t.due_date),
         'days_overdue': (now - t.due_date).days}
        for t in overdue_tasks
    ]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done', Task.updated_at >= seven_days_ago
    ).count()

    users = User.query.options(subqueryload(User.tasks)).all()
    user_stats = []
    for u in users:
        total = len(u.tasks)
        completed = sum(1 for t in u.tasks if t.status == 'done')
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': tasks_by_status,
        'tasks_by_priority': tasks_by_priority,
        'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def get_user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    pending = sum(1 for t in tasks if t.status == 'pending')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    cancelled = sum(1 for t in tasks if t.status == 'cancelled')
    overdue = sum(1 for t in tasks if t.is_overdue())
    high_priority = sum(1 for t in tasks if t.priority <= 2)

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        },
    }


def get_all_categories():
    categories = Category.query.all()
    result = []
    for c in categories:
        data = c.to_dict()
        data['task_count'] = Task.query.filter_by(category_id=c.id).count()
        result.append(data)
    return result


def create_category(payload):
    category = Category(
        name=payload['name'],
        description=payload.get('description', ''),
        color=payload.get('color', '#000000'),
    )
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(cat_id, payload):
    cat = Category.query.get(cat_id)
    if not cat:
        raise NotFoundError('Categoria não encontrada')
    for field in ('name', 'description', 'color'):
        if field in payload:
            setattr(cat, field, payload[field])
    db.session.commit()
    return cat.to_dict()


def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        raise NotFoundError('Categoria não encontrada')
    db.session.delete(cat)
    db.session.commit()
