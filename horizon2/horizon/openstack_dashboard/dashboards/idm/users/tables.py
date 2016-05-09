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

from django.conf import settings

from horizon import tables

from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


LOG = logging.getLogger('idm_logger')

class OrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', ''),
                                verbose_name=('Description'))
    empty_message = 'You don\'t have any organizations.'
    pagination_url = 'fiware_complex_server_filters_organizations'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(OrganizationsTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'user_id': self.kwargs['user_id']})

    class Meta:
        name = "organizations"
        verbose_name = ("Organizations")
        row_class = idm_tables.OrganizationClickableRow
        table_actions = (tables.FilterAction,)


class ApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Applications'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    empty_message = 'You are not authorized in any application.'
    pagination_url = 'fiware_complex_server_filters_applications'
    filter_data = {
    }

    def __init__(self, *args, **kwargs):
        super(ApplicationsTable, self).__init__(*args, **kwargs)
        self.filter_data.update({'user_id': self.kwargs['user_id']})

    class Meta:
        name = "applications"
        verbose_name = ("Applications")
        row_class = idm_tables.ApplicationClickableRow
        table_actions = (tables.FilterAction,)
