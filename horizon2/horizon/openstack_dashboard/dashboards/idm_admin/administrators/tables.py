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

from horizon import tables

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


class ManageAuthorizedMembersLink(tables.LinkAction):
    name = "manage_administrators"
    verbose_name = ("Authorize")
    url = "horizon:idm_admin:administrators:members"
    classes = ("ajax-modal",)
    icon = "key"

    def allowed(self, request, user):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        idm_admin = fiware_api.keystone.get_idm_admin_app(request)
        if not idm_admin:
            return False
        default_org = fiware_api.keystone.user_get(
            request, request.user).default_project_id
        allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
            request,
            user=request.user.id,
            organization=default_org)
        return allowed.get(idm_admin.id, False)


class MembersTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_USER_MEDIUM_AVATAR))
    name = tables.Column(lambda obj: getattr(obj, 'username', obj.name))
    pagination_url = 'fiware_complex_server_filters_users'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(MembersTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'application_id': fiware_api.keystone.get_idm_admin_app(self.request).id})
    
    class Meta:
        name = "members"
        verbose_name = ("Authorized Administrators")
        multi_select = False
        row_class = idm_tables.UserClickableRow
        table_actions = (tables.FilterAction, ManageAuthorizedMembersLink,)
