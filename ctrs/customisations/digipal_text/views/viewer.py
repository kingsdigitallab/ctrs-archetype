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
