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

    drop
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
        '''
        Read CSV file and Insert or update records in the database.

        CurrentItem - sheflmark, archive
        ItemPart - locus, CI
        Text - context OR 'WORK, version VERSION'
        TextContent - IP, translation & IP, transcription
        TextContentXML - TC
        '''
        type_tsl, _ = TextContentType.objects.get_or_create(name='Translation')
        type_tsc, _ = TextContentType.objects.get_or_create(
            name='Transcription'
        )
        ci_ids = CurrentItem.objects.all().values_list('id', flat=True)
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
            if ci.id not in ci_ids:
                print(' new CI')
            if ci is None:
                print('WARNING: invalid inputs')
            else:
                options = dict(locus=row['locus'], current_item=ci)
                ip, c = ItemPart.objects.get_or_create(**options)
                if c:
                    print(' new IP')
                version_name = row['context']
                if not version_name:
                    version_name = '{}, version {}'.format(
                        row['work'], row['versionnumber']
                    )
                print(version_name)
                text, c = Text.objects.get_or_create(name=version_name)
                if c:
                    print(' new Text')
                for t in [type_tsl, type_tsc]:
                    tc, c = TextContent.objects.get_or_create(
                        item_part=ip, type=t
                    )
                    if c:
                        if c:
                            print(' new TC')
                        tc.text = text
                        tc.save()
                        tcx, c = TextContentXML.objects.get_or_create(
                            text_content=tc
                        )
                        if c:
                            tcx.content = '<p>Empty</p>'
                            tcx.save()
