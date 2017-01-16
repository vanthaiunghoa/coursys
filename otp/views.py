from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django_cas.views import _redirect_url

from courselib.auth import ForbiddenResponse, NotFoundResponse
from six.moves.urllib.parse import urlencode
from django_otp.models import Device
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import all_otp_devices, any_otp_device, totpauth_url
from .forms import TokenForm

import datetime
import qrcode
import qrcode.image.svg


def _setup_view(request, next_page):
    '''
    Common logic to set up these views: make sure Django auth is done and check our conditions.
    '''
    if not next_page and 'next' in request.GET:
        next_page = request.GET['next']
    if not next_page:
        next_page = _redirect_url(request)

    if not request.maybe_stale_user.is_authenticated():
        # Not authenticated at all. Force standard-Django auth.
        return next_page, False, False

    okay_auth = request.session_info.okay_age_auth(request.maybe_stale_user)
    okay_2fa = request.session_info.okay_age_2fa(request.maybe_stale_user)

    return next_page, okay_auth, okay_2fa



def login_2fa(request, next_page=None):
    next_page, okay_auth, okay_2fa = _setup_view(request, next_page)

    if not okay_auth:
        # Stale standard-Django authentication: redirect to normal login page.
        return HttpResponseRedirect(settings.PASSWORD_LOGIN_URL + '?' + urlencode({'next': next_page}))

    if not okay_2fa:
        # need to do 2FA for this user
        if not any_otp_device(request.maybe_stale_user):
            messages.add_message(request, messages.WARNING, 'You are required to do two-factor authentication but have no device enabled. You must add one.')
            return HttpResponseRedirect(reverse('otp:add_topt'))

        form = TokenForm(user=request.maybe_stale_user, request=request)
        context = {
            'form': form,
        }
        return render(request, 'otp/login_2fa.html', context)

    return HttpResponseRedirect(next_page)


def add_topt(request, next_page=None):
    next_page, okay_auth, okay_2fa = _setup_view(request, next_page)

    if not okay_auth:
        return ForbiddenResponse(request)

    # TODO: if they already have 2FA set up, should also check okay_2fa.

    if 'qr' in request.GET:
        # this is a request for the QR code for a device's URL.
        factory = qrcode.image.svg.SvgPathImage
        devs = TOTPDevice.objects.filter(user=request.maybe_stale_user, id=request.GET['qr'])
        if not devs:
            return NotFoundResponse()

        device = devs[0]
        qr = qrcode.make(totpauth_url(device), image_factory=factory)
        response = HttpResponse(content_type='image/svg+xml')
        qr.save(response)
        return response

    # TODO: if the user has an existing device, should we re-use that? What's best practice?
    device = TOTPDevice(user=request.maybe_stale_user, name='Authenticator, enabled %s' % (datetime.date.today()))
    device.save()
    context = {
        'device': device,
    }
    return render(request, 'otp/add_topt.html', context)
