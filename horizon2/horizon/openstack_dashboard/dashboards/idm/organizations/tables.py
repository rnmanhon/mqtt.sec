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

import logging

from django.core import urlresolvers

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.local import local_settings
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


LOG = logging.getLogger('idm_logger')


class OtherOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', ''))
    hide_panel = True
    pagination_url = 'fiware_complex_server_filters_organizations'
    empty_message = 'There are no other organizations.'
    filter_data = {
        'organization_role': 'OTHER',
    }

    class Meta:
        name = "other_organizations"
        verbose_name = ("")
        row_class = idm_tables.OrganizationClickableRow


class OwnedOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', ''))
    switch = tables.Column(lambda obj: idm_utils.get_switch_url(
        obj, check_switchable=False))
    hide_panel = True
    pagination_url = 'fiware_complex_server_filters_organizations'
    empty_message = 'You are not owner of any organization.'
    filter_data = {
        'organization_role': getattr(local_settings, "KEYSTONE_OWNER_ROLE"),
    }

    class Meta:
        name = "owned_organizations"
        verbose_name = ("")
        row_class = idm_tables.OrganizationClickableRow


class MemberOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None))
    hide_panel = True
    pagination_url = 'fiware_complex_server_filters_organizations'
    empty_message = 'You are not member of any organization.'
    filter_data = {
        'organization_role': getattr(local_settings, "OPENSTACK_KEYSTONE_DEFAULT_ROLE"),
    }

    class Meta:
        name = "member_organizations"
        verbose_name = ("")
        row_class = idm_tables.OrganizationClickableRow


class ManageMembersLink(tables.LinkAction):
    name = "manage_members"
    verbose_name = ("Manage")
    url = "horizon:idm:organizations:members"
    classes = ("ajax-modal",)
    icon = "cogs"

    def allowed(self, request, user):
        # Allowed if he is an owner in the organization
        # TODO(garcianavalon) move to fiware_api
        org_id = self.table.kwargs['organization_id']
        user_roles = api.keystone.roles_for_user(
            request, request.user.id, project=org_id)
        owner_role = fiware_api.keystone.get_owner_role(request)
        return owner_role.id in [r.id for r in user_roles]

    def get_link_url(self, datum=None):
        org_id = self.table.kwargs['organization_id']
        return  urlresolvers.reverse(self.url, args=(org_id,))


class MembersTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_USER_MEDIUM_AVATAR))
    username = tables.Column('username', verbose_name=('Members'))
    empty_message = 'This organization does not have any members.'
    pagination_url = 'fiware_complex_server_filters_users'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(MembersTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'organization_id': self.kwargs['organization_id']})

    class Meta:
        name = "members"
        verbose_name = ("Members")
        table_actions = (tables.FilterAction, ManageMembersLink, )
        multi_select = False
        row_class = idm_tables.UserClickableRow


class AuthorizingApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Applications'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    empty_message = 'This organization does not have any authorizing applications'
    pagination_url = 'fiware_complex_server_filters_applications'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(AuthorizingApplicationsTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'organization_id': self.kwargs['organization_id']})

    class Meta:
        name = "applications"
        verbose_name = ("Authorizing Applications")
        row_class = idm_tables.ApplicationClickableRow
        table_actions = (tables.FilterAction,)
