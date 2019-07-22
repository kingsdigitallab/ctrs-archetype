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
from digipal.models import ItemPartType, ItemPart, CurrentItem, Text
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

        tc_types = {
            slugify(name): TextContentType.objects.get_or_create(name=name)[0]
            for name
            in ['Transcription', 'Translation']
        }
        ci_ids = CurrentItem.objects.all().values_list('id', flat=True)

        ip_types = {
            slugify(name): ItemPartType.objects.get_or_create(name=name)[0]
            for name
            in ['Manuscript', 'Version', 'Work']
        }

        #
        for tc in TextContent.objects.all():
            tc.text = None
            tc.save()

        # a special CI for all versions and works
        ci_cotr = CurrentItem.get_or_create('Editions', 'COTR, Database')
        ip_works = {}
        ip_versions = {}

        for row in read_all_lines_from_csv(self.args[0]):

            # create the work
            work_name = row['work']

            ip_work = ip_works.get(slugify(work_name), None)
            if not ip_work:
                ip_work = self.get_or_create_ip_and_textcontents(
                    ci_cotr, {
                        'custom_label': work_name
                    },
                    tc_types
                )
                ip_work.type = ip_types['work']
                ip_work.save()
                ip_works[slugify(work_name)] = ip_work

            # create the version
            version_name = row['context']
            if not version_name:
                version_name = '{}, version {}'.format(
                    row['work'], row['versionnumber']
                )
            print(version_name)

            ip_version = ip_versions.get(version_name, None)

            if not ip_version:
                ip_version = self.get_or_create_ip_and_textcontents(
                    ci_cotr, {
                        'custom_label': version_name
                    },
                    tc_types
                )
                ip_version.type = ip_types['version']
                ip_version.group = ip_work
                ip_version.save()
                ip_versions[slugify(version_name)] = ip_version

            # create MS-text

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
                ip = self.get_or_create_ip_and_textcontents(
                    ci, {
                        'locus': row['locus']
                    },
                    tc_types
                )
                ip.type = ip_types['manuscript']
                ip.group = ip_version
                ip.save()

    def get_or_create_ip_and_textcontents(
        self, ci, ip_options, tc_types, version_name=None,
    ):
        ip_options['current_item'] = ci
        ip, c = ItemPart.objects.get_or_create(**ip_options)
        if c:
            print(' new IP')
        text = None
        if version_name:
            text, c = Text.objects.get_or_create(name=version_name)
            if c:
                print(' new Text')
        for tc_type in tc_types.values():
            tc, c = TextContent.objects.get_or_create(
                item_part=ip, type=tc_type
            )
            if c:
                if c:
                    print(' new TC')
                if text:
                    tc.text = text
                tc.save()
                tcx, c = TextContentXML.objects.get_or_create(
                    text_content=tc
                )
                if c:
                    tcx.content = '<p>Empty</p>'
                    tcx.save()

        return ip
