# Copyright (C) 2014 Universidad Politecnica de Madrid
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import base64
import datetime
import io
import logging
import os

import pyqrcode

from django.conf import settings

from django.core.cache import cache
from django.core.signing import Signer
from django.shortcuts import redirect

from horizon import forms
from horizon import messages
from horizon import views

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.settings.multisettings \
    import forms as settings_forms


LOG = logging.getLogger('idm_logger')

class MultiFormView(views.APIView):
    template_name = 'settings/multisettings/index.html'
    
    def get_context_data(self, **kwargs):
        context = super(MultiFormView, self).get_context_data(**kwargs)

        # Initial data
        user_id = self.request.user.id
        user = fiware_api.keystone.user_get(self.request, user_id)
        initial_email = {
            'email': user.name
        }

        # Current account_type
        # TODO(garcianavalon) find a better solution to this
        user_roles = [a.role['id'] for a in fiware_api.keystone.role_assignments_list(self.request, 
            user=user_id, domain='default')]
        basic_role = fiware_api.keystone.get_basic_role(self.request, use_idm_account=True)
        trial_role = fiware_api.keystone.get_trial_role(self.request, use_idm_account=True)
        community_role = fiware_api.keystone.get_community_role(self.request, use_idm_account=True)
        account_roles = [
            basic_role,
            trial_role,
            community_role,
        ]
        account_type = next((r.name for r in account_roles 
            if r.id in user_roles), None)

        account_info = {
            'account_type': str(account_type),
            'started_at': getattr(user, str(account_type) + '_started_at', None),
            'duration': getattr(user, str(account_type) + '_duration', None),
            #'regions': self._current_regions(self.user.cloud_project_id)
        }

        if account_info['started_at'] and account_info['duration']:
            start_date = datetime.datetime.strptime(account_info['started_at'], '%Y-%m-%d')
            end_date = start_date + datetime.timedelta(days=account_info['duration'])
            account_info['end_date'] = end_date.strftime('%Y-%m-%d')

        context['account_info'] = account_info

        if account_type != community_role.name:
            context['show_community_request'] = True

        if (account_type == basic_role.name 
            and len(fiware_api.keystone.get_trial_role_assignments(self.request)) 
                < getattr(settings, 'MAX_TRIAL_USERS', 0)):
            context['show_trial_request'] = True

        if fiware_api.keystone.two_factor_is_enabled(self.request, user):
            context['two_factor_enabled'] = True

        #Create forms
        status = settings_forms.UpgradeForm(self.request)
        cancel = settings_forms.BasicCancelForm(self.request)
        password = settings_forms.PasswordForm(self.request)
        email = settings_forms.EmailForm(self.request, initial=initial_email)
        two_factor = settings_forms.ManageTwoFactorForm(self.request)

        idm_username = getattr(settings, 'IDM_USER_CREDENTIALS')['username']

        if idm_username == user.name:
            context['forms'] = [status, password, email, cancel]
        else:
            context['forms'] = [status, password, email, two_factor, cancel]
        return context


# Handeling views
class AccountStatusView(forms.ModalFormView):
    form_class = settings_forms.UpgradeForm
    template_name = 'settings/multisettings/status.html'

class PasswordView(forms.ModalFormView):
    form_class = settings_forms.PasswordForm
    template_name = 'settings/multisettings/change_password.html'

class EmailView(forms.ModalFormView):

    form_class = settings_forms.EmailForm
    template_name = 'settings/multisettings/change_email.html'

    def get_form_kwargs(self):
        kwargs = super(EmailView, self).get_form_kwargs()
        user_id = self.request.user.id
        user = fiware_api.keystone.user_get(self.request, user_id)
        kwargs['initial']['email'] = getattr(user, 'name', '')
        return kwargs

class CancelView(forms.ModalFormView):
    form_class = settings_forms.BasicCancelForm
    template_name = 'settings/multisettings/cancel.html'

class ManageTwoFactorView(forms.ModalFormView):
    form_class = settings_forms.ManageTwoFactorForm
    template_name = 'settings/multisettings/two_factor.html'

    def get_context_data(self, **kwargs):
        context = super(ManageTwoFactorView, self).get_context_data(**kwargs)
        
        user = fiware_api.keystone.user_get(self.request, self.request.user.id)
        if fiware_api.keystone.two_factor_is_enabled(self.request, user):
            context['two_factor_enabled'] = True
        return context

class DisableTwoFactorView(forms.ModalFormView):
    form_class = settings_forms.DisableTwoFactorForm
    template_name = 'settings/multisettings/two_factor_disable.html'

    def dispatch(self, request, *args, **kwargs):
        user_id = self.request.user.id
        user = fiware_api.keystone.user_get(self.request, user_id)
        if not fiware_api.keystone.two_factor_is_enabled(self.request, user):
            return redirect('horizon:settings:multisettings:index')
        return super(DisableTwoFactorView, self).dispatch(request, args, kwargs)

class ForgetTwoFactorDevicesView(forms.ModalFormView):
    form_class = settings_forms.ForgetTwoFactorDevicesForm
    template_name = 'settings/multisettings/two_factor_forget_devices.html'

    def dispatch(self, request, *args, **kwargs):
        user_id = self.request.user.id
        user = fiware_api.keystone.user_get(self.request, user_id)
        if not fiware_api.keystone.two_factor_is_enabled(self.request, user):
            return redirect('horizon:settings:multisettings:index')
        return super(ForgetTwoFactorDevicesView, self).dispatch(request, args, kwargs)

class TwoFactorNewKeyView(views.APIView):
    template_name = 'settings/multisettings/two_factor_newkey.html'

    def get_template_names(self):
        if self.request.is_ajax():
            if not hasattr(self, "ajax_template_name"):
                # Transform standard template name to ajax name (leading "_")
                bits = list(os.path.split(self.template_name))
                bits[1] = "".join(("_", bits[1]))
                self.ajax_template_name = os.path.join(*bits)
            template = self.ajax_template_name
        else:
            template = self.template_name
        return template

    def get_context_data(self, **kwargs):
        context = super(TwoFactorNewKeyView, self).get_context_data(**kwargs)
        cache_key = self.request.session['two_factor_data']
        del self.request.session['two_factor_data']

        (key, uri) = cache.get(cache_key)
        cache.delete(cache_key)
        
        context['two_factor_key'] = key
        qr = pyqrcode.create(uri, error='L')
        qr_buffer = io.BytesIO()
        qr.svg(qr_buffer, scale=3)
        context['two_factor_qr_encoded'] = base64.b64encode(qr_buffer.getvalue())
        
        return context

    def dispatch(self, request, *args, **kwargs):
        if 'two_factor_data' not in self.request.session:
            return redirect('horizon:settings:multisettings:index')
        return super(TwoFactorNewKeyView, self).dispatch(request, args, kwargs)


def email_verify_and_update(request):
    """If the verification_key is correct, change the user email."""
    # check the verification_key
    name = request.user.name
    new_email = request.GET.get('new_email')
    signer = Signer()
    expected_verification_key = signer.sign(name + new_email).split(':')[1]

    if expected_verification_key == request.GET.get('verification_key'):

        # now update email
        user_id = request.user.id

        # if we dont set password to None we get a dict-key error in api/keystone
        api.keystone.user_update(
            request,
            user_id,
            name=new_email,
            password=None)

        msg = 'Email changed succesfully.'
        messages.success(request, msg)
    else:
        msg = 'Invalid verification key. Email not updated.'
        messages.error(request, msg)

    # redirect user to settings home
    response = redirect('horizon:settings:multisettings:index')
    return response
