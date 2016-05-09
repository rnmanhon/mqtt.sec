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

from django.core import urlresolvers

from horizon import tables

from openstack_dashboard import fiware_api
from openstack_dashboard.local import local_settings
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


class ProvidingApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    hide_panel = True
    pagination_url = 'fiware_complex_server_filters_applications'
    empty_message = 'You are not provider of any application.'
    filter_data = {
        'application_role': getattr(local_settings, "FIWARE_PROVIDER_ROLE_ID"),
    }

    
    class Meta:
        name = "providing_table"
        verbose_name = ("")
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow
        

class PurchasedApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    hide_panel = True
    pagination_url = 'fiware_complex_server_filters_applications'
    empty_message = 'You are not purchaser of any application.'
    filter_data = {
        'application_role': getattr(local_settings, "FIWARE_PURCHASER_ROLE_ID"),
    }

    class Meta:
        name = "purchased_table"
        verbose_name = ("")
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow


class AuthorizedApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    hide_panel = True
    pagination_url = 'fiware_complex_server_filters_applications'
    empty_message = 'You are not authorized in any application.'
    filter_data = {
        'application_role': 'OTHER',
    }

    class Meta:
        name = "authorized_table"
        verbose_name = ("")
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow


class ManageAuthorizedUsersLink(tables.LinkAction):
    name = "manage_application_users"
    verbose_name = ("Authorize")
    url = "horizon:idm:myApplications:users"
    classes = ("ajax-modal",)
    icon = "key"

    def allowed(self, request, user):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        if request.user.default_project_id == request.organization.id:
            allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
                request,
                user=request.user.id,
                organization=request.user.default_project_id)
        else:
            allowed = fiware_api.keystone.list_organization_allowed_roles_to_assign(
                request,
                organization=request.organization.id)
        app_id = self.table.kwargs['application_id']
        return allowed.get(app_id, False)

    def get_link_url(self, datum=None):
        app_id = self.table.kwargs['application_id']
        return  urlresolvers.reverse(self.url, args=(app_id,))


class AuthUsersTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_USER_MEDIUM_AVATAR))
    username = tables.Column('username')
    empty_message = 'This application does not have any authorized users.'
    pagination_url = 'fiware_complex_server_filters_users'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(AuthUsersTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'application_id': self.kwargs['application_id']})
            
    
    class Meta:
        name = "auth_users"
        verbose_name = ("Authorized Users")
        table_actions = (tables.FilterAction, ManageAuthorizedUsersLink, )
        multi_select = False
        row_class = idm_tables.UserClickableRow


class ManageAuthorizedOrganizationsLink(tables.LinkAction):
    name = "manage_application_organizations"
    verbose_name = ("Authorize")
    url = "horizon:idm:myApplications:organizations"
    classes = ("ajax-modal",)
    icon = "key"

    def allowed(self, request, user):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        if request.user.default_project_id == request.organization.id:
            allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
                request,
                user=request.user.id,
                organization=request.user.default_project_id)
        else:
            allowed = fiware_api.keystone.list_organization_allowed_roles_to_assign(
                request,
                organization=request.organization.id)
        app_id = self.table.kwargs['application_id']
        return allowed.get(app_id, False)

    def get_link_url(self, datum=None):
        app_id = self.table.kwargs['application_id']
        return  urlresolvers.reverse(self.url, args=(app_id,))


class AuthorizedOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Applications'))
    description = tables.Column(lambda obj: getattr(obj, 'description', ''))
    empty_message = 'This application does not have any authorized organizations.'
    pagination_url = 'fiware_complex_server_filters_organizations'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(AuthorizedOrganizationsTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'application_id': self.kwargs['application_id']})

    class Meta:
        name = "organizations"
        verbose_name = ("Authorized Organizations")
        table_actions = (tables.FilterAction, 
            ManageAuthorizedOrganizationsLink, )
        row_class = idm_tables.OrganizationClickableRow