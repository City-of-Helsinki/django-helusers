import uuid
import logging
from django.db import models
from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

from .utils import uuid_to_username


logger = logging.getLogger(__name__)


class AbstractUser(DjangoAbstractUser):
    uuid = models.UUIDField(unique=True)
    department_name = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.clean()
        return super(AbstractUser, self).save(*args, **kwargs)

    def clean(self):
        self._make_sure_uuid_is_set()
        if not self.username:
            self.set_username_from_uuid()
        super(AbstractUser, self).clean()

    def _make_sure_uuid_is_set(self):
        if self.uuid is None:
            self.uuid = uuid.uuid1()

    def set_username_from_uuid(self):
        self._make_sure_uuid_is_set()
        self.username = uuid_to_username(self.uuid)

    class Meta:
        abstract = True
