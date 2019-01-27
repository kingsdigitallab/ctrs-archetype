# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# PROJECT settings
# PLEASE DO NOT PLACE ANY SENSITIVE DATA HERE (password, keys, personal
# data, etc.)
# Use local_settings.py for that purpose

# Lightbox
"""
The Lightbox is a separate project, even though it's still tightly linked to Digipal. It is possible to install it through pip:
>>> pip install git+https://github.com/Gbuomprisco/Digital-Lightbox.git
By default, it is disabled. You can enable it by setting the variable LIGHTBOX in your settings:
"""
LIGHTBOX = False

# Mezzanine
# SITE_TITLE = 'The community of the realm in Scotland'
SITE_TITLE = 'CoTR - Archetype'

# Social
"""
The following variables contains the URLs/username to social networking sites.
- The TWITTER variable asks for the Twitter username.
- The GITHUB variable asks for the relative URL to your Github project or account
- The COMMENTS_DISQUS_SHORTNAME asks for the Disqus shortname
"""
TWITTER = ''
GITHUB = ''
# COMMENTS_DISQUS_SHORTNAME = "exondomesday"

# Annotator Settings

"""
If True, this setting will reject every change to the DB. To be used in production websites.
"""
REJECT_HTTP_API_REQUESTS = False  # if True, prevents any change to the DB

"""
This setting allows to set the number of zoom levels available in the OpenLayers layer.
"""
ANNOTATOR_ZOOM_LEVELS = 7  # This setting sets the number of zoom levels of O

FOOTER_LOGO_LINE = True

# Customise the faceted search settings
MODELS_PRIVATE = ['textcontentxml', 'itempart', 'image']
MODELS_PUBLIC = MODELS_PRIVATE

DEBUG_PERFORMANCE = False
COMPRESS_ENABLED = True
# COMPRESS_ENABLED = True

# from customisations.digipal.views.faceted_search.settings import FACETED_SEARCH

# CUSTOM_APPS = ['exon.customisations.mapping']

TEXT_IMAGE_MASTER_CONTENT_TYPE = 'transcription'
KDL_MAINTAINED = True

TEXT_EDITOR_OPTIONS_CUSTOM = {
    'buttons': {
        'btnPersonName': {'label': 'Person name', 'tei': '<rs type="person" subtype="name">{}</rs>'},
        'btnPersonMaritalStatus': {'label': 'Marital status', 'tei': '<rs type="person" subtype="marital-status">{}</rs>'},
        'btnPerson': {'label': 'Person', 'buttons': ['btnPersonName', 'btnPersonMaritalStatus']},

        'btnPlaceName': {'label': 'Place name', 'tei': '<rs type="place" subtype="name">{}</rs>'},
        'btnBirthPlace': {'label': 'Birth place', 'tei': '<rs type="place" subtype="birthplace">{}</rs>'},
        'btnResidence': {'label': 'Residence', 'tei': '<rs type="place" subtype="residence">{}</rs>'},
        'btnPlace': {'label': 'Place', 'buttons': ['btnPlaceName', 'btnBirthPlace', 'btnResidence']},

        'btnDate': {'label': 'Date', 'tei': '<rs type="date">{}</rs>'},
        'btnOccupation': {'label': 'Occupation', 'tei': '<rs type="occupation">{}</rs>'},

        'btnReligion': {'label': 'Religion', 'tei': '<rs type="religion">{}</rs>'},
        'btnReligiousStatus': {'label': 'Religious status', 'tei': '<rs type="religious-status">{}</rs>'},

        'btnJuridicalStatus': {'label': 'Juridical status', 'tei': '<rs type="juridical-status">{}</rs>'},
        'btnInfrastructure': {'label': 'Infrastructure', 'tei': '<rs type="infrastructure">{}</rs>'},
        'btnBuilding': {'label': 'Building', 'tei': '<rs type="building">{}</rs>'},
        'btnLand': {'label': 'Land', 'tei': '<rs type="land">{}</rs>'},
        'btnEconomicData': {'label': 'Economic Data', 'tei': '<rs type="economic-data">{}</rs>'},

        'btnFurniture': {'label': 'Furniture', 'tei': '<rs type="item" subtype="furniture">{}</rs>'},
        'btnClothing': {'label': 'Clothing', 'tei': '<rs type="item" subtype="clothing">{}</rs>'},
        'btnFood': {'label': 'Food', 'tei': '<rs type="item" subtype="food">{}</rs>'},
        'btnTool': {'label': 'Tool', 'tei': '<rs type="item" subtype="tool">{}</rs>'},
        'btnWritingMaterial': {'label': 'Writing material', 'tei': '<rs type="item" subtype="writing-material">{}</rs>'},
        'btnItem': {'label': 'Item', 'buttons': ['btnFurniture', 'btnClothing', 'btnFood', 'btnTool', 'btnWritingMaterial']},
    },
    'show_highlights_in_preview': 1,
    'toolbars': {
        'default': 'psclear undo redo pssave | btnPerson btnPlace btnDate btnOccupation btnReligion btnReligiousStatus | btnJuridicalStatus btnInfrastructure btnBuilding btnLand btnEconomicData btnItem | code ',
    },
    'panels': {
        'north': {
            'ratio': 0.0
        },
        'east': {
            'ratio': 0.0
        },
    }
}
