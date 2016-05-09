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

from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


class ManageMembersLink(tables.LinkAction):
    name = "manage_members"
    verbose_name = ("Add")
    url = "horizon:idm:home_orgs:members"
    classes = ("ajax-modal", "link",)

class RegisterApplication(tables.LinkAction):
    name = "register_application"
    verbose_name = "Register"
    url = "horizon:idm:myApplications:create"
    classes = ("link",)
    render_as_link = True

class MembersTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_USER_MEDIUM_AVATAR))
    username = tables.Column('username', verbose_name=('Members'))
    view_all_url = 'horizon:idm:organizations:index'
    pagination_url = 'fiware_complex_server_filters_users'
    empty_message = 'No members.'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(MembersTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'organization_id': self.request.organization.id})

    class Meta:
        name = "members"
        verbose_name = ("Members")
        table_actions = (ManageMembersLink, )
        multi_select = False
        row_class = idm_tables.UserClickableRow
        template = 'idm/home/_data_table.html'


class ApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    view_all_url = 'horizon:idm:organizations:index'
    pagination_url = 'fiware_complex_server_filters_applications'
    empty_message = 'You are not authorized in any application.'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(ApplicationsTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'organization_id': self.request.organization.id})


    class Meta:
        name = "applications"
        verbose_name = ("Applications")
        table_actions = (RegisterApplication,)
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow
        template = 'idm/home/_data_table.html'
        
