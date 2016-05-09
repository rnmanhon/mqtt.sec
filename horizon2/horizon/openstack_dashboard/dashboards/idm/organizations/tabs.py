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

from horizon import exceptions
from horizon import tabs

from django.core.cache import cache

from openstack_dashboard import fiware_api
from openstack_dashboard.local import local_settings as settings
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables

LOG = logging.getLogger('idm_logger')
LIMIT = getattr(settings, 'PAGE_LIMIT', 8)


class OtherOrganizationsTab(tabs.TableTab):
    name = ("Other Organizations")
    slug = "other_organizations_tab"
    table_classes = (organization_tables.OtherOrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_other_organizations_data(self):
        organizations = []
        # try:
        #     all_organizations = fiware_api.keystone.project_list(
        #         self.request)
        #     my_organizations = fiware_api.keystone.project_list(
        #         self.request, user=self.request.user.id)

        #     organizations = idm_utils.filter_default(
        #         [t for t in all_organizations if not t in my_organizations])
        #     organizations = sorted(organizations, key=lambda x: x.name.lower())
        
        #     self._tables['other_organizations'].pages = idm_utils.total_pages(
        #         organizations, LIMIT)

        #     organizations = idm_utils.paginate_list(organizations, 1, LIMIT)

        # except Exception as e:
        #     exceptions.handle(self.request,
        #                       ("Unable to retrieve organization list. \
        #                             Error message: {0}".format(e)))
        return organizations


class OwnedOrganizationsTab(tabs.TableTab):
    name = ("Owner")
    slug = "owned_organizations_tab"
    table_classes = (organization_tables.OwnedOrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_owned_organizations_data(self):
        organizations = []
        # try:
        #     # NOTE(garcianavalon) the organizations the user is owner(admin)
        #     # are already in the request object by the middleware
        #     organizations = self.request.organizations
        #     organizations = idm_utils.filter_default(
        #         sorted(organizations, key=lambda x: x.name.lower()))

        #     self._tables['owned_organizations'].pages = idm_utils.total_pages(
        #         organizations, LIMIT)

        #     organizations = idm_utils.paginate_list(organizations, 1, LIMIT)

        # except Exception:
        #     exceptions.handle(self.request,
        #                       ("Unable to retrieve organization information."))
        return organizations


class MemberOrganizationsTab(tabs.TableTab):
    name = ("Member")
    slug = "member_organizations_tab"
    table_classes = (organization_tables.MemberOrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_member_organizations_data(self):
        organizations = []
        # try:
        #     my_organizations = fiware_api.keystone.project_list(
        #         self.request, user=self.request.user.id)
        #     owner_organizations = [org.id for org in self.request.organizations]
        #     organizations = [o for o in my_organizations 
        #                      if not o.id in owner_organizations]

        #     organizations = idm_utils.filter_default(sorted(organizations, key=lambda x: x.name.lower()))

        #     self._tables['member_organizations'].pages = idm_utils.total_pages(
        #         organizations, LIMIT)

        #     organizations = idm_utils.paginate_list(organizations, 1, LIMIT)

        # except Exception:
        #     exceptions.handle(self.request,
        #                       ("Unable to retrieve organization information."))
        return organizations


class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (OwnedOrganizationsTab, MemberOrganizationsTab, OtherOrganizationsTab)
    sticky = True