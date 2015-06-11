from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class HelsinkiAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get('html_url')

    def get_avatar_url(self):
        return self.account.extra_data.get('avatar_url')

    def to_str(self):
        dflt = super(HelsinkiAccount, self).to_str()
        return self.account.extra_data.get('name', dflt)


class HelsinkiProvider(OAuth2Provider):
    id = 'helsinki'
    name = 'City of Helsinki employees'
    package = 'helusers.providers.helsinki'
    account_class = HelsinkiAccount

    def extract_uid(self, data):
        return str(data['uuid'])

    def extract_common_fields(self, data):
        return data.copy()

    def get_default_scope(self):
        return ['read']

providers.registry.register(HelsinkiProvider)


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        exclude_fields = ['is_staff', 'password', 'is_superuser']
        user_fields = [f.name for f in user._meta.fields if f not in exclude_fields]
        for field in user_fields:
            if field in data:
                setattr(user, field, data[field])
        return user
