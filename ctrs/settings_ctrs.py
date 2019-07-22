# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# PROJECT settings
# PLEASE DO NOT PLACE ANY SENSITIVE DATA HERE (password, keys, personal
# data, etc.)
# Use local_settings.py for that purpose
from .customisations.digipal.views.faceted_search.settings import FacettedType

# Lightbox
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
MODELS_PRIVATE = ['textcontentxml', 'itempart', 'text']
MODELS_PUBLIC = MODELS_PRIVATE

DEBUG_PERFORMANCE = False
COMPRESS_ENABLED = True
# COMPRESS_ENABLED = True

# CUSTOM_APPS = ['exon.customisations.mapping']

TEXT_IMAGE_MASTER_CONTENT_TYPE = 'transcription'
KDL_MAINTAINED = True

TEXT_EDITOR_OPTIONS_CUSTOM = {
    'buttons': {
        'btnHeading': {'label': 'Heading', 'tei': '<head>{}</head>', 'color': '#efffb0'},
        'btnHeadingEmphasised': {'label': 'Heading (rubricated)', 'tei': '<head rend="emphasised">{}</head>'},
        'btnChapterNumber': {'label': 'Chapter Number', 'tei': '<cn>{}</cn>', 'color': '#ffe7bc'},
        'btnSentenceNumber': {'label': 'Sentence Number', 'tei': '<sn>{}</sn>', 'color': '#ffe7bc'},
        'btnPageNumber': {'label': 'Locus', 'tei': '<location loctype="locus">{}</location>', 'color': '#ffe7bc'},
        'btnStructure': {'label': 'Structure', 'buttons': [
            'btnHeading', 'btnHeadingEmphasised', 'btnChapterNumber', 'btnSentenceNumber', 'btnPageNumber'
        ]},

        'btnUnsettled': {'label': 'V-Unsettled (shared)', 'tei': '<seg type="unsettled">{}</seg>'},
        'btnUnsettledUnique': {'label': 'V-Unsettled (unique)', 'tei': '<seg type="unsettled" subtype="unique">{}</seg>'},
        'btnWUnsettled': {'label': 'W-Unsettled (shared)', 'tei': '<seg type="unsettled" group="work">{}</seg>'},
        'btnGenetic': {'label': 'Dynamics', 'buttons': [
            'btnUnsettled', 'btnUnsettledUnique', 'btnWUnsettled'
        ]},

        'btnAddedAbove': {'label': 'Added (above)', 'tei': '<add place="above">{}</add>'},
        'btnAddedInline': {'label': 'Added (inline)', 'tei': '<add place="inline">{}</add>'},
        'btnDeletedStruck': {'label': 'Deleted (struck)', 'tei': '<del rend="strikethrough">{}</del>', 'plain': 1},
        'btnDeletedErased': {'label': 'Deleted (erased)', 'tei': '<del rend="erased">{}</del>'},
        'btnDeletedUnderpointed': {'label': 'Deleted (underpointed)', 'tei': '<del rend="underpointed">{}</del>'},
        'btnRedInk': {'label': 'Red Ink', 'tei': '<hi rend="color(ret)">{}</hi>', 'color': '#ffc9c9'},
        'btnHighlighted': {'label': 'Highlighted', 'tei': '<hi rend="highlight">{}</hi>'},
        'btnSuperscripted': {'label': 'Superscripted', 'tei': '<hi rend="sup">{}</hi>', 'plain': 1},
        'btnScribal': {'label': 'Scribal Intervention', 'buttons': [
            'btnAddedAbove', 'btnAddedInline',
            'btnDeletedStruck', 'btnDeletedErased', 'btnDeletedUnderpointed',
            'btnRedInk', 'btnHighlighted', 'btnSuperscripted'
        ]},

        'btnVernacular': {'label': 'Vernacular', 'tei': '<seg lang="vernacular">{}</seg>', 'plain': 1},
        'btnHandShift': {'label': 'New Hand', 'tei': '<newhand>{}</newhand>'},
        'btnOther': {'label': 'Other', 'buttons': [
            'btnVernacular', 'btnHandShift',
        ]},
    },
    'show_highlights_in_preview': 1,
    'toolbars': {
        'default': 'psclear undo redo pssave | psconvert | btnStructure btnGenetic btnScribal btnOther | code ',
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

CUSTOM_APPS = ['ctrs_text']

# FACETED SEARCH

texts = FacettedType.fromKey('texts')
version_field = {
    'key': 'version', 'label': 'Version',
    'path': 'text_content.text.name',
    'search': True, 'viewable': True, 'type': 'title',
    'count': True,
}
texts.addField(version_field.copy(), 'url')
filters = ['version', 'text_type']
for f in texts.getFields():
    if f['key'] not in filters:
        f['count'] = False
        f['filter'] = False


texts.options['column_order'] = [
    'url', 'version',  'repo_place', 'shelfmark', 'text_type'
]

texts.disableView('overview')

manuscripts = FacettedType.fromKey('manuscripts')
manuscripts.options['disabled'] = True

# Regiam / Declaration
text_work_field = {
    'key': 'text_work', 'label': 'Work',
    'path': 'get_work_label', 'type': 'title', 'search': True,
    'count': True
}

texts.addField(text_work_field.copy(), 'url')

# Regiam / Declaration
text_state = {
    'key': 'text_state', 'label': 'State',
    'path': 'get_state', 'type': 'title', 'search': False,
    'count': True, 'viewable': True,
}

texts.addField(text_state.copy())
texts.getOption('column_order').append('text_state')
