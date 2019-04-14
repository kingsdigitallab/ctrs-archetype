from digipal.views.faceted_search.settings import FACETED_SEARCH, remove_fields_from_faceted_search, get_content_type_from_key, FacettedType

# place Texts first
FACETED_SEARCH['types'] = [
    FACETED_SEARCH['type_keys']['texts'],
    FACETED_SEARCH['type_keys']['manuscripts'],
]

# disable the list view, snippet is what we allways want
texts = FacettedType.fromKey('texts')
texts.disableView('list')
