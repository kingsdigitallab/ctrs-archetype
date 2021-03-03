from django.contrib import admin
from digipal import admin as dpadmin
from digipal.models import ItemPart


class ItemPartAdmin(dpadmin.ItemPartAdmin):
    # 'current_item', 'locus',
    list_display = [
        'id', 'display_label', 'group_locus', 'type',
        'get_part_count', 'keywords_string',
    ]
    list_editable = ['group_locus']
    list_display_links = list(set(list_display) - set(list_editable))


admin.site.unregister(ItemPart)
admin.site.register(ItemPart, ItemPartAdmin)
