# -*- coding: utf-8 -*-
from digipal_text.models import TextContentXML, TextUnits, TextUnit, ClassProperty
from digipal.utils import re_sub_fct
from digipal import utils as dputils
from django.db import models
import regex as re


def TextContentXML_convert(self):
    content = self.content

    print('---------CONVERSION OF THE TRANSLATION--------')

    # 1. Clean up

    content = re.sub(ur'<span[^>]*></span>', u'', content)

    # remove all &nbsp;
    content = re.sub(ur'(?musi)&nbsp;', ur' ', content)
    content = re.sub(ur'(?musi)\n+', ur' ', content)
    content = re.sub(ur'(?musi) +', ur' ', content)

    content = re.sub(ur'style\s*=\s*"[^"]*"', ur'', content)

    convert_pipes = 1
    if convert_pipes:
        # remove all line break markup so it can be reconstructed from
        # pipes
        while True:
            l = len(content)
            content = re.sub(
                ur'<span data-dpt="lb"[^>]*>([^<]*)</span>', ur'\1', content)
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
            ur'(-?\|+)', ur'<span data-dpt="lb" data-dpt-src="ms">\1</span>', content)

    # remove nested line break spans (due to bugs with multiple
    # conversions)
    if 1:
        while True:
            l = len(content)
            content = re.sub(ur'(<span[^>]*>)\1([^<>]*)(</span>)\3',
                             ur'\1\2\3', content)
            if len(content) == l:
                break

    # remove all style/lang/class attributes
    # mark spans for deletion
    # exception: span with line-through
    if 0:
        xml = dputils.get_xml_from_unicode(content, ishtml=True, add_root=True)

        for element in xml.findall('.//*'):
            delete = element.tag == 'span'
            styles = element.attrib.get('style', '')
            if 'line-through' in styles or 'underline' in styles:
                element.attrib['data-dpt'] = 'del'
                element.attrib['data-dpt-cat'] = 'words'
                if 'underline' in styles:
                    element.attrib['data-dpt-type'] = 'supplied'
                delete = False
            if delete:
                element.tag = 'deleteme'
            else:
                if 'style' in element.attrib:
                    del element.attrib['style']
                if 'lang' in element.attrib:
                    del element.attrib['lang']
                if 'class' in element.attrib:
                    del element.attrib['class']

        content = dputils.get_unicode_from_xml(xml, remove_root=True)

    # (1): sentence number
    content = re.sub(ur'\((\d+)\)', ur'<span data-dpt="sb">\1</span>', content)
    # /f.XXXra/ : page break
    content = re.sub(ur'/f.([\dX]+[rvab]+)/', ur'<span data-dpt="location" data-dpt-loctype="locus">\1</span>', content)
    # | : line break
    content = re.sub(ur'()\|', ur'<span data-dpt="lb">|</span>', content)
    # | : unsettled text
    content = re.sub(ur'\[[^]*]\]', ur'<span data-dpt="lb">|</span>', content)

    self.content = content


TextContentXML.convert = TextContentXML_convert
