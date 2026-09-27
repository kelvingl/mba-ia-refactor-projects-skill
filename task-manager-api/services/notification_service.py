import smtplib
import logging
from datetime import datetime, timezone
from config.settings import settings

logger = logging.getLogger('app')


class NotificationService:
    def send_email(self, to: str, subject: str, body: str) -> bool:
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to, f'Subject: {subject}\n\n{body}')
            server.quit()
            logger.info('Email sent to %s', to)
            return True
        except Exception:
            logger.exception('Failed to send email to %s', to)
            return False

    def notify_task_assigned(self, user, task) -> None:
        subject = f'Nova task atribuída: {task.title}'
        body = (
            f'Olá {user.name},\n\n'
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\nStatus: {task.status}'
        )
        self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task) -> None:
        subject = f'Task atrasada: {task.title}'
        body = (
            f'Olá {user.name},\n\n'
            f"A task '{task.title}' está atrasada!\n\n"
            f'Data limite: {task.due_date}'
        )
        self.send_email(user.email, subject, body)
