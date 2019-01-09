from django.conf import settings
from django.conf.urls import patterns, include, url
from mezzanine.core.views import direct_to_template
from django.contrib import admin
# from customisations.digipal_text import models
# from customisations.digipal_text.views import viewer
# from exon.customisations.mapping import models

admin.autodiscover()

# ADD YOUR OWN URLPATTERNS *ABOVE* THE LINE BELOW.
# DigiPal URLs
urlpatterns = None

# dppatterns = patterns(
#     'exon.customisations.digipal_lab.views',
#     url(r'^lab/hundreds/$', 'hundreds.view_hundreds'),
#     url(r'^lab/hands/$', 'hands.view_hands'),
#     url(r'^lab/codicology/$', 'codicology.view_table'),
#     url(r'^lab/wordlist/$', 'words.view_list'),
#     url(r'^lab/viscoll/$', 'viscoll.view_viscoll'),
#     url(r'^lab/collationdiagrams/$', 'collation_diagrams.view_collation_diagrams'),
# )

# dppatterns += patterns('exon.customisations.mapping',
#                        url(r'^lab/map/$', 'views.view_map'))

# dppatterns += patterns('', ('^', include('digipal.urls')))

dppatterns = patterns('', ('^', include('digipal.urls')))

if urlpatterns:
    urlpatterns += dppatterns
else:
    urlpatterns = dppatterns

# Adds ``STATIC_URL`` to the context.
handler500 = 'mezzanine.core.views.server_error'
handler404 = 'mezzanine.core.views.page_not_found'
