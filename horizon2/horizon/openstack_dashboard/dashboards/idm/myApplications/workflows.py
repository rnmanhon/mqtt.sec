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

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import workflows as idm_workflows

INDEX_URL = "horizon:idm:myApplications:index"
APPLICATION_ROLE_PERMISSION_SLUG = "fiware_roles"
LOG = logging.getLogger('idm_logger')

# ROLES AND PERMISSIONS
class RoleAndPermissionApi(idm_workflows.RelationshipApiInterface):
    """FIWARE Roles logic to assign"""

    def _list_all_owners(self, request, superset_id):
        role_list = []
        # TODO(garcianavalon) the default roles should be non editable!
        idm_app = fiware_api.keystone.get_idm_admin_app(request)
        role_list += fiware_api.keystone.role_list(request,
            application=idm_app.id)

        role_list += fiware_api.keystone.role_list(
            request, application=superset_id)

        # Save the role_list to use in the template
        self.application_roles = role_list
        return [(role.id, role.name) for role in role_list]

    def _list_all_objects(self, request, superset_id):
        permission_list = []
        # TODO(garcianavalon) the default roles should be non editable!
        idm_app = fiware_api.keystone.get_idm_admin_app(request)
        permission_list += fiware_api.keystone.permission_list(request,
            application=idm_app.id)

        permission_list += fiware_api.keystone.permission_list(
            request, application=superset_id)

        # Save the permission_list to use in the template
        self.application_permissions = permission_list
        return permission_list

    def _list_current_assignments(self, request, superset_id):
        application_role_permissions = {}
        role_list = getattr(self, 'application_roles',
            fiware_api.keystone.role_list(request, application=superset_id))
        for role in role_list:
            application_role_permissions[role.id] = [
                p.id for p in fiware_api.keystone.permission_list(
                    request, role=role.id)
            ]
        return application_role_permissions

    def _get_default_object(self, request):
        return None

    def _add_object_to_owner(self, request, superset, owner, obj):
        fiware_api.keystone.add_permission_to_role(
            request,
            permission=obj,
            role=owner)

    def _remove_object_from_owner(self, request, superset, owner, obj):
         fiware_api.keystone.remove_permission_from_role(
            request,
            permission=obj,
            role=owner)

    def _get_supersetid_name(self, request, superset_id):
        application = fiware_api.keystone.application_get(request, superset_id)
        return application.name


class UpdateApplicationRolesAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = ('Unable to retrieve data. Please try again later.')
    RELATIONSHIP_CLASS = RoleAndPermissionApi
    ERROR_URL = INDEX_URL

    def get_default_role_field_name(self):
        """ No use for this method, this workflow doesn't support the
        'adding from a pool of all resources' logic as the user one does.
        """
        #return "default_" + self.slug + "_role"
        return

    def get_member_field_name(self, permission_id):
        return self.slug + "_permission_" + permission_id

    class Meta:
        name = ("Manage your applications' roles")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateApplicationRoles(idm_workflows.UpdateRelationshipStep):
    action_class = UpdateApplicationRolesAction
    members_list_title = ("Application roles")
    RELATIONSHIP_CLASS = RoleAndPermissionApi
    template_name = "idm/myApplications/roles/_workflow_step_update_members.html"


class ManageApplicationRoles(idm_workflows.RelationshipWorkflow):
    slug = "manage_application_roles"
    name = ("Manage Roles")
    finalize_button_name = ("Finish")
    success_message = ('Modified roles and permissions.')
    failure_message = ('Unable to modify roles and permissions.')
    success_url = "horizon:idm:myApplications:detail"
    default_steps = (UpdateApplicationRoles,)
    RELATIONSHIP_CLASS = RoleAndPermissionApi
    member_slug = idm_workflows.RELATIONSHIP_SLUG

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return urlresolvers.reverse(self.success_url,
                    kwargs={'application_id':self.context['superset_id']})

    def handle(self, request, data):
        success = super(ManageApplicationRoles, self).handle(request, data)
        app_id = data['superset_id']
        application = fiware_api.keystone.application_get(request, app_id)
        try:
            role_permissions = {}
            public_roles = [
                role for role in fiware_api.keystone.role_list(
                    request, application=app_id)
                if role.is_internal == False
            ]

            for role in public_roles:
                public_permissions = [
                    perm for perm in fiware_api.keystone.permission_list(
                        request, role=role.id)
                    if perm.is_internal == False
                ]
                if public_permissions:
                    role_permissions[role.id] = public_permissions

            fiware_api.access_control_ge.policyset_update(
                request,
                application=application, 
                role_permissions=role_permissions)

        except Exception:
            exceptions.handle(
                request,
                'Failed to update policies in Access Control GE')

        return success



# APPLICATION MEMBERS
class AuthorizedUsersApi(idm_workflows.RelationshipApiInterface):
    """FIWARE roles and user logic"""

    def _list_all_owners(self, request, superset_id):
        all_users = fiware_api.keystone.user_list(request, filters={'enabled':True})
        return [
            (user.id, idm_utils.get_avatar(user, 'img_small', 
                idm_utils.DEFAULT_USER_SMALL_AVATAR) + '$' + user.username) 
            for user in all_users if getattr(user, 'username', None)]

    def _list_all_objects(self, request, superset_id):
        # TODO(garcianavalon) move to fiware_api
        all_roles = fiware_api.keystone.role_list(request)
        if request.user.default_project_id == request.organization.id:
            allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
                request,
                user=request.user.id,
                organization=request.user.default_project_id)
        else:
            allowed = fiware_api.keystone.list_organization_allowed_roles_to_assign(
                request,
                organization=request.organization.id)
        self.allowed = [role for role in all_roles
                   if role.id in allowed[superset_id]]
        return self.allowed


    def _list_current_assignments(self, request, superset_id):
        # NOTE(garcianavalon) logic for this part:
        # load all the user-scoped application roles for every user
        # but only the ones the user can assign
        application_users_roles = {}
        allowed_ids = [r.id for r in self.allowed]
        role_assignments = [a for a in fiware_api.keystone.user_role_assignments(
                                request, application=superset_id)
                            if a.role_id in allowed_ids]

        all_users = fiware_api.keystone.user_list(request, filters={'enabled':True})

        for assignment in role_assignments:
            user = next((user for user in all_users
                         if user.id == assignment.user_id
                         and user.default_project_id == assignment.organization_id),
                        None)
            if not user:
                continue

            if not user.id in application_users_roles:
                application_users_roles[user.id] = []

            application_users_roles[user.id].append(assignment.role_id)

        return application_users_roles


    def _get_default_object(self, request):
        return None


    def _add_object_to_owner(self, request, superset, owner, obj):
        default_org = fiware_api.keystone.user_get(request, owner).default_project_id
        fiware_api.keystone.add_role_to_user(request,
                                             application=superset,
                                             user=owner,
                                             organization=default_org,
                                             role=obj)


    def _remove_object_from_owner(self, request, superset, owner, obj):
        default_org = fiware_api.keystone.user_get(request, owner).default_project_id
        fiware_api.keystone.remove_role_from_user(request,
                                                  application=superset,
                                                  user=owner,
                                                  organization=default_org,
                                                  role=obj)


    def _get_supersetid_name(self, request, superset_id):
        application = fiware_api.keystone.application_get(request, superset_id)
        return application.name


class UpdateAuthorizedUsersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = ('Unable to retrieve data. Please try again later.')
    RELATIONSHIP_CLASS = AuthorizedUsersApi
    ERROR_URL = INDEX_URL

    class Meta:
        name = ("Manage authorized users")
        slug = idm_workflows.RELATIONSHIP_SLUG + '_users'


class UpdateAuthorizedUsers(idm_workflows.UpdateRelationshipStep):
    action_class = UpdateAuthorizedUsersAction
    available_list_title = ("All users")
    members_list_title = ("Authorized Users")
    no_available_text = ("No users found.")
    no_members_text = ("No users.")
    RELATIONSHIP_CLASS = AuthorizedUsersApi
    server_filter_url = urlresolvers.reverse_lazy(
        'fiware_complex_server_filters_users')


class ManageAuthorizedUsers(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_users_application_roles"
    name = ("Authorize users in your application")
    finalize_button_name = ("Save")
    success_message = ('Modified users.')
    failure_message = ('Unable to modify users.')
    success_url = "horizon:idm:myApplications:detail"
    default_steps = (UpdateAuthorizedUsers,)
    RELATIONSHIP_CLASS = AuthorizedUsersApi
    member_slug = idm_workflows.RELATIONSHIP_SLUG + '_users'

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return urlresolvers.reverse(self.success_url,
                    kwargs={'application_id':self.context['superset_id']})


# APPLICATION ORGANIZATIONS
class AuthorizedOrganizationsApi(idm_workflows.RelationshipApiInterface):
    """FIWARE roles and organization logic"""

    def _list_all_owners(self, request, superset_id):
        all_organizations = fiware_api.keystone.project_list(request)
        return [
            (org.id, idm_utils.get_avatar(org, 'img_small', 
                idm_utils.DEFAULT_ORG_SMALL_AVATAR) + '$' + org.name) 
            for org in idm_utils.filter_default(all_organizations)]


    def _list_all_objects(self, request, superset_id):
        all_roles = fiware_api.keystone.role_list(request)
        if request.user.default_project_id == request.organization.id:
            allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
                request,
                user=request.user.id,
                organization=request.user.default_project_id)
        else:
            allowed = fiware_api.keystone.list_organization_allowed_roles_to_assign(
                request,
                organization=request.organization.id)
        self.allowed = [role for role in all_roles
                   if role.id in allowed[superset_id]]
        return self.allowed


    def _list_current_assignments(self, request, superset_id):
        # NOTE(garcianavalon) logic for this part:
        # load all the organization-scoped application roles for every
        # organization but only the ones the user can assign
        application_organizations_roles = {}
        allowed_ids = [r.id for r in self.allowed]
        role_assignments = fiware_api.keystone.organization_role_assignments(
            request, application=superset_id)
        organizations = set([a.organization_id for a in role_assignments])
        for organization_id in organizations:
            application_organizations_roles[organization_id] = [
                a.role_id for a in role_assignments
                if a.organization_id == organization_id
                and a.role_id in allowed_ids
            ]
        return application_organizations_roles


    def _get_default_object(self, request):
        return None


    def _add_object_to_owner(self, request, superset, owner, obj):
        fiware_api.keystone.add_role_to_organization(
            request,
            application=superset,
            organization=owner,
            role=obj)


    def _remove_object_from_owner(self, request, superset, owner, obj):
        fiware_api.keystone.remove_role_from_organization(
            request,
            application=superset,
            organization=owner,
            role=obj)


    def _get_supersetid_name(self, request, superset_id):
        application = fiware_api.keystone.application_get(request, superset_id)
        return application.name


class UpdateAuthorizedOrganizationsAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = ('Unable to retrieve data. Please try again later.')
    RELATIONSHIP_CLASS = AuthorizedOrganizationsApi
    ERROR_URL = INDEX_URL

    class Meta:
        name = ("Manage authorized organizations")
        slug = idm_workflows.RELATIONSHIP_SLUG + '_organizations'


class UpdateAuthorizedOrganizations(idm_workflows.UpdateRelationshipStep):
    action_class = UpdateAuthorizedOrganizationsAction
    available_list_title = ("All Organizations")
    members_list_title = ("Authorized Organizations")
    no_available_text = ("No organizations found.")
    no_members_text = ("No organizations.")
    RELATIONSHIP_CLASS = AuthorizedOrganizationsApi
    server_filter_url = urlresolvers.reverse_lazy(
        'fiware_complex_server_filters_organizations')


class ManageAuthorizedOrganizations(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_organizations_application_roles"
    name = ("Authorize organizations in your application")
    finalize_button_name = ("Save")
    success_message = ('Modified organizations.')
    failure_message = ('Unable to modify organizations.')
    success_url = "horizon:idm:myApplications:detail"
    default_steps = (UpdateAuthorizedOrganizations,)
    RELATIONSHIP_CLASS = AuthorizedOrganizationsApi
    member_slug = idm_workflows.RELATIONSHIP_SLUG + '_organizations'
    no_roles_message = 'Some organizations don\'t have any role assigned. \
        If you save now they won\'t be authorized in the application'

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return urlresolvers.reverse(self.success_url,
                    kwargs={'application_id':self.context['superset_id']})
