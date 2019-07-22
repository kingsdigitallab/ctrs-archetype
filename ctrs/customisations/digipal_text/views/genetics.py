from django.shortcuts import render
from digipal.models import Text, ItemPart
from digipal_text.models import TextContentXML, TextContentType
from digipal import utils as dputils


def view_versions(request, ip_group_id=None):
    context = {
        'wide_page': True,
    }

    ip_group = ItemPart.objects.filter(id=ip_group_id).first()
    context['ip_group'] = ip_group
    context['tcs'] = []
    slots_count = 0

    atypes = TextContentType.objects.all().order_by('id')

    default_type = atypes[0].slug
    atype = request.GET.get('type', default_type)
    other_type = atypes[1].slug
    if atype == other_type:
        other_type = default_type
    context['other_type'] = other_type
    context['this_type'] = atype

    # text content xmls
    tcxs = TextContentXML.objects.filter(
        text_content__item_part__group=ip_group, text_content__type__slug=atype
    ).order_by('text_content__item_part__display_label')
    ip_group_tcxs = TextContentXML.objects.filter(
        text_content__item_part=ip_group, text_content__type__slug=atype
    ).order_by('text_content__item_part__display_label')
    for tcx in list(ip_group_tcxs) + list(tcxs):
        tcx.save_with_element_ids()
        content = tcx.content

        regions = []

        xml = dputils.get_xml_from_unicode(content, ishtml=True, add_root=True)

        for element in xml.findall('.//span[@data-dpt-type="unsettled"]'):
            regions.append({
                'id': element.attrib['id'],
                'content': dputils.get_unicode_from_xml(element, text_only=True)
            })

        context['tcs'].append({
            'ip': tcx.text_content.item_part,
            'regions': regions
        })

    context['slots'] = range(
        1, 1 + max([len(tc['regions']) for tc in context['tcs']])
    )

    context['show_numbers'] = 0

    return render(request, 'digipal_text/version.html', context)
