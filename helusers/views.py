from collections import OrderedDict
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.views import View
from django.views.generic.base import RedirectView
from django.contrib.auth import logout, REDIRECT_FIELD_NAME
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib import messages
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from jose import JOSEError

from .jwt import JWT, ValidationError
from .models import OIDCBackChannelLogoutEvent
from . import oidc

LANGUAGE_FIELD_NAME = "ui_locales"


class LogoutView(DjangoLogoutView):
    def dispatch(self, request, *args, **kwargs):
        was_authenticated = request.user.is_authenticated
        session = request.session
        end_session_url = session.get("social_auth_end_session_url")
        if end_session_url:
            self.next_page = end_session_url
        ret = super().dispatch(request, *args, **kwargs)
        if was_authenticated:
            messages.success(request, _("You have been successfully logged out."))
        return ret


class LogoutCompleteView(DjangoLogoutView):
    def dispatch(self, request, *args, **kwargs):
        return HttpResponseRedirect(self.get_next_page())


class LoginView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        # We make sure the user is logged out first, because otherwise
        # PSA will enter the connect flow where a new social authentication
        # method is connected to an existing user account.
        logout(self.request)

        url = reverse("social:begin", kwargs=dict(backend="tunnistamo"))
        redirect_to = self.request.GET.get(REDIRECT_FIELD_NAME)
        lang = self.request.GET.get(LANGUAGE_FIELD_NAME)

        query_params = OrderedDict()
        if redirect_to:
            query_params[REDIRECT_FIELD_NAME] = redirect_to
        if lang:
            query_params[LANGUAGE_FIELD_NAME] = lang
        if query_params:
            url += "?" + urlencode(query_params)

        return url


class OIDCBackChannelLogout(View):
    http_method_names = ["post"]

    def _validate_request(self, request):
        if request.content_type != "application/x-www-form-urlencoded":
            return None

        try:
            logout_token = request.POST["logout_token"]
            jwt = JWT(logout_token)

            issuer = jwt.issuer

            keys = oidc.get_keys(issuer)
            jwt.validate(
                keys, oidc.accepted_audience(), required_claims={"aud", "iat", "jti"}
            )

            sub_or_sid_present = False
            for claim_name in ["sub", "sid"]:
                if claim_name in jwt.claims:
                    claim_value = jwt.claims[claim_name]
                    if not isinstance(claim_value, str):
                        raise ValidationError()
                    sub_or_sid_present = True
            if not sub_or_sid_present:
                raise ValidationError()

            events_value = jwt.claims["events"]
            if not isinstance(events_value, dict):
                raise ValidationError()
            logout_event_value = events_value[
                "http://schemas.openid.net/event/backchannel-logout"
            ]
            if not isinstance(logout_event_value, dict):
                raise ValidationError()

            if "nonce" in jwt.claims:
                raise ValidationError()
        except (JOSEError, KeyError, ValidationError):
            return None

        return jwt

    def _handle_request(self, request):
        jwt = self._validate_request(request)

        if jwt is None:
            return HttpResponseBadRequest()

        if OIDCBackChannelLogout._user_callback:
            response = OIDCBackChannelLogout._user_callback(request=request, jwt=jwt)
            if (
                isinstance(response, HttpResponse)
                and response.status_code >= 400
                and response.status_code < 600
            ):
                return response

        OIDCBackChannelLogoutEvent.objects.logout_token_received(jwt)

        return HttpResponse()

    def post(self, request, *args, **kwargs):
        response = self._handle_request(request)

        response["Cache-Control"] = "no-cache, no-store"
        response["Pragma"] = "no-cache"

        return response


def _update_back_channel_logout_user_callback():
    OIDCBackChannelLogout._user_callback = None
    try:
        callback_name = getattr(settings, "HELUSERS_BACK_CHANNEL_LOGOUT_CALLBACK", None)
        if callback_name:
            callback = import_string(callback_name)
            OIDCBackChannelLogout._user_callback = callback
    except ImportError:
        pass


_update_back_channel_logout_user_callback()


@receiver(setting_changed)
def _reload_config(setting, **kwargs):
    if setting == "HELUSERS_BACK_CHANNEL_LOGOUT_CALLBACK":
        _update_back_channel_logout_user_callback()
