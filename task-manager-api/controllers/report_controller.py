from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import joinedload
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.error_handler import NotFoundError, ForbiddenError


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def summary_report():
    now = _now_utc()
    seven_days_ago = now - timedelta(days=7)

    overdue_tasks = Task.query.filter(
        Task.due_date < now,
        Task.status.notin_(["done", "cancelled"]),
    ).all()
    overdue_list = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "days_overdue": (now - t.due_date).days,
        }
        for t in overdue_tasks
    ]

    total = Task.query.count()
    done = Task.query.filter_by(status="done").count()

    users = User.query.options(joinedload(User.tasks)).all()
    user_stats = []
    for user in users:
        u_total = len(user.tasks)
        u_done = sum(1 for t in user.tasks if t.status == "done")
        user_stats.append({
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": u_total,
            "completed_tasks": u_done,
            "completion_rate": round((u_done / u_total) * 100, 2) if u_total > 0 else 0,
        })

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": total,
            "total_users": User.query.count(),
            "total_categories": Category.query.count(),
        },
        "tasks_by_status": {
            "pending": Task.query.filter_by(status="pending").count(),
            "in_progress": Task.query.filter_by(status="in_progress").count(),
            "done": done,
            "cancelled": Task.query.filter_by(status="cancelled").count(),
        },
        "tasks_by_priority": {
            "critical": Task.query.filter_by(priority=1).count(),
            "high": Task.query.filter_by(priority=2).count(),
            "medium": Task.query.filter_by(priority=3).count(),
            "low": Task.query.filter_by(priority=4).count(),
            "minimal": Task.query.filter_by(priority=5).count(),
        },
        "overdue": {"count": len(overdue_list), "tasks": overdue_list},
        "recent_activity": {
            "tasks_created_last_7_days": Task.query.filter(Task.created_at >= seven_days_ago).count(),
            "tasks_completed_last_7_days": Task.query.filter(
                Task.status == "done", Task.updated_at >= seven_days_ago
            ).count(),
        },
        "user_productivity": user_stats,
    }


def user_report(current_user, user_id):
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise ForbiddenError("Acesso a relatório de outro usuário")
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    tasks = Task.query.filter_by(user_id=user_id).all()
    now = _now_utc()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": sum(1 for t in tasks if t.status == "pending"),
            "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
            "cancelled": sum(1 for t in tasks if t.status == "cancelled"),
            "overdue": sum(
                1 for t in tasks if t.due_date and t.due_date < now and t.status not in ("done", "cancelled")
            ),
            "high_priority": sum(1 for t in tasks if t.priority <= 2),
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        },
    }
