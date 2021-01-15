from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from deprecation import deprecated

from .user_utils import update_user


@deprecated(
    deprecated_in="0.6.0",
    details="Allauth based authentication is deprecated. Use the social-auth-app-django based authentication system.",
)
class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Update user based on token information."""

        user = sociallogin.user
        # If the user hasn't been saved yet, it will be updated
        # later on in the sign-up flow.
        if not user.pk:
            return

        data = sociallogin.account.extra_data
        oidc = sociallogin.account.provider == 'helsinki_oidc'
        update_user(user, data, oidc)

    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        exclude_fields = ['is_staff', 'password', 'is_superuser', 'id']
        user_fields = [f.name for f in user._meta.fields if f not in exclude_fields]
        for field in user_fields:
            if field in data:
                setattr(user, field, data[field])
        return user

    def save_user(self, request, sociallogin, form=None):
        # This is called at the end of the new user flow.
        u = sociallogin.user
        u.set_unusable_password()
        sociallogin.save(request)

        data = sociallogin.account.extra_data
        oidc = sociallogin.account.provider == 'helsinki_oidc'
        update_user(u, data, oidc)

        return u
