import logging
from src.models.database import db
from src.models.category import Category
from src.models.task import Task
from src.middlewares.error_handler import NotFoundError

logger = logging.getLogger(__name__)


def get_all_categories():
    categories = Category.query.all()
    return [
        {**c.to_dict(), 'task_count': Task.query.filter_by(category_id=c.id).count()}
        for c in categories
    ]


def create_category(payload):
    category = Category()
    category.name = payload['name']
    category.description = payload.get('description', '')
    category.color = payload.get('color', '#000000')
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(cat_id, payload):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")
    for field in ('name', 'description', 'color'):
        if field in payload:
            setattr(category, field, payload[field])
    db.session.commit()
    return category.to_dict()


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")
    db.session.delete(category)
    db.session.commit()
    return {'message': 'Categoria deletada'}
