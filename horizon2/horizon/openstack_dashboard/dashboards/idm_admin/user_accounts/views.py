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

import datetime
import logging
import json

from django import http
from django.conf import settings
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from horizon import forms

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm_admin.user_accounts \
    import forms as user_accounts_forms
from openstack_dashboard.dashboards.idm_admin \
    import utils as idm_admin_utils
from openstack_dashboard.fiware_auth import views as fiware_auth
from openstack_dashboard.utils import email as email_utils


LOG = logging.getLogger('idm_logger')

FIWARE_DEFAULT_DURATION = getattr(settings, 'FIWARE_DEFAULT_DURATION')
KEYSTONE_TRIAL_ROLE = getattr(settings, 'KEYSTONE_TRIAL_ROLE')
KEYSTONE_BASIC_ROLE = getattr(settings, 'KEYSTONE_BASIC_ROLE')
KEYSTONE_COMMUNITY_ROLE = getattr(settings, 'KEYSTONE_COMMUNITY_ROLE')


def _current_account(request, user_id):
    # TODO(garcianavalon) find a better solution to this
    user_roles = [
        a.role['id'] for a 
        in fiware_api.keystone.role_assignments_list(request, 
            user=user_id, domain='default')
    ]
   
    fiware_roles = user_accounts_forms.get_account_choices()

    return next((role for role in fiware_roles
        if role[0] in user_roles), (None, None))

def _current_regions(request, cloud_project_id):
    endpoint_groups = fiware_api.keystone.list_endpoint_groups_for_project(
        request, cloud_project_id)
    current_regions = []
    for endpoint_group in endpoint_groups:
        if 'region_id' in endpoint_group.filters:
            current_regions.append(endpoint_group.filters['region_id'])
    return current_regions

class FindUserView(forms.ModalFormView):
    form_class = user_accounts_forms.FindUserByEmailForm
    template_name = 'idm_admin/user_accounts/index.html'

    def dispatch(self, request, *args, **kwargs):
        if idm_admin_utils.is_current_user_administrator(request):
            return super(FindUserView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')


class UpdateAccountView(forms.ModalFormView):
    form_class = user_accounts_forms.UpdateAccountForm
    template_name = 'idm_admin/user_accounts/update.html'
    success_url = 'horizon:idm_admin:user_accounts:update'

    def dispatch(self, request, *args, **kwargs):
        if idm_admin_utils.is_current_user_administrator(request):
            self.user = fiware_api.keystone.user_get(request,
                kwargs['user_id'])
            return super(UpdateAccountView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')

    def get_context_data(self, **kwargs):
        context = super(UpdateAccountView, self).get_context_data(**kwargs)
        user = self.user

        context['user'] = user

        context['allowed_regions'] = json.dumps(
            getattr(settings, 'FIWARE_ALLOWED_REGIONS', None))

        context['default_durations'] = json.dumps(FIWARE_DEFAULT_DURATION)

        account_type = _current_account(self.request, user.id)[1]
        account_info = {
            'account_type': account_type,
            'started_at': getattr(user, str(account_type) + '_started_at', None),
            'duration': getattr(user, str(account_type) + '_duration',
                                FIWARE_DEFAULT_DURATION.get(account_type)),
            'regions': _current_regions(self.request, user.cloud_project_id)
        }

        if account_info['started_at'] and account_info['duration']:
            start_date = datetime.datetime.strptime(account_info['started_at'], '%Y-%m-%d')
            end_date = start_date + datetime.timedelta(days=account_info['duration'])
            account_info['end_date'] = end_date.strftime('%Y-%m-%d')

        context['account_info'] = account_info
        return context

    def get_initial(self):
        initial = super(UpdateAccountView, self).get_initial()
        user_id = self.user.id
        
        current_account = _current_account(self.request, user_id)
        current_regions = _current_regions(self.request, self.user.cloud_project_id)

        initial.update({
            'user_id': user_id,
            'regions': [(region_id, region_id) for region_id in current_regions],
            'account_type': current_account[0],
        })
        return initial


class UpdateAccountEndpointView(View, user_accounts_forms.UserAccountsLogicMixin):
    """ Upgrade account logic without the form"""
    http_method_names = ['post']
    use_idm_account = True
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # Check there is a valid keystone token in the header
        token = request.META.get('HTTP_X_AUTH_TOKEN', None)
        if not token:
            return http.HttpResponse('Unauthorized', status=401)

        try:
            idm_admin_utils.is_user_administrator_from_token(request, token=token)
            
        except Exception:
            return http.HttpResponse('Unauthorized', status=401)

        return super(UpdateAccountEndpointView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = fiware_api.keystone.user_get(request, data['user_id'])
            role_id = data['role_id']

            if (role_id == fiware_api.keystone.get_trial_role(
                request).id):

                trial_left = self._max_trial_users_reached(request)
                if not trial_left:
                    return http.HttpResponseNotAllowed()

            regions = data.get('regions', [])

            if (role_id != fiware_api.keystone.get_basic_role(
                    request).id
                and not regions):

                return http.HttpResponseBadRequest()

            self.update_account(request, user, role_id, regions)

            if data.get('notify'):

                account_type = _current_account(self.request, user.id)[1]

                content = {
                    'regions': _current_regions(self.request, user.cloud_project_id),
                    'user':user,
                    'account_type': account_type,
                    'started_at': getattr(user, account_type + '_started_at', None),
                    'duration': getattr(user, account_type + '_duration',
                                        FIWARE_DEFAULT_DURATION.get(account_type)),
                    'show_cloud_info': account_type in ['trial', 'community'],
                }

                if content['started_at'] and content['duration']:
                    start_date = datetime.datetime.strptime(content['started_at'], '%Y-%m-%d')
                    end_date = start_date + datetime.timedelta(days=content['duration'])
                    content['end_date'] = end_date.strftime('%Y-%m-%d')

                email_utils.send_account_status_change_email(
                    user=user,
                    content=content)

            return http.HttpResponse()

        except Exception as exception:
            return http.HttpResponseServerError(str(exception), content_type="text/plain")


class NotifyUsersEndpointView(View):
    """Notify a list of users that their resources are about to be deleted."""
    http_method_names = ['post']
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # Check there is a valid keystone token in the header
        token = request.META.get('HTTP_X_AUTH_TOKEN', None)
        if not token:
            return http.HttpResponse('Unauthorized', status=401)

        try:
            idm_admin_utils.is_user_administrator_from_token(request, token=token)

        except Exception:
            return http.HttpResponse('Unauthorized', status=401)

        return super(NotifyUsersEndpointView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        
        data = json.loads(request.body)
        errors = []

        for user_id in data['users']:
            try:
                user = fiware_api.keystone.user_get(request, user_id)
                account_type = _current_account(self.request, user.id)[1]

                if not account_type:
                    errors.append((user_id, 'Has no basic, trial or community rol assigned.'))
                    continue
                elif account_type == 'basic':
                    errors.append((user_id, 'User is basic.'))
                    continue

                content = {
                    'regions': _current_regions(self.request, user.cloud_project_id),
                    'user':user,
                    'account_type': account_type,
                    'started_at': getattr(user, account_type + '_started_at'),
                    'duration': getattr(user, account_type + '_duration',
                                        FIWARE_DEFAULT_DURATION.get(account_type)),
                    'show_cloud_info': account_type in ['trial', 'community'],
                }
                # NOTE(garcianavalon) there should always be an end date in this email
                # if content.get('started_at') and content.get('duration'):
                start_date = datetime.datetime.strptime(content['started_at'], '%Y-%m-%d')
                end_date = start_date + datetime.timedelta(days=content['duration'])
                content['end_date'] = end_date.strftime('%Y-%m-%d')

                email_utils.send_account_status_expire_email(
                    user=user,
                    content=content)

            except Exception as exception:
                errors.append((user_id, str(exception)))
                continue

        return http.HttpResponse(json.dumps({'error_users': errors}),
                                 content_type="application/json")

