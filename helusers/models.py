import uuid
import logging
from django.db import models
from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

logger = logging.getLogger(__name__)


class AbstractUser(DjangoAbstractUser):
    uuid = models.UUIDField(unique=True)
    department_name = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.uuid is None:
            self.uuid = uuid.uuid1()
        return super(AbstractUser, self).save(*args, **kwargs)

    class Meta:
        abstract = True
