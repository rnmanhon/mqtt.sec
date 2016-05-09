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

import horizon

from openstack_dashboard.dashboards.idm_admin import utils as idm_admin_utils


class Idm_Admin(horizon.Dashboard):
    name = (" ")
    name_sm = (" ")
    slug = "idm_admin"
    panels = ('notify', 'administrators', 'user_accounts')
    default_panel = 'notify'

    def nav(self, context):
        # NOTE(garcianavalon) hide it if the user doesn't belong to idm_admin
        request = context['request']
        return idm_admin_utils.is_current_user_administrator(request)


horizon.register(Idm_Admin)
