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

import os
import logging

from django import shortcuts
from django.conf import settings
from django import forms 
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import forms as idm_forms


LOG = logging.getLogger('idm_logger')
AVATAR_SMALL = settings.MEDIA_ROOT+"/"+"OrganizationAvatar/small/"
AVATAR_MEDIUM = settings.MEDIA_ROOT+"/"+"OrganizationAvatar/medium/"
AVATAR_ORIGINAL = settings.MEDIA_ROOT+"/"+"OrganizationAvatar/original/"

GENERIC_ERROR_MESSAGE = 'An error ocurred. Please try again later.'

class RemoveOrgForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    title = 'Remove from Organization'

    def handle(self, request, data):
        user = request.user.id
        project = data['orgID']
        member_role = fiware_api.keystone.get_member_role(request)
        api.keystone.remove_tenant_user_role(request, project=project,
                                             user=user, role=member_role)
        messages.success(request, ("You removed yourself from the organization successfully."))
        response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
        return response


class CreateOrganizationForm(forms.SelfHandlingForm):
    name = forms.CharField(label=("Name"), max_length=64, required=True)
    description = forms.CharField(
        label=("Description"), 
        widget=forms.widgets.Textarea(attrs={'rows':4, 'cols':40}),
        required=True)

    def clean_name(self):
        """ Validate that the name is not already in use."""
        org_name = self.cleaned_data['name']
        try:
            all_organizations = fiware_api.keystone.project_list(self.request)
            names_in_use = [org.name for org 
                             in all_organizations]
            if org_name in names_in_use:
                raise forms.ValidationError(
                    ("An organization with that name already exists."),
                    code='invalid')
            return org_name
        except Exception:
            exceptions.handle(self.request, 
                              GENERIC_ERROR_MESSAGE, 
                              ignore=True)

    def handle(self, request, data):
        # Create organization
        default_domain = api.keystone.get_default_domain(request)
        try:
            self.object = fiware_api.keystone.project_create(
                request,
                name=data['name'],
                description=data['description'],
                enabled=True,
                domain=default_domain,
                website='')
                                                     
        except Exception:
            exceptions.handle(request, 
                              GENERIC_ERROR_MESSAGE, 
                              ignore=True)
            return False

        # Set organization and user id
        organization_id = self.object.id
        user_id = request.user.id

        LOG.debug('Organization %s created', organization_id)

        # Grant purchaser in all default apps
        default_apps = fiware_api.keystone.get_fiware_default_apps(
            self.request)
        purchaser_role = fiware_api.keystone.get_purchaser_role(
            self.request)
        try:
            for app in default_apps:
                fiware_api.keystone.add_role_to_organization(
                    self.request, 
                    purchaser_role.id, 
                    organization_id, 
                    app.id,
                    use_idm_account=True)
                LOG.debug('Granted role %s in app %s', purchaser_role.name, app.name)
        except Exception as e:
            exceptions.handle(self.request,
                redirect=reverse('horizon:idm:organizations:index'))
            return False

        # Find owner role id
        try:
            owner_role = fiware_api.keystone.get_owner_role(self.request)
            if owner_role is None:
                msg = ('Could not find owner role in Keystone')
                LOG.debug(msg)
                raise exceptions.NotFound(msg)
        except Exception as e:
            exceptions.handle(self.request,
                redirect=reverse('horizon:idm:organizations:index'))
            return False
        try:
            api.keystone.add_tenant_user_role(request,
                                              project=organization_id,
                                              user=user_id,
                                              role=owner_role.id)
            LOG.debug('Added user %s and organization %s to role %s', 
                user_id, organization_id, owner_role.id)
        except Exception:
            exceptions.handle(
                request,
                ('Failed to add {0} organization to list').format(
                    data['name']))
            return False
    
        response = shortcuts.redirect('switch_tenants', organization_id)
        return response


class InfoForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    name = forms.CharField(label=("Name"), max_length=64, required=True)
    description = forms.CharField(
        label=("Description"), 
        widget=forms.widgets.Textarea(attrs={'rows':4, 'cols':40}), 
        required=True)
    website = forms.URLField(label=("Website"), required=False)
    title = 'Information'

    def handle(self, request, data):
        try:
            fiware_api.keystone.project_update(
                request, 
                data['orgID'], 
                name=data['name'], 
                description=data['description'],
                website=data['website'])
            
            LOG.debug('Organization %s updated', data['orgID'])
            messages.success(request, 
                ("Organization updated successfully."))
        except Exception:
            messages.error(request, 
                ("An error occurred, try again later."))

        return shortcuts.redirect(
            'horizon:idm:organizations:detail', data['orgID'])


class AvatarForm(forms.SelfHandlingForm, idm_forms.ImageCropMixin):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    image = forms.ImageField(required=False)
    title = 'Avatar Update'

    def handle(self, request, data):
        if request.FILES:
            image = request.FILES['image'] 
            output_img = self.crop(image)
            
            small = 25, 25, 'small'
            medium = 36, 36, 'medium'
            original = 100, 100, 'original'
            meta = [original, medium, small]
            for meta in meta:
                size = meta[0], meta[1]
                img_type = meta[2]
                output_img.thumbnail(size)
                img = 'OrganizationAvatar/' + img_type + "/" + self.data['orgID']
                output_img.save(settings.MEDIA_ROOT + "/" + img, 'JPEG')
        
                if img_type == 'small':
                    fiware_api.keystone.project_update(request, data['orgID'], img_small=img)
                elif img_type == 'medium':
                    fiware_api.keystone.project_update(request, data['orgID'], img_medium=img)
                else:
                    fiware_api.keystone.project_update(request, data['orgID'], img_original=img)

            LOG.debug('Organization {0} image updated'.format(data['orgID']))
            messages.success(request, ("Organization updated successfully."))

        response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
        return response

             
class CancelForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    title = 'Cancel'
    
    def handle(self, request, data, organization):
        if getattr(organization, 'is_cloud_project', False):
            messages.error(request, ("Your cloud organization can't be deleted."))
            response = shortcuts.redirect('horizon:idm:organizations:index')
            return response

        image = getattr(organization, 'img_original', '')
        if "OrganizationAvatar" in image:
            os.remove(AVATAR_SMALL + organization.id)
            os.remove(AVATAR_MEDIUM + organization.id)
            os.remove(AVATAR_ORIGINAL + organization.id)
            LOG.debug('%s deleted', image)

        fiware_api.keystone.project_delete(request, organization)
        LOG.info('Organization %s deleted', organization.id)

        messages.success(request, ("Organization deleted successfully."))
        response = shortcuts.redirect('horizon:idm:organizations:index')
        return response


