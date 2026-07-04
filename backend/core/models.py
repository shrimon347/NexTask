import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base model shared by domain entities.

    Provides:
    - UUID primary key
    - soft activation flag
    - automatic created/updated timestamps
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
