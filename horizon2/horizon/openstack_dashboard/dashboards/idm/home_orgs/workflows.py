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
from django.core import urlresolvers

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import workflows as idm_workflows
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.organizations import workflows as organization_workflows

LOG = logging.getLogger('idm_logger')
INDEX_URL = 'horizon:idm:home_orgs:index'

# ORGANIZATION ROLES

class UpdateProjectMembersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = ('Unable to retrieve user list. Please try again later.')
    RELATIONSHIP_CLASS = organization_workflows.UserRoleApi
    ERROR_URL = INDEX_URL
    class Meta:
        name = ("Organization Members")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateProjectMembers(idm_workflows.UpdateRelationshipStep):
    action_class = UpdateProjectMembersAction
    available_list_title = ("All Users")
    members_list_title = ("Organization Members")
    no_available_text = ("No users found.")
    no_members_text = ("No users.")
    RELATIONSHIP_CLASS = organization_workflows.UserRoleApi
    server_filter_url = urlresolvers.reverse_lazy(
        'fiware_complex_server_filters_users')


class ManageOrganizationMembers(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_users"
    name = ("Manage Members")
    finalize_button_name = ("Save")
    success_message = ('Modified users.')
    failure_message = ('Unable to modify users.')
    success_url = "horizon:idm:home_orgs:index"
    default_steps = (UpdateProjectMembers,)
    RELATIONSHIP_CLASS = organization_workflows.UserRoleApi
    member_slug = idm_workflows.RELATIONSHIP_SLUG
    current_user_editable = False
    no_roles_message = 'Some users don\'t have any role assigned. \
        If you save now they won\'t be part of the organization'
    
    # def get_success_url(self):
    #     # Overwrite to allow passing kwargs
    #     return reverse(self.success_url, 
    #                 kwargs={'organization_id':self.context['superset_id']})


