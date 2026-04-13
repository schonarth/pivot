import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    api_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        db_table = "users"