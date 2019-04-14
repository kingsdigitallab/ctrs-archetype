from django.shortcuts import render
from digipal.models import Text
from digipal_text.models import TextContentXML
from digipal import utils as dputils


def view_versions(request, aid=None):
    context = {
        'wide_page': True,
    }

    text = Text.objects.filter(id=aid).first()
    context['text'] = text
    context['tcs'] = []
    slots_count = 0

    for tcx in TextContentXML.objects.filter(text_content__text=text):
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

    print(context)

    return render(request, 'digipal_text/version.html', context)
