# -*- coding: utf-8 -*-
from digipal_text.models import TextContentXML, TextContentXMLStatus
from digipal.models import ItemPart
from digipal import utils as dputils
import regex as re


def TextContentXML_convert(self):
    content = self.content

    # 1. Clean up

    # normalise spaces
    content = re.sub(ur'(?musi)&nbsp;', ur' ', content)
    content = re.sub(ur'(?musi)\n+', ur' ', content)
    content = re.sub(ur'(?musi) +', ur' ', content)

    # remove all style/lang/class attributes
    # mark spans for deletion
    # exception: span with line-through
    if 1:
        attribs_to_remove = set(['style', 'class', 'lang', 'data-mce-style'])

        xml = dputils.get_xml_from_unicode(content, ishtml=True, add_root=True)

        for element in xml.findall('.//*'):
            attribs = set(element.attrib.keys())

            intersection = attribs.intersection(attribs_to_remove)
            if intersection:
                # convert strikethrough and underline
                styles = element.attrib.get('style', '')
                if 'line-through' in styles or 'underline' in styles:
                    element.attrib['data-dpt'] = 'del'
                    element.attrib['data-dpt-rend'] = 'strikethrough'

                for att in intersection:
                    del element.attrib[att]

            if element.tag.lower() in ['div', 'span']\
                    and not element.attrib.keys():
                element.tag = 'deleteme'

            if element.tag.lower() in ['em']:
                # <seg lang="vernacular">{}</seg>
                element.tag = 'span'
                element.attrib['data-dpt'] = 'seg'
                element.attrib['data-dpt-lang'] = 'vernacular'

        content = dputils.get_unicode_from_xml(xml, remove_root=True)
        content = re.sub(ur'</?deleteme>', ur'', content)

    convert_pipes = 1
    if convert_pipes:
        # remove all line break markup so it can be reconstructed from
        # pipes
        while True:
            l = len(content)
            content = re.sub(
                ur'<span data-dpt="sb"[^>]*>([^<]*)</span>', ur'\1', content)
            if len(content) == l:
                break

        # convert WORD|WORD into WORD-|WORD
        content = re.sub(ur'(?musi)(\w)\|(\w)', ur'\1-|\2', content)
        # convert - | into -|
        content = re.sub(ur'(?musi)-s+\|', ur'-|', content)

        # convert | and -| into spans
        # content = re.sub(ur'(-?\|+)', ur'<span data-dpt="lb"
        # data-dpt-cat="sep">\1</span>', content)
        content = re.sub(
            ur'(-?\|+)', ur'<span data-dpt="sb">\1</span>', content)

    # remove nested line break spans (due to bugs with multiple
    # conversions)
    if 1:
        while True:
            l = len(content)
            content = re.sub(ur'(<span[^>]*>)\1([^<>]*)(</span>)\3',
                             ur'\1\2\3', content)
            if len(content) == l:
                break

    # c. ii: chapter number
    content = re.sub(
        ur'\bc\.? ([ivxl]+)\b', ur'<span data-dpt="cn">\1</span>', content
    )
    # (1): sentence number
    content = re.sub(
        ur'\((\d+)\)', ur'<span data-dpt="sn">\1</span>', content
    )
    # /f.XXXra/ : page break
    content = re.sub(
        ur'/f\.?\s*([\dX]+[rvab]+)/',
        ur'<span data-dpt="location" data-dpt-loctype="locus">\1</span>', content
    )

    if 1:
        def replace_unsettled_unique(amatch):
            return replace_unsettled(amatch, 'unique')

        def replace_unsettled(amatch, atype='shared'):
            # convert empty [] to [ - ]
            ret = amatch.group(1)
            ret = ret.strip()
            if ret in ['', '...']:
                ret = '...'

            print(ret)

            subtype = 'data-dpt-subtype="{}"'.format(atype)

            ret = ur'<span data-dpt="seg" data-dpt-type="unsettled" {}>{}</span>'.format(
                subtype, ret)

            return ret

        # [] : unsettled text - unique
        content = re.sub(
            ur'<strong>\[</strong>([^\[\]]*)<strong>\]</strong>',
            ur'<strong>[\1]</strong>',
            content
        )
        # [] : unsettled text - unique
        content = re.sub(
            ur'<strong>\s*\[([^]<]*)\]\s*</strong>',
            replace_unsettled_unique,
            content
        )
        # [] : unsettled text - unique
        content = re.sub(
            ur'\[\s*<strong>([^]<]*)</strong>\s*\]',
            replace_unsettled_unique,
            content
        )
        # [] : unsettled text - shared
        content = re.sub(
            ur'\[([^]<]*)\]',
            replace_unsettled,
            content
        )

    content = re.sub(ur'<strong>(.*?)</strong>',
                     ur'<span data-dpt="hi" data-dpt-rend="highlight">\1</span>', content)

    # (Title) ... | chapter title
    if 1:
        content = re.sub(
            ur'(?musi)\(\s*Title\s*\)(.+?)(</?p>|<span data-dpt="s[bn]"|<span data-dpt="head")',
            ur'<span data-dpt="head">\1</span>\2',
            content
        )

    self.content = content


TextContentXML.convert = TextContentXML_convert


def add_region_ids_to_xml(xml):
    '''
    Add a unique @id attribute to all unsettled regions element in the XML.
    USED TO: Convert the ∅ to ⊕ in the MS-text only.
    '''

    # 0 if content has not changed (i.e. no need to save)
    inc = 0

    # assign an id to all the unsettled elements
    from datetime import datetime
    now = datetime.utcnow()
    n = (now - datetime(1970, 1, 1)).total_seconds()

    for element in xml.findall('.//span[@data-dpt-type="unsettled"]'):

        if 'id' not in element.attrib:
            inc += 1
            aid = '%0.8x%x' % (n, inc)
            element.attrib['id'] = aid

    return inc


def TextContentXML_save(self, *args, **kwargs):
    # initialise the status if undefined
    if not self.status_id:
        self.status = TextContentXMLStatus.objects.order_by(
            'sort_order').first()

    # TODO: don't call save twice... is that a bug?
    ret = super(TextContentXML, self).save(*args, **kwargs)

    if self.content:
        # add a unique @id to each region
        xml = dputils.get_xml_from_unicode(
            self.content, ishtml=True, add_root=True)
        add_region_ids_to_xml(xml)

        # note that after this the entities are converted to utf-8
        self.content = dputils.get_unicode_from_xml(xml, remove_root=True)

        # save
        ret = super(TextContentXML, self).save(*args, **kwargs)

    return ret


TextContentXML.save = TextContentXML_save


def TextContentXML_get_version_label(self):
    ret = u'?'
    ip = self.text_content.item_part
    if ip and ip.type:
        if ip.type.name == u'Work':
            ret = u'WORK'
        if ip.type.name == u'Version':
            ret = ip.custom_label
        if ip.type.name == u'Manuscript':
            if ip.group:
                ret = ip.group.custom_label

    return ret


TextContentXML.get_version_label = TextContentXML_get_version_label


def TextContentXML_get_work_label(self):
    ret = u'?'
    ip = self.text_content.item_part
    if ip and ip.type:
        if ip.type.name == u'Work':
            ret = ip.custom_label
        if ip.type.name == u'Version':
            if ip.group:
                ret = ip.group.custom_label
        if ip.type.name == u'Manuscript':
            if ip.group and ip.group.group:
                ret = ip.group.group.custom_label

    return ret


TextContentXML.get_work_label = TextContentXML_get_work_label


def TextContentXML_get_state(self):
    ret = 'Empty'
    content = (self.content or '').strip()
    if len(content) > 20:
        ret = self.status.name
        if self.status.slug == 'draft':
            if 'unsettled' not in content:
                ret += ' (not encoded)'
    return ret


TextContentXML.get_state = TextContentXML_get_state


def ItemPart_get_ctrs_label(self):
    ret = u''
    if self.current_item and self.current_item.repository:
        if self.current_item.repository.place:
            city = self.current_item.repository.place.name
            if city and city != 'COTR':
                ret += u'{}, '.format(city)
    ret += self.display_label
    return ret


ItemPart.get_ctrs_label = ItemPart_get_ctrs_label
