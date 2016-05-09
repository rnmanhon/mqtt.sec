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

from django.shortcuts import redirect

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm \
    import utils as idm_utils
from openstack_dashboard.dashboards.idm_admin.administrators \
    import tables as administrators_tables
from openstack_dashboard.dashboards.idm_admin \
    import utils as idm_admin_utils
from openstack_dashboard.dashboards.idm_admin.administrators \
    import workflows as administrators_workflows
from openstack_dashboard.local import local_settings


class DetailApplicationView(tables.MultiTableView):
    template_name = 'idm_admin/administrators/index.html'
    table_classes = (administrators_tables.MembersTable, )

    def dispatch(self, request, *args, **kwargs):
        if idm_admin_utils.is_current_user_administrator(request):
            return super(DetailApplicationView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')

    def get_members_data(self):
        users = []
        # try:
        #     # NOTE(garcianavalon) Get all the users' ids that belong to
        #     # the application (they have one or more roles)
        #     all_users = fiware_api.keystone.user_list(self.request,
        #                                        filters={'enabled':True})
        #     role_assignments = fiware_api.keystone.user_role_assignments(
        #         self.request,
        #         application=fiware_api.keystone.get_idm_admin_app(
        #             self.request).id)
        #     users = [user for user in all_users if user.id
        #              in set([a.user_id for a in role_assignments])]
            
        #     users = sorted(users, key=lambda x: getattr(x, 'username', x.name).lower())

        #     self._tables['members'].pages = idm_utils.total_pages(users, LIMIT)

        #     users = idm_utils.paginate_list(users, 1, LIMIT)
        
        # except Exception:
        #     exceptions.handle(self.request,
        #                       ("Unable to retrieve member information."))
        return users

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(DetailApplicationView, self).get_context_data(**kwargs)
        application_id = fiware_api.keystone.get_idm_admin_app(
            self.request).id
        return context


class ManageMembersView(workflows.WorkflowView):
    workflow_class = administrators_workflows.ManageAuthorizedMembers

    def dispatch(self, request, *args, **kwargs):
        if idm_admin_utils.is_current_user_administrator(request):
            return super(ManageMembersView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')
            
    def get_initial(self):
        initial = super(ManageMembersView, self).get_initial()
        initial['superset_id'] = fiware_api.keystone.get_idm_admin_app(
            self.request).id
        return initial
