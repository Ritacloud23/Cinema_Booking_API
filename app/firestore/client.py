import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import settings


def get_firestore_db():
    if not settings.FIRESTORE_ENABLED:
        return None

    if not firebase_admin._apps:
        credential = credentials.Certificate(
            settings.FIREBASE_CREDENTIALS_PATH
        )

        firebase_admin.initialize_app(
            credential,
            {
                "projectId": settings.FIREBASE_PROJECT_ID,
            },
        )

    return firestore.client()