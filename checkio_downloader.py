#!/usr/bin/env python3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
####################################################################################
#
# A Python script download solutions from https://checkio.org
#
# tested on Python 3.6+
# requires: Beautiful Soup (https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
#
# Christoph Haunschmidt, started 2019-09

import argparse
import datetime
import os
import re
import string
import sys
import urllib.parse
import urllib.request
from collections import defaultdict, namedtuple

from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
}


def get_url(url):
    request = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(request)
    return resp.read()


def get_schema_and_domain_from_url(url):
    parse_result = urllib.parse.urlparse(url)
    return '{0.scheme}://{0.netloc}'.format(parse_result)


class CheckIOSolution:
    class InvalidFormatKeyError(Exception):
        pass

    FIELDS_BY_HTML = set('html posted_at solution_source solution_title mission_title solution_category'.split())

    FIELDS_BY_URL = set('url extension mission_title_slug user_name solution_title_slug solution_hash'.split())

    ALL_FIELDS = FIELDS_BY_HTML | FIELDS_BY_URL

    FORMAT_STR_DICT_FIELDS = ALL_FIELDS - {'html', 'solution_source'}

    SOLUTION_URL_RE = re.compile(r'^(?:http(s)?:\/\/)?'
                                 '(?P<extension>\w+)\.checkio\.org/mission/'
                                 '(?P<mission_title_slug>[\w\-]+)/publications/'
                                 '(?P<user_name>[^/]+)/[^/]+/'
                                 '(?P<solution_title_slug>[^/]+)/share/'
                                 '(?P<solution_hash>[a-z0-f]+)/?$', re.IGNORECASE)

    DEFAULT_FORMAT_STR = '{mission_title_slug}.{extension}'

    def __init__(self, url):
        m = CheckIOSolution.SOLUTION_URL_RE.match(url)
        if not m:
            raise ValueError(f'Is not a valid solution URL: {url}')
        for field in CheckIOSolution.FIELDS_BY_URL:
            setattr(self, field, m.groupdict().get(field, ''))
        self.url = url
        self.extension = self.extension.lower()
        self._processed = False

    def process_url(self):
        self.html = get_url(self.url)
        soup = BeautifulSoup(self.html, features='html.parser')
        date_str = soup.select('noscript p[style="text-align: center;"]')[0].get_text(strip=True)
        self.posted_at = datetime.datetime.strptime(date_str, '%B %d, %Y').date()
        self.mission_title = soup.select('noscript p > a')[1].get_text(strip=True)
        self.solution_title = soup.select('noscript p > b')[0].get_text(strip=True)
        self.solution_category = soup.select('noscript p > a')[0].get_text(strip=True)
        self.solution_source = soup.select('noscript pre[class^=brush]')[0].get_text()
        self._processed = True

    def __getattr__(self, name):
        if name in CheckIOSolution.FIELDS_BY_HTML:
            if not self._processed:
                self.process_url()
        return self.__getattribute__(name)

    def filename(self, format_str=None):
        format_str = format_str or CheckIOSolution.DEFAULT_FORMAT_STR
        needed_fields = {t[1] for t in string.Formatter().parse(format_str)}
        invalid_fields = needed_fields - CheckIOSolution.FORMAT_STR_DICT_FIELDS
        if invalid_fields:
            raise CheckIOSolution.InvalidFormatKeyError('Invalid format key: "{}"'.format('", "'.join(invalid_fields)))
        return format_str.format_map({field: getattr(self, field) for field in needed_fields})

    @property
    def source_code(self):
        return self.solution_source

    def __str__(self):
        result = []
        for field in self.FIELDS_BY_URL:
            result.append('{0}="{1}"'.format(field, getattr(self, field)))
        return '\n'.join(result)


class CheckIODownloader:

    SolutionMeta = namedtuple('SolutionMeta', 'url mission_title solution_title')

    USER_SOLUTIONS_URL_RE = re.compile(r'^(?:http(s)?:\/\/)?'
                                       '(?P<extension>\w+)\.checkio\.org/user/'
                                       '(?P<user_name>[^/]+)/solutions/share/'
                                       '(?P<user_hash>[a-z0-f]+)/?$', re.IGNORECASE)

    def __init__(self, url, output_directory, filename_format='', overwrite=False, dry_run=False):
        self.url = url
        self.output_directory = output_directory
        self.filename_format_str = filename_format
        self.overwrite = overwrite
        self.dry_run = dry_run

        self.stats = defaultdict(set)
        self.solutions_meta = []
        self.solutions = []
        self.parse_solution_urls()

    def parse_solution_urls(self):
        self.solutions_meta = []
        m = CheckIOSolution.SOLUTION_URL_RE.match(self.url)
        if m:
            solution_meta = CheckIODownloader.SolutionMeta(
                url=self.url, mission_title=m.group('mission_title_slug'),
                solution_title=m.group('solution_title_slug'))
            self.solutions_meta = [solution_meta]
            return

        m = CheckIODownloader.USER_SOLUTIONS_URL_RE.match(self.url)
        if not m:
            raise ValueError(f'Not a user solutions URL: {self.url}')

        soup = BeautifulSoup(get_url(self.url), features='html.parser')

        solution_rows = soup.select('div.block_progress.block_progress__container')
        for row in solution_rows:
            anchor = row.select('div.block_progress_main.block_progress__row a')[0]
            url = anchor['href']
            if url.startswith('/'):
                url = get_schema_and_domain_from_url(self.url) + url
            mission_title = row.select('span.block_progress_task.block_progress__row')[0].get_text(strip=True)
            solution_meta = CheckIODownloader.SolutionMeta(
                url=url, solution_title=anchor.get_text(strip=True), mission_title=mission_title)
            self.solutions_meta.append(solution_meta)
        return self.solutions_meta

    @staticmethod
    def write_file(output_file_full_path, content):
        if content:
            with open(output_file_full_path, 'w') as f:
                f.write(content)

    def process_solution_urls(self):
        for i, solution_meta in enumerate(self.solutions_meta, start=1):
            try:
                title = '{0.mission_title} | {0.solution_title}'.format(solution_meta)[:50]
                print(f'[ {i:>4} / {len(self.solutions_meta):<4} ] [ {title:50} ] ... ', end='')
                solution = CheckIOSolution(solution_meta.url)
                to_file = os.path.join(self.output_directory, solution.filename(format_str=self.filename_format_str))
                if os.path.exists(to_file):
                    self.stats['existing'].add(solution)
                    if self.overwrite:
                        if not self.dry_run:
                            self.write_file(to_file, solution.source_code)
                        print('OK - already existing, overwritten')
                        self.stats['overwritten'].add(solution)
                    else:
                        print('OK - already existing, skipped')
                else:
                    if not self.dry_run:
                        self.write_file(to_file, solution.source_code)
                    print('OK - new')
                    self.stats['new'].add(solution_meta)
                self.solutions.append(solution)
            except CheckIOSolution.InvalidFormatKeyError as excp:
                print(f'FAIL: {excp}, QUITTING')
                sys.exit(1)
            except Exception as excp:
                print(f'FAIL: {excp}')
                self.stats['error'].add(solution)

    def __str__(self):
        result = ['CheckIODownloader Statistics{}'.format('' if not self.dry_run else ' (DRY RUN)')]
        result.append('Existing: {}'.format(len(self.stats.get('existing', []))))
        result.append('New: {}'.format(len(self.stats.get('new', []))))
        result.append('Overwritten: {}'.format(len(self.stats.get('overwritten', []))))
        result.append('Errors: {}'.format(len(self.stats.get('error', []))))
        return '\n'.join(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Parses and downloads CheckiO solutions',
        epilog='Written by Christoph Haunschmidt')

    parser.add_argument('url', metavar='CHECKIO_URL',
                        help='shareable user solutions (at checkio.org, go to "Profile" > "Progress" '
                        'and copy the share URL) or single solution URL')
    parser.add_argument('-o', '--output-directory', default=os.getcwd(),
                        help='output directory for writing solution source files '
                        '(default: the current working directory)')
    parser.add_argument('--filename-format', default=CheckIOSolution.DEFAULT_FORMAT_STR,
                        metavar='FORMAT_IN_PYTHON_FORMAT_SYNTAX',
                        help='filename format for the solution files (without extension). This is in Pythons '
                        'string formatting syntax. All values are strings except "posted_at", which is of type '
                        '"datetime.date". Possible keys are: '
                        '"{}" (default: "%(default)s")'.format(
                            '", "'.join(sorted(CheckIOSolution.FORMAT_STR_DICT_FIELDS))))
    parser.add_argument('--overwrite', action='store_true', default=False,
                        help='overwrite existing files')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='dry run, do not (over-)write files')

    args = parser.parse_args()

    try:
        checkio_downloader = CheckIODownloader(**vars(args))
        checkio_downloader.process_solution_urls()
        print(checkio_downloader, file=sys.stderr)
    except Exception as e:
        print('Error: {}'.format(e), file=sys.stderr)
        sys.exit(1)
