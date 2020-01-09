from django.conf import settings
from django.conf.urls import patterns, include, url
from mezzanine.core.views import direct_to_template
from django.contrib import admin
from customisations.digipal_text import models
from customisations.digipal_text import admin as dpcadmin
from customisations.digipal_text.views import viewer
from ctrs.customisations.digipal_text.views import regions as views_ctrs_regions

# from exon.customisations.mapping import models

admin.autodiscover()

# ADD YOUR OWN URLPATTERNS *ABOVE* THE LINE BELOW.
# DigiPal URLs
urlpatterns = None

dppatterns = patterns(
    '',
    url(
        r'^digipal/manuscripts/(?P<parent_ip_id>[^/]+)/regions/?$',
        views_ctrs_regions.view_regions_table,
        name='regions_table'
    ),
    url(
        r'^ctrs/regions/detect/?$',
        views_ctrs_regions.view_regions_detect,
        name='regions_detect'
    ),
    url(
        r'^ctrs/regions/tree/?$',
        views_ctrs_regions.view_regions_tree,
        name='regions_tree'
    )
)

# dppatterns += patterns('', ('^', include('digipal.urls')))

dppatterns += patterns('', ('^', include('digipal.urls')))

# dppatterns += [r'^', include('digipal.urls')]

if urlpatterns:
    urlpatterns += dppatterns
else:
    urlpatterns = dppatterns

# Adds ``STATIC_URL`` to the context.
handler500 = 'mezzanine.core.views.server_error'
handler404 = 'mezzanine.core.views.page_not_found'
