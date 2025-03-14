import logging
import uuid
from collections import defaultdict
from itertools import chain

from django.contrib.auth.models import AbstractUser as DjangoAbstractUser
from django.contrib.auth.models import Group
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .utils import uuid_to_username

logger = logging.getLogger(__name__)


class ADGroup(models.Model):
    # Because AD group names are case insensitive, name is saved as lowercase.
    name = models.CharField(max_length=200, db_index=True)
    display_name = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


class ADGroupMapping(models.Model):
    group = models.ForeignKey(
        Group, db_index=True, on_delete=models.CASCADE, related_name="ad_groups"
    )
    ad_group = models.ForeignKey(
        ADGroup, db_index=True, on_delete=models.CASCADE, related_name="groups"
    )

    def __str__(self):
        return "%s -> %s" % (self.ad_group, self.group)

    class Meta:
        unique_together = (("group", "ad_group"),)
        verbose_name = _("AD group mapping")
        verbose_name_plural = _("AD group mappings")


class AbstractUser(DjangoAbstractUser):
    uuid = models.UUIDField(unique=True)
    department_name = models.CharField(max_length=50, null=True, blank=True)
    ad_groups = models.ManyToManyField(ADGroup, blank=True)

    def save(self, *args, **kwargs):
        self.clean()
        return super(AbstractUser, self).save(*args, **kwargs)

    def clean(self):
        self._make_sure_uuid_is_set()
        if not self.username:
            self.set_username_from_uuid()

    def _make_sure_uuid_is_set(self):
        if self.uuid is None:
            self.uuid = uuid.uuid1()

    def set_username_from_uuid(self):
        self._make_sure_uuid_is_set()
        self.username = uuid_to_username(self.uuid)

    def get_display_name(self):
        if self.first_name and self.last_name:
            return "{0} {1}".format(self.first_name, self.last_name).strip()
        else:
            return self.email

    def get_short_name(self):
        if self.first_name:
            return self.first_name
        return self.email

    def get_username(self):
        if not self.username or self.username.startswith("u-"):
            return self.email
        return self.username

    def natural_key(self):
        return (str(self.uuid),)

    def sync_groups_from_ad(self):
        """Determine which Django groups to add or remove based on AD groups."""

        ad_list = ADGroupMapping.objects.values_list("ad_group", "group")
        mappings = defaultdict(list)
        for ad_group, group in ad_list:
            mappings[ad_group].append(group)

        user_ad_groups = set(
            self.ad_groups.filter(groups__isnull=False).values_list(flat=True)
        )
        all_mapped_groups = set(chain(*mappings.values()))
        old_groups = set(
            self.groups.filter(id__in=all_mapped_groups).values_list(flat=True)
        )
        new_groups = set(chain(*[mappings[x] for x in user_ad_groups]))

        groups_to_delete = old_groups - new_groups
        if groups_to_delete:
            self.groups.remove(*groups_to_delete)
        groups_to_add = new_groups - old_groups
        if groups_to_add:
            self.groups.add(*groups_to_add)

    @transaction.atomic
    def update_ad_groups(self, ad_group_names):
        # Lock the User object to prevent races
        user = type(self).objects.select_for_update().get(id=self.id)

        # Make sure there's an ADGroup object for each group
        lower_names = [x.lower() for x in ad_group_names]
        ad_groups = {
            x.name.lower(): x for x in ADGroup.objects.filter(name__in=lower_names)
        }
        for name in ad_group_names:
            n = name.lower()
            if n not in ad_groups:
                ad_groups[n] = ADGroup.objects.create(name=n, display_name=name)

        # Update user's groups
        new_ad_groups = set([x.id for x in ad_groups.values()])
        old_ad_groups = set([x.id for x in user.ad_groups.all()])
        groups_to_add = new_ad_groups - old_ad_groups
        if groups_to_add:
            user.ad_groups.add(*groups_to_add)
        groups_to_remove = old_ad_groups - new_ad_groups
        if groups_to_remove:
            user.ad_groups.remove(*groups_to_remove)

        user.sync_groups_from_ad()

    def __str__(self):
        if self.first_name and self.last_name:
            return "%s %s (%s)" % (self.last_name, self.first_name, self.email)
        else:
            return self.email

    class Meta:
        abstract = True
        ordering = ("id",)


class OIDCBackChannelLogoutEventManager(models.Manager):
    def logout_token_received(self, logout_token):
        sub = logout_token.claims.get("sub", "")
        sid = logout_token.claims.get("sid", "")

        try:
            with transaction.atomic():
                self.create(iss=logout_token.issuer, sub=sub, sid=sid)
        except IntegrityError:
            pass

    def is_session_terminated_for_token(self, token):
        sid = token.claims.get("sid")
        if sid:
            return self.filter(iss=token.issuer, sid=sid).exists()

        return False


class OIDCBackChannelLogoutEvent(models.Model):
    created_at = models.DateTimeField(default=timezone.now, blank=False)
    iss = models.CharField(max_length=4096, db_index=True)
    sub = models.CharField(max_length=4096, blank=True, db_index=True)
    sid = models.CharField(max_length=4096, blank=True, db_index=True)

    objects = OIDCBackChannelLogoutEventManager()

    class Meta:
        unique_together = ["iss", "sub", "sid"]
        verbose_name = "OIDC back channel logout event"
        verbose_name_plural = "OIDC back channel logout events"
