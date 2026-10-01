import logging
from sqlalchemy.exc import SQLAlchemyError
from models.database import db
from models.category import Category
from models.task import Task
from middlewares.error_handler import NotFoundError

logger = logging.getLogger(__name__)


def get_all_categories():
    categories = Category.query.all()
    result = []
    for cat in categories:
        data = cat.to_dict()
        data["task_count"] = Task.query.filter_by(category_id=cat.id).count()
        result.append(data)
    return result


def create_category(payload):
    category = Category(
        name=payload["name"],
        description=payload.get("description", ""),
        color=payload.get("color", "#000000"),
    )
    try:
        db.session.add(category)
        db.session.commit()
        return category.to_dict()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def update_category(cat_id, payload):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")
    if "name" in payload:
        category.name = payload["name"]
    if "description" in payload:
        category.description = payload["description"]
    if "color" in payload:
        category.color = payload["color"]
    try:
        db.session.commit()
        return category.to_dict()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")
    Task.query.filter_by(category_id=cat_id).update({"category_id": None})
    try:
        db.session.delete(category)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
