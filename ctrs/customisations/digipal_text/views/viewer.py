# -*- coding: utf-8 -*-
#from digipal_text.models import *
from digipal_text.models import TextContentXMLStatus, TextContent, TextContentXML
import re
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import transaction
from digipal import utils

# OVERRIDED FUNCTIONS

from digipal_text.views import viewer
from django.http import HttpRequest
from collections import OrderedDict

if 0:

    base_get_all_master_locations = viewer.get_all_master_locations

    def viewer_get_all_master_locations(context):
        res = base_get_all_master_locations(context)

        # let's add 'whole' as the first option
        ret = OrderedDict()
        if 0:
            # last option
            ret = res

        ret['whole'] = ['whole']
        for k, v in res.items():
            ret[k] = v

        return ret

    viewer.get_all_master_locations = viewer_get_all_master_locations

if 1:
    '''
    Copied from MOA / MOFA project customisation
    '''
    text_api_view_text_base = viewer.text_api_view_text

    def text_api_view_text(request, item_partid, content_type, location_type, location, content_type_record, user=None, max_size=None):

        # default operation
        ret = text_api_view_text_base(request, item_partid, content_type, location_type,
                                      location, content_type_record, user=user, max_size=max_size)

        # asking for face and no face defined => return whole text
        # that way the text can be synce with master location or image: locus/face
        # Note: this works for both reading and writing
        # TODO: use error code instead on relying on error message
        if ret.get('status', '') == 'error' and\
            'location not found' in ret.get('message', '') and\
                location and location.lower() == 'face':
            location_type = 'whole'
            location = ''
            # let's try again
            ret = text_api_view_text(request, item_partid, content_type, location_type,
                                     location, content_type_record, user=user, max_size=max_size)

            # Let's return locus/face. Why?
            # e.g. click on a clause in the transcription -> reverse sync to master
            # location -> sync to translation -> translation reload because it's
            # real location would be 'whole' and it receives locus/face from ML
            if not ret.get('status', '') == 'error' and ret.get('location_type', '') == 'whole':
                ret['location_type'] = 'locus'
                ret['location'] = 'face'

        return ret

    if text_api_view_text_base != text_api_view_text:
        viewer.text_api_view_text = text_api_view_text

    # --

    resolve_default_location_base = viewer.resolve_default_location

    # rules:
    #     if no specific location (e.g. face or dorse)
    #        then we pretend there is a (locus, face)
    #
    # Without this there will be bug with the sync of sublocation on load
    # because the server successfully responds whole instead of locus=face.

    def resolve_default_location(location_type, location, response):
        locations = response.get('locations', None)

        if locations:
            has_specific_location = False

            for lt, ls in response['locations'].iteritems():
                if ls:
                    has_specific_location = True
                    break

            if not has_specific_location:
                locations['locus'] = ['face']
                response['locations'] = OrderedDict(
                    sorted(locations.items(), key=lambda i: i[0]))

        ret = resolve_default_location_base(location_type, location, response)
        return ret

    if resolve_default_location_base != resolve_default_location:
        viewer.resolve_default_location = resolve_default_location

    #
    base_get_all_master_locations = viewer.get_all_master_locations

    def viewer_get_all_master_locations(context):
        res = base_get_all_master_locations(context)

        # let's add 'whole' as the first option
        ret = OrderedDict()

        ret['locus'] = ['face']
        # ret['whole'] = ['whole']

        return ret

    viewer.get_all_master_locations = viewer_get_all_master_locations


if 1:
    from digipal import utils as dputils

    def get_elementid_from_xml_element(element, idcount, as_string=False):
        ''' returns the elementid as a list
            e.g. [(u'', u'clause'), (u'type', u'disposition')]

            element: an xml element (etree)
            idcount: a dictionary, new for each enclosing text unit. Used to know
                which occurrence of an element we are seeing and generate a
                unique id. E.g. two same titles ('sheriff') marked up in the same
                way within the same entry => we need a count to differentiate
                them. We add [@o, 2] to second occurrence, etc.
        '''
        from django.utils.text import slugify

        element_text = utils.get_xml_element_text(element)

        # eg. parts: [(u'', u'clause'), (u'type', u'disposition')]
        parts = [
            (unicode(re.sub('data-dpt-?', '', k)), unicode(v))
            for k, v
            in element.attrib.iteritems()
            if k.startswith('data-dpt')
            # CTRS: patch 1
            and k not in ['data-dpt-cat', 'data-dpt-subtype']
        ]

        # white list to filter the elements
        # CTRS: patch 2
        if element.attrib.get('data-dpt-group', '') == 'work':
            element_text = slugify(u'%s' % element_text.lower())
            # CTRS: patch 3
            if len(element_text) > 0:
                text = unicode(element_text[:20])
            else:
                text = u'∅'
            parts.append([u'@text', text])
        else:
            parts = None

        if parts:
            order = dputils.inc_counter(idcount, repr(parts))
            if order > 1:
                # add (u'@o', u'2') if it is the 2nd occurrence of this
                # elementid
                parts.append((u'@o', u'%s' % order))

        return parts

    # monkey patch
    from digipal_text.views import viewer
    viewer.get_elementid_from_xml_element = get_elementid_from_xml_element
