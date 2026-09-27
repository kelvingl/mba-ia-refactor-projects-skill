from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_now_utc)

    tasks = db.relationship('Task', back_populates='user', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, plain: str) -> None:
        self.password = generate_password_hash(plain)

    def check_password(self, plain: str) -> bool:
        return check_password_hash(self.password, plain)

    def is_admin(self) -> bool:
        return self.role == 'admin'
