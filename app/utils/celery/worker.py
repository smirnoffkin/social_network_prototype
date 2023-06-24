from celery import Celery

from app.config import settings

celery = Celery("tasks", broker=settings.broker_url)


@celery.task
def verify_email_for_registration(email: str) -> bool:
    """
    Confirmation of mail for registration.
    TO DO: find and add a service for mail verification.
    For now, it's used as a stub function
    """
    return True
