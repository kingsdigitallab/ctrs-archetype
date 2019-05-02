# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
from os.path import isdir
import os
import sys
import shlex
import subprocess
import re
from optparse import make_option
from django.db import IntegrityError
from digipal.models import *
from digipal.utils import natural_sort_key, read_all_lines_from_csv
from digipal.templatetags.hand_filters import chrono
from django.template.defaultfilters import slugify
from time import sleep
from digipal.management.commands.dpbase import DPBaseCommand
from digipal_text.models import TextContent, TextContentXML, TextContentType


class Command(DPBaseCommand):
    help = """
Cotr-archetype text tools

Commands:

    import_text_meta CSV_FILE
        Insert/Update CI, IP & Text records from a CSV file
        (work, context, )

    email

    validate

    record_path
        Test the field extraction from record + path used by the faceted search module
        e.g. record_path manuscripts historical_item.historical_item_type.name 598

    dateconv [hi [HI_ID]]
        reports datse which cannot be parsed correctly
        if hi: check hi.get_date_sort() otherwise check dateevidence.date

    max_date_range FIELD
        e.g. max_date_range HistoricalItem.date
        returns the minimum and maximum of the date values among all HistoricalItem records

    date_prob
        report all HI dates with a very wide range (unrecognised, or open ended range)

    cs
        TODO
        collect static

    cpip REQ1 REQ2
        compare two PIP req files (pip freeze)

    download_images URL
        URL: e.g. "http://domain/path/to/image_{001_r,003_v}.jpg"

    unstatic
        Opposite of collectstatics
        It removes the copies of the assets
        This is only for dev env. when you are changing the js/css, ...
        Note that transpiled code can't be made dynamic (e.g. less, ts)

    jsdates
        test date conversion during json parsing
"""

    args = 'locus|email'
    option_list = BaseCommand.option_list + (
        make_option('--db',
                    action='store',
                    dest='db',
                    default='default',
                    help='Name of the target database configuration (\'default\' if unspecified)'),
        make_option('--src',
                    action='store',
                    dest='src',
                    default='hand',
                    help='Name of the source database configuration (\'hand\' if unspecified)'),
        make_option('--table',
                    action='store',
                    dest='table',
                    default='',
                    help='Name of the tables to backup. This acts as a name filter.'),
        make_option('--dry-run',
                    action='store_true',
                    dest='dry-run',
                    default=False,
                    help='Dry run, don\'t change any data.'),
    )

    def handle(self, *args, **options):

        self.log_level = 3

        self.options = options

        if len(args) < 1:
            raise CommandError(
                'Please provide a command. Try "python manage.py help dpmigrate" for help.')
        args = list(args)
        command = args.pop(0)

        self.args = args

        known_command = False

        if command == 'import':
            self.import_text_meta()
            known_command = True

        if command == 'drop':
            self.drop()
            known_command = True

        if not known_command:
            print(self.help)

    def drop(self):
        for m in [CurrentItem, ItemPart, Text]:
            m.objects.all().delete()

    def import_text_meta(self):
        type_tsl, _ = TextContentType.objects.get_or_create(name='Translation')
        type_tsc, _ = TextContentType.objects.get_or_create(
            name='Transcription'
        )
        for row in read_all_lines_from_csv(self.args[0]):
            '''
            u'context': u'John Haldenstone',
            u'work': u'Declaration',
            u'locus': u'',
            u'shelfmark': u'Codex Helmstedt 411',
            u'archive': u'Wolfenb\xfcttel, Herzog August Bibliothek',
            '_line_index': 26
            '''
            print(row['shelfmark'], row['archive'])
            ci = CurrentItem.get_or_create(row['shelfmark'], row['archive'])
            if ci is None:
                print('WARNING: invalid inputs')
            else:
                options = dict(locus=row['locus'], current_item=ci)
                ip, c = ItemPart.objects.get_or_create(**options)
                text, c = Text.objects.get_or_create(name=row['context'])
                for t in [type_tsl, type_tsc]:
                    tc, c = TextContent.objects.get_or_create(
                        item_part=ip, type=t
                    )
                    if c:
                        tc.text = text
                        tc.save()
                        tcx, c = TextContentXML.objects.get_or_create(
                            text_content=tc
                        )
                        if c:
                            tcx.content = '<p>Empty</p>'
                            tcx.save()
