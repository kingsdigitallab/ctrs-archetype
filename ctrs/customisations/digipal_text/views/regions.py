# -*- coding: utf-8 -*-
from django.shortcuts import render
from digipal.models import Text, ItemPart
from digipal_text.models import TextContentXML, TextContentType
from digipal import utils as dputils


def set_context_types_from_request(request, context):
    atypes = TextContentType.objects.all().order_by('id')

    default_type = atypes[0].slug
    atype = request.GET.get('type', default_type)
    other_type = atypes[1].slug
    if atype == other_type:
        other_type = default_type
    context['other_type'] = other_type
    context['this_type'] = atype

    return atype


def view_regions_detect(request):

    print('-' * 40)

    context = {}

    atype = set_context_types_from_request(request, context)

    msids = [27, 39]
    for i in range(len(msids)):
        msid = request.GET.get('msid-{}'.format(i))
        if msid:
            msids[i] = int(msid)

    tcxs = {
        tcx.text_content.item_part_id: {
            'record': tcx
        }
        for tcx
        in
        TextContentXML.objects.filter(
            text_content__item_part__id__in=msids,
            text_content__type__slug=atype
        )
    }

    context['msids'] = msids

    context['ips'] = ItemPart.objects.all()

    cs = [
        dputils.get_plain_text_from_html(tcxs[msid]['record'].content) + ' EOT'
        for msid
        in msids
    ]

    import re
    cs = [
        re.findall(r'\w+', c)
        for c in cs
    ]

    ps = [0, 0]
    markedup = []

    stop_words = ['et', 'de', 'a', 'ac', 'in', 'pro', 'quem', 'aut']

    while True:
        ls = [0, 0]
        w = None
        d = 0
        while True:
            moved = 0
            if (ps[0] + ls[0]) < len(cs[0]):
                ls[0] += 1
                moved = 1
            if (ps[1] + ls[1]) < len(cs[1]):
                ls[1] += 1
                moved = 1

            if not moved:
                break

            frags = [c[ps[i]:ps[i] + ls[i]] for i, c in enumerate(cs)]
            # fragsn = [c[ps[i]:ps[i] + ls[i]] for i, c in enumerate(cs)]
            inter = set(frags[0]).intersection(frags[1])
            if sum(ls) > 2:
                inter = inter.difference(stop_words)

            if inter:
                w = list(inter)[0]
                ds = [frags[0].index(w), frags[1].index(w)]
                skippeds = [frags[0][:ds[0]], frags[1][:ds[1]]]

                # move stop word away from end of the skipped area
                while all(skippeds) and skippeds[0][-1] == skippeds[1][-1]:
                    w0 = skippeds[0].pop()
                    skippeds[1].pop()
                    w = w0 + ' ' + w

                ps[0] += ds[0] + 1
                ps[1] += ds[1] + 1
                break

        if w is None:
            break

        if any(skippeds):
            t = u'[{} | {}]'.format(
                ' '.join(skippeds[0]) or u'Ø',
                ' '.join(skippeds[1]) or u'Ø'
            )
            # print(t)
            markedup.append(u'<span class="unsettled">{}</span>'.format(t))
        if w:
            # print(w)
            markedup.append(w)

    context['show_numbers'] = 0
    context['markedup'] = ' '.join(markedup)
    context['markedup'] = re.sub(
        ur'(\d+)', r'<br><br>(\1)', context['markedup'])

    return render(request, 'digipal_text/regions_detect.html', context)


def view_regions_table(request, ip_group_id=None):
    context = {
        'wide_page': True,
    }

    ip_group = ItemPart.objects.filter(id=ip_group_id).first()
    context['ip_group'] = ip_group
    context['tcs'] = []
    slots_count = 0

    atype = set_context_types_from_request(request, context)

    # text content xmls
    tcxs = TextContentXML.objects.filter(
        text_content__item_part__group=ip_group, text_content__type__slug=atype
    ).order_by('text_content__item_part__display_label')
    ip_group_tcxs = TextContentXML.objects.filter(
        text_content__item_part=ip_group, text_content__type__slug=atype
    ).order_by('text_content__item_part__display_label')

    is_group_work = ip_group.type.name.lower() == 'work'

    pattern = './/span[@data-dpt-type="unsettled"]'

    for tcx in list(ip_group_tcxs) + list(tcxs):
        tcx.save_with_element_ids()
        content = tcx.content

        regions = []

        xml = dputils.get_xml_from_unicode(content, ishtml=True, add_root=True)

        for element in xml.findall(pattern):
            is_element_work = element.attrib.get(
                'data-dpt-group', '').lower() == 'work'
            if is_group_work != is_element_work:
                continue

            regions.append({
                'id': element.attrib['id'],
                'content': dputils.get_unicode_from_xml(element, text_only=True)
            })

        context['tcs'].append({
            'ip': tcx.text_content.item_part,
            'regions': regions
        })

    context['slots'] = range(
        max([len(tc['regions']) for tc in context['tcs']])
    )

    context['show_numbers'] = 0

    return render(request, 'digipal_text/regions_table.html', context)
