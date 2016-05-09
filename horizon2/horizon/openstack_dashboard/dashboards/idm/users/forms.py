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

from horizon import forms
from horizon import messages

from openstack_dashboard import fiware_api
from openstack_dashboard import api
from openstack_dashboard.dashboards.idm import forms as idm_forms


LOG = logging.getLogger('idm_logger')

AVATAR_SMALL = settings.MEDIA_ROOT+"/"+"UserAvatar/small/"
AVATAR_MEDIUM = settings.MEDIA_ROOT+"/"+"UserAvatar/medium/"
AVATAR_ORIGINAL = settings.MEDIA_ROOT+"/"+"UserAvatar/original/"

class InfoForm(forms.SelfHandlingForm):
    userID = forms.CharField(label=("ID"), 
                             widget=forms.HiddenInput())
    username = forms.CharField(label=("Username"), 
                               max_length=64, 
                               required=True)
    description = forms.CharField(label=("About Me"),
                                  widget=forms.widgets.Textarea, 
                                  required=False)
    # city = forms.CharField(label=("City"), 
    #                        max_length=64, 
    #                        required=False)
    website = forms.URLField(label=("Website"), required=False)
    title = 'Personal Information'

    def handle(self, request, data):
        try:
            user = fiware_api.keystone.user_get(request, data['userID'])
            api.keystone.user_update(request,
                                     user.id,
                                     username=data['username'],
                                     website=data['website'],
                                     description=data['description'],
                                     # city=data['city'],
                                     password='')
            # NOTE(garcianavalon) No need for keeping this name updated
            # anymore
            # api.keystone.tenant_update(request,
            #                            user.default_project_id,
            #                            name=data['username'])
            LOG.debug('User {0} updated'.format(data['userID']))
            messages.success(request, ('User updated successfully'))
            
        except Exception:
            messages.error('An error ocurred, try again later')
                
        return shortcuts.redirect('horizon:idm:users:detail',
            data['userID'])


class AvatarForm(forms.SelfHandlingForm, idm_forms.ImageCropMixin):
    userID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    image = forms.ImageField(required=False)
    title = 'Change your avatar'

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
                img = 'UserAvatar/' + img_type + "/" + self.data['userID']
                output_img.save(settings.MEDIA_ROOT + "/" + img, 'JPEG')
                
                if img_type == 'small':
                    api.keystone.user_update(request, data['userID'], 
                        img_small=img, password='')
                elif img_type == 'medium':
                    api.keystone.user_update(request, data['userID'], 
                        img_medium=img, password='')
                else:
                    api.keystone.user_update(request, data['userID'], 
                        img_original=img, password='')

            LOG.debug('User {0} image updated'.format(data['userID']))
            messages.success(request, ("User updated successfully."))

        return shortcuts.redirect('horizon:idm:users:detail', 
            data['userID'])

             
class CancelForm(forms.SelfHandlingForm):
    userID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    title = 'Cancel Account'
    
    def handle(self, request, data, user):
        image = getattr(user, 'img_original', '')
        if "UserAvatar" in image:
            os.remove(AVATAR_SMALL + user.id)
            os.remove(AVATAR_MEDIUM + user.id)
            os.remove(AVATAR_ORIGINAL + user.id)
            LOG.debug('{0} deleted'.format(image))
        api.keystone.user_delete(request, user)
        LOG.info('User {0} deleted'.format(user.id))
        messages.success(request, ("User deleted successfully."))
        response = shortcuts.redirect('horizon:idm:users:detail')
        return response
