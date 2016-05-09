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
import math

from horizon import exceptions

from django.conf import settings
from django.core import urlresolvers

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.local import local_settings


LOG = logging.getLogger('idm_logger')

DEFAULT_ORG_MEDIUM_AVATAR = 'dashboard/img/logos/medium/group.png'
DEFAULT_APP_MEDIUM_AVATAR = 'dashboard/img/logos/medium/app.png'
DEFAULT_USER_MEDIUM_AVATAR = 'dashboard/img/logos/medium/user.png'

DEFAULT_ORG_SMALL_AVATAR = 'dashboard/img/logos/small/group.png'
DEFAULT_APP_SMALL_AVATAR = 'dashboard/img/logos/small/app.png'
DEFAULT_USER_SMALL_AVATAR = 'dashboard/img/logos/small/user.png'


def filter_default(items):
    """Remove from a list the automated created project for a user. This project
    is created during the user registration step and is needed for the user to be
    able to perform operations in the cloud, as a work around the Keystone-OpenStack
    project behaviour. We don't want the user to be able to do any operations to this 
    project nor even notice it exists.

    Also filters other default items we dont want to show, like internal
    applications.
    """
    filtered = [i for i in items if not getattr(i, 'is_default', False)]
    return filtered


def check_elements(elements, valid_elements):
    """Checks a list of elements are present in an allowed elements list"""
    invalid_elements = [k for k in elements if k not in valid_elements]
    if invalid_elements:
        raise TypeError('The elements {0} are not defined \
            in {1}'.format(invalid_elements, valid_elements))


def swap_dict(old_dict):
    """Returns a new dictionary in wich the keys are all the values of the old
    dictionary and the values are lists of keys that had that value.
    
    Example: 
    d = { 'a':['c','v','b'], 's':['c','v','d']} 
    swap_dict(d) -> {'c': ['a', 's'], 'b': ['a'], 'd': ['s'], 'v': ['a', 's']}
    """
    new_dict = {}
    for key in old_dict:
        for value in old_dict[key]:
            new_dict[value] = new_dict.get(value, [])
            new_dict[value].append(key)
    return new_dict


def get_avatar(obj, avatar_type, default_avatar):
    """Gets the object avatar or a default one."""
    if type(obj) == dict:
        avatar = obj.get(avatar_type, None)
    else:
        avatar = getattr(obj, avatar_type, None)
    if avatar:
        return settings.MEDIA_URL + avatar
    else:
        return settings.STATIC_URL + default_avatar


def get_switch_url(organization, check_switchable=True):
    if check_switchable and not getattr(organization, 'switchable', False):
        return False

    if type(organization) == dict:
        organization_id = organization['id']
    else:
        organization_id = organization.id
        
    return urlresolvers.reverse('switch_tenants',
                                kwargs={'tenant_id': organization_id})


def page_numbers(elements, page_size):
    return range(1, int(math.ceil(float(len(elements))/page_size)) + 1)


def total_pages(elements, page_size):
    if not elements:
        return 0
    return page_numbers(elements, page_size)[-1]


def paginate_list(elements, page_number, page_size):
    index = (page_number - 1) * page_size
    return elements[index:index + page_size]


class PickleObject():
    """Extremely simple class that holds the very little information we need
    to cache. Keystoneclient resource objects are not pickable.
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


def obj_to_jsonable_dict(obj, attrs):
    """converts a object into a json-serializable dict, geting the
    specified attributes.
    """
    as_dict = {}
    for attr in attrs:
        if hasattr(obj, attr):
            as_dict[attr] = getattr(obj, attr)
    return as_dict
