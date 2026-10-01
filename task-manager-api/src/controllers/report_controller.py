from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
from src.models.database import db
from src.models.task import Task
from src.models.user import User
from src.models.category import Category
from src.middlewares.error_handler import NotFoundError
from src.controllers.authorization import ensure_self_or_admin


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def summary_report():
    seven_days_ago = _now_utc() - timedelta(days=7)
    total_tasks = Task.query.count()
    done = Task.query.filter_by(status='done').count()

    overdue_tasks = [t for t in Task.query.all() if t.is_overdue()]
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (_now_utc() - t.due_date).days,
        }
        for t in overdue_tasks
    ]

    # Single query with eager loading — avoids N+1
    users = User.query.options(joinedload(User.tasks)).all()
    user_stats = []
    for u in users:
        total = len(u.tasks)
        completed = sum(1 for t in u.tasks if t.status == 'done')
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round(completed / total * 100, 2) if total else 0,
        })

    return {
        'generated_at': str(_now_utc()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
        },
        'tasks_by_status': {
            'pending': Task.query.filter_by(status='pending').count(),
            'in_progress': Task.query.filter_by(status='in_progress').count(),
            'done': done,
            'cancelled': Task.query.filter_by(status='cancelled').count(),
        },
        'tasks_by_priority': {
            'critical': Task.query.filter_by(priority=1).count(),
            'high': Task.query.filter_by(priority=2).count(),
            'medium': Task.query.filter_by(priority=3).count(),
            'low': Task.query.filter_by(priority=4).count(),
            'minimal': Task.query.filter_by(priority=5).count(),
        },
        'overdue': {'count': len(overdue_tasks), 'tasks': overdue_list},
        'recent_activity': {
            'tasks_created_last_7_days': Task.query.filter(Task.created_at >= seven_days_ago).count(),
            'tasks_completed_last_7_days': Task.query.filter(
                Task.status == 'done', Task.updated_at >= seven_days_ago
            ).count(),
        },
        'user_productivity': user_stats,
    }


def user_report(current_user, user_id):
    ensure_self_or_admin(current_user, user_id)
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': sum(1 for t in tasks if t.status == 'pending'),
            'in_progress': sum(1 for t in tasks if t.status == 'in_progress'),
            'cancelled': sum(1 for t in tasks if t.status == 'cancelled'),
            'overdue': sum(1 for t in tasks if t.is_overdue()),
            'high_priority': sum(1 for t in tasks if t.priority <= 2),
            'completion_rate': round(done / total * 100, 2) if total else 0,
        },
    }
