# -*- coding: utf-8 -*-
from django.shortcuts import render
from digipal.models import Text, ItemPart
from digipal_text.models import TextContentXML, TextContentType
from digipal import utils as dputils
import re
from django.utils.text import slugify
from digipal_text.views import viewer
import json

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


def view_regions_tree(request):
    context = {}

    atype = set_context_types_from_request(request, context)

    context['ips_available'] = ItemPart.objects.filter(
        type__name__iexact='version',
        group__display_label__iexact='declaration'
    )

    # ips selected by user
    context['ips'] = [
        ip
        for ip
        in context['ips_available']
        if request.GET.get('ip-{}'.format(ip.pk), '')
    ]
    if not context['ips']:
        context['ips'] = context['ips_available']

    class Region(list):
        pass

    tree = []

    for ip in context['ips']:
        for i, vregion in enumerate(get_regions_from_version_ip(ip, atype)):
            if len(tree) <= i:
                tree.append(Region())
            tree[i].append(vregion)

    # count the number of unique reading per region
    for wregion in tree:
        wreadings = {}
        for version in wregion:
            vreadings = {
                slugify(ms['region']): 1
                for ms
                in version['mss']
            }
            version['unique_readings'] = len(vreadings)
            wreadings.update(vreadings)
        wregion.unique_readings = len(wreadings)

    # generate a dictionary: region-id => degree of unsettledness
    # that maps with the image annotations drawn with the Text Editor

    regions_value = {}

    # TODO: get all regions from the heatmap
    idcount = {}
    tcx = TextContentXML.objects.filter(
        text_content__item_part__display_label__icontains='heat',
        text_content__type__slug=atype
    ).first()
    content = tcx.content
    xml = dputils.get_xml_from_unicode(content, ishtml=True, add_root=True)
    pattern = './/span[@data-dpt-type="unsettled"]'
    i = 0
    for element in xml.findall(pattern):
        is_element_work = element.attrib.get(
            'data-dpt-group', '').lower() == 'work'
        if not is_element_work:
            continue

        rid = ':'.join([
            pair[1]
            for pair in viewer.get_elementid_from_xml_element(element, idcount)
            if pair[0].startswith('@')
        ])

        if i < len(tree):
            regions_value[rid] = tree[i].unique_readings
        else:
            print(u'WARNING: tree[{}] doesnt exist, {}'.format(i, rid))

        i += 1

    # print(regions_value)
    context['regions_tree'] = tree
    context['regions_value'] = json.dumps(regions_value)

    return render(request, 'digipal_text/regions_tree.html', context)


def get_regions_from_version_ip(vip, atype):
    '''
    vip: the ItemPart for a version-text
    atype: 'transcription'|'translation'

    Returns all the regions from a version-text.
    For each region, returns the region as found in the version-text
    and as found in the participating MSS.

    returns:
    [
        {
            'ip': <ItemPart 'Version 1'>,
            'region': 'ab [] cd',
            'mss': [{
                'ip': <ItemPart 'MS 1'>,
                'region': 'ab xy cd',
                },
                'ip': <ItemPart 'MS 2'>,
                'region': 'ab pq cd',
            }],
        },
        ...
    ]
    '''
    ret = []

    ips = [vip] + list(vip.subdivisions.all())

    vxml = None

    pattern = './/span[@data-dpt-type="unsettled"]'

    for ip in ips:
        # get the xml for the Version or MS
        tcx = TextContentXML.objects.filter(
            text_content__item_part=ip,
            text_content__type__slug=atype
        ).first()
        content = tcx.content

        xml = dputils.get_xml_from_unicode(content, ishtml=True, add_root=True)

        is_ip_version = vxml is None
        if is_ip_version:
            vxml = xml
        else:
            # replace all the v-region in vxml with those found in MS xml
            mregions = [
                dputils.get_unicode_from_xml(
                    element, text_only=True, remove_root=True
                )
                for element
                in xml.findall(pattern)
            ]
            i = 0
            for element in vxml.findall(pattern):
                is_element_work = element.attrib.get(
                    'data-dpt-group', '').lower() == 'work'
                if not is_element_work:
                    tail = element.tail
                    # element.clear()
                    element.tail = tail
                    element.text = ur'[{}]'.format(mregions[i])
                    # print('H')
                    # print(element.text)
                    i += 1


        # extract all the w-regions from vxml
        i = 0
        for element in vxml.findall(pattern):
            is_element_work = element.attrib.get(
                'data-dpt-group', '').lower() == 'work'
            if not is_element_work:
                continue
            text = dputils.get_unicode_from_xml(
                element, text_only=True, remove_root=True
            )
            region = {
                'region': text,
                'ip': ip,
            }
            # print(i, region)
            if is_ip_version:
                region.update({'mss': []})
                ret.append(region)
            else:
                ret[i]['mss'].append(region)
            i += 1

    return ret


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
        dputils.get_plain_text_from_html(
            tcxs[msid]['record'].content) + ' EOT EOT'
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
        # w, skippeds = get_next_chunk1(ps, cs, stop_words)
        w, skippeds = get_next_chunk1(ps, cs, stop_words)

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


def normalise(w):
    return w.lower().replace('u', 'v')


def get_next_chunk2(ps, cs, stop_words):
    '''
    Method:
    We incrementally grow the unsettled regions in both texts cs
    from positions ps until we find two consecutive tokens.

    One token is at the end of the search string of one text,
    the other is anywhere inside the search string of the other text.

    This method copes better with large amount of change (e.g. Regiam).
    But it can be too inclusive and miss important 'anchor' tokens
    such as the line number or a rare word.
    '''
    w = None
    ls = [1, 1]
    skippeds = [[], []]
    while True:
        moved = 0
        for i in range(2):
            if (ps[i] + ls[i]) < len(cs[i]) - 1:
                ls[i] += 1
                moved = 1

        if not moved:
            break

        frags = [c[ps[i]:ps[i] + ls[i]] for i, c in enumerate(cs)]

        if normalise(frags[0][0]) == normalise(frags[1][0]):
            ps[0] += 1
            ps[1] += 1
            return frags[0][0], skippeds

        ds = [0, 0]
        for i, c in enumerate(cs):
            w0 = frags[i][-2:]
            for j in range(len(frags[1 - i]) - 1):
                if normalise(frags[1 - i][j]) == normalise(w0[0]) and normalise(frags[1 - i][j + 1]) == normalise(w0[1]):
                    ds[1 - i] = j
                    ds[i] = len(frags[i]) - 2

                    w = ' '.join(w0)

                    skippeds = [frags[0][:ds[0]], frags[1][:ds[1]]]

                    ps[0] += ds[0] + 2
                    ps[1] += ds[1] + 2

                    return w, skippeds

    return w, skippeds


def get_next_chunk1(ps, cs, stop_words):
    '''
    Returns the

    ps: current position in each text, e.g. [1, 4]
    cs: the tokenised texts, e.g. [['first', 'text'], ['second', 'text']]
    stop_words: list of frequent words

    Method:
    We incrementally grow the unsettled regions in both texts cs
    from positions ps until we find a common token.

    stop_words are not considered as common token because they are too frequent
    They would otherwise create false positive and disrupt the matching of
    subsequent regions or even the rest of the texts.
    '''
    w = None
    ls = [0, 0]
    skippeds = [[], []]
    while True:
        moved = 0
        if (ps[0] + ls[0]) < len(cs[0]) - 1:
            ls[0] += 1
            moved = 1
        if (ps[1] + ls[1]) < len(cs[1]) - 1:
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

    return w, skippeds


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

        if content:
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
