# -*- coding: utf-8 -*-
from django.shortcuts import render
from digipal.models import ItemPart
from digipal_text.models import TextContentXML, TextContentType
from digipal import utils as dputils
from django.utils.text import slugify
from digipal_text.views import viewer
import json

# the xpath to find unsettled regions in the XML
XPATH_REGION = './/span[@data-dpt-type="unsettled"]'


def view_regions_table(request, parent_ip_id=None):
    '''
    Returns data to display a table used by project team editors
    to verify that the mark up matches across all XMLs.

    parent_ip_id = the id of the parent ItemPart (Version or Work)
    It will be shown in the first column, subsequent columns are for the
    children itempart.

    Two cases:
    a) the parent is a Version and children are MS-Texts
    b) the parent is a Work and the children are Versions
    '''
    context = {
        'wide_page': True,
    }

    ip_parent = ItemPart.objects.filter(id=parent_ip_id).first()
    context['ip_parent'] = ip_parent
    context['tcs'] = []
    is_parent_work = ip_parent.type.name.lower() == 'work'

    atype = set_context_types_from_request(request, context)

    for ip, tcx, xml in get_group_from_parent_ip(ip_parent, atype):
        regions = []

        for element in xml.findall(XPATH_REGION):
            if is_parent_work != is_work_region(element):
                continue

            region_content = dputils.get_unicode_from_xml(
                element, text_only=True
            )

            regions.append({
                'id': element.attrib['id'],
                'content': region_content,
            })

        context['tcs'].append({
            'ip': ip,
            'regions': regions
        })

    context['slots'] = range(
        max([len(tc['regions']) for tc in context['tcs']])
    )

    return render(request, 'digipal_text/regions_table.html', context)


def view_regions_tree(request):
    '''
    Returns a list of regions for the Versions selected by the users.
    For each region, returns statistics and values taken by each
    version.
    '''
    context = {}

    atype = set_context_types_from_request(request, context)

    context['ips_available'] = ItemPart.objects.filter(
        type__name__iexact='version',
        group__display_label__iexact='declaration'
    )

    # ips selected by user
    context['ips'] = [
        ip for ip in context['ips_available']
        if request.GET.get('ip-{}'.format(ip.pk), '')
    ]
    if not context['ips']:
        context['ips'] = context['ips_available']

    class Region(list):
        pass

    tree = []

    for vip in context['ips']:
        for i, vregion in enumerate(get_regions_from_version_ip(vip, atype)):
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
    i = 0
    for element in xml.findall(XPATH_REGION):
        if not is_work_region(element):
            continue

        rid = ':'.join([
            pair[1]
            for pair in viewer.get_elementid_from_xml_element(element, idcount)
            if pair[0].startswith('@')
        ])

        if i < len(tree):
            regions_value[rid] = tree[i].unique_readings
        else:
            print(u'WARNING: tree[{}] doesnt exist, {}'.format(i, repr(rid)))

        i += 1

    # print(regions_value)
    context['regions_tree'] = tree
    context['regions_value'] = json.dumps(regions_value)

    return render(request, 'digipal_text/regions_tree.html', context)


def get_regions_from_version_ip(parent_ip, atype):
    '''
    parent_ip: ItemPart of a Version-Text
    atype: 'transcription'|'translation'

    Returns all the regions from the parent document.
    For each region, returns the region as found in the parent and direct
    children.

    returns:
    [
        {
            'ip': <ItemPart 'Version 1'>,
            'region': 'ab [] cd',
            'mss': [{
                'ip': <ItemPart 'MS 1'>,
                'region': 'ab xy cd',
                }, {
                'ip': <ItemPart 'MS 2'>,
                'region': 'ab pq cd',
                },
                # ...
            }],
        },
        # next region in <ItemPart 'Version 1'>
    ]
    '''
    ret = []

    # the parent text, also used as a XML canvas
    pxml = None

    for ip, tcx, xml in get_group_from_parent_ip(parent_ip, atype):
        is_ip_parent = pxml is None
        if is_ip_parent:
            pxml = xml
        else:
            # replace all the v-regions in pxml with those found in child xml

            # collect all child regions
            mregions = [
                dputils.get_unicode_from_xml(
                    element, text_only=True, remove_root=True
                )
                for element
                in xml.findall(XPATH_REGION)
            ]

            # replace the v-regions only in the canvas / pxml
            i = 0
            for element in pxml.findall(XPATH_REGION):
                if not is_work_region(element):
                    region_text = 'MISSING'
                    if i < len(mregions):
                        region_text = mregions[i]

                    tail = element.tail
                    element.tail = tail
                    element.text = ur'[{}]'.format(region_text)
                    i += 1

        # extract all the w-regions from pxml
        i = 0
        for element in pxml.findall(XPATH_REGION):
            if not is_work_region(element):
                continue
            text = dputils.get_unicode_from_xml(
                element, text_only=True, remove_root=True
            )
            region = {
                'region': text,
                'ip': ip,
            }
            # print(i, region)
            if is_ip_parent:
                region.update({'mss': []})
                ret.append(region)
            else:
                ret[i]['mss'].append(region)
            i += 1

    return ret


def view_regions_detect(request):
    '''
    Experimental view to automatically find unsettled regions
    among a list of texts by comparing their content.
    '''

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


def is_work_region(element):
    '''
    Returns True if the given element is a W-region.
    As opposed to a V-region.

    element: a ElementTree Element instance (i.e. an XML Element)
    '''
    return element.attrib.get('data-dpt-group', '').lower() == 'work'


def set_context_types_from_request(request, context=None):
    atypes = TextContentType.objects.all().order_by('id')

    default_type = atypes[0].slug
    atype = request.GET.get('type', default_type)
    other_type = atypes[1].slug
    if atype == other_type:
        other_type = default_type

    if context is not None:
        context['other_type'] = other_type
        context['this_type'] = atype

    return atype


def get_group_from_parent_ip(parent_ip, atype):
    '''
    Returns a list of entries.
    Each entry correspond to a text.
    The first entry is for the parent_ip.
    The following ones are for the children of the parent.
    Each entry is [ip, tcx, xml]
    Where ip is an ItemPart. tcx a TextContentXML and xml an ElementTree
    '''
    ips = [parent_ip] + list(
        parent_ip.subdivisions.all().order_by('display_label')
    )

    for ip in ips:
        tcx = TextContentXML.objects.filter(
            text_content__item_part=ip,
            text_content__type__slug=atype
        ).first()
        content = tcx.content or ''

        xml = dputils.get_xml_from_unicode(
            content, ishtml=True, add_root=True
        )

        yield ip, tcx, xml
