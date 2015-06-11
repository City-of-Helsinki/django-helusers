import uuid
import logging
from django.db import models
from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

logger = logging.getLogger(__name__)


class AbstractUser(DjangoAbstractUser):
    uuid = models.UUIDField(primary_key=True)
    department_name = models.CharField(max_length=50, null=True, blank=True)
    primary_sid = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if self.uuid is None:
            self.uuid = uuid.uuid1()
        if not self.primary_sid:
            self.primary_sid = uuid.uuid4()
        return super(AbstractUser, self).save(*args, **kwargs)

    class Meta:
        abstract = True
