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
    FIELDS = set(
        'extension title url user_name src posted_at solution_hash solution_title_slug solution_source '
        'mission_title mission_title_slug tag'.split())

    SOLUTION_URL_RE = re.compile(r'^(?:http(s)?:\/\/)?'
                                 '(?P<extension>\w+)\.checkio\.org/mission/'
                                 '(?P<mission_title_slug>[\w\-]+)/publications/'
                                 '(?P<user_name>[^/]+)/[^/]+/'
                                 '(?P<solution_title_slug>[^/]+)/share/'
                                 '(?P<solution_hash>[a-z0-f]+)/?$', re.IGNORECASE)

    def __init__(self, url):
        m = CheckIOSolution.SOLUTION_URL_RE.match(url)
        if not m:
            raise ValueError(f'Is not a valid solution URL: {url}')
        for field in self.FIELDS:
            setattr(self, field, m.groupdict().get(field, ''))
        self.url = url
        self.extension = self.extension.lower()
        self.processed = False

    def process_url(self):
        self.src = get_url(self.url)
        soup = BeautifulSoup(self.src, features='html.parser')
        self.solution_source = soup.select('noscript pre[class^=brush]')[0].get_text()
        date_str = soup.select('noscript p[style="text-align: center;"]')[0].get_text(strip=True)
        self.posted_at = datetime.datetime.strptime(date_str, '%B %d, %Y').date()
        self.solution_title = soup.select('noscript p > b')[0].get_text(strip=True)
        self.mission_title = soup.select('noscript p > a')[1].get_text(strip=True)
        self.tag = soup.select('noscript p > a')[0].get_text(strip=True)
        self.processed = True

    @property
    def filename(self):
        return '{0.mission_title_slug}.{0.extension}'.format(self)

    @property
    def source_code(self):
        if not self.processed:
            self.process_url()
        return self.solution_source

    def __str__(self):
        result = []
        for field in self.FIELDS - {'src', 'solution_source'}:
            result.append('{0}="{1}"'.format(field, getattr(self, field)))
        return '\n'.join(result)


class CheckIODownloader:
    SolutionMeta = namedtuple('SolutionMeta', 'url mission_title solution_title')

    USER_SOLUTIONS_URL_RE = re.compile(r'^(?:http(s)?:\/\/)?'
                                       '(?P<extension>\w+)\.checkio\.org/user/'
                                       '(?P<user_name>[^/]+)/solutions/share/'
                                       '(?P<user_hash>[a-z0-f]+)/?$', re.IGNORECASE)

    def __init__(self, url, output_directory, overwrite=False, dry_run=False):
        self.url = url
        self.output_directory = output_directory
        self.overwrite = overwrite
        self.dry_run = dry_run

        self.stats = defaultdict(set)
        self.solutions_meta = []
        self.solutions = []
        self.parse_solution_urls()

    def parse_solution_urls(self):
        self.solutions_meta = []

        m = CheckIODownloader.USER_SOLUTIONS_URL_RE.match(self.url)
        if not m:
            raise ValueError(f'Not a user solutions URL: {self.url}')

        schema_domain = get_schema_and_domain_from_url(self.url)
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
                to_file = os.path.join(self.output_directory, solution.filename)
                if os.path.exists(to_file):
                    self.stats['existing'].add(solution_meta)
                    if self.overwrite:
                        if not self.dry_run:
                            self.write_file(to_file, solution.source_code)
                        print('OK - already existing, overwritten')
                        self.stats['overwritten'].add(solution_meta)
                    else:
                        print('OK - already existing, skipped')
                else:
                    if not self.dry_run:
                        self.write_file(to_file, solution.source_code)
                    print('OK - new')
                    self.stats['new'].add(solution_meta)
                self.solutions.append(solution)
            except Exception as excp:
                print(f'FAIL: {excp}')
                self.stats['error'].add(solution_meta)

    def __str__(self):
        result = ['CheckIODownloader Statistics{}'.format('' if not self.dry_run else ' (DRY RUN)')]
        result.append('Existing: {}'.format(len(self.stats.get('existing', []))))
        result.append('New: {}'.format(len(self.stats.get('new', []))))
        result.append('Overwritten: {}'.format(len(self.stats.get('overwritten', []))))
        result.append('Errors: {}'.format(len(self.stats.get('error', []))))
        return '\n'.join(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Parses and downloads checkio solutions',
        epilog='Written by Christoph Haunschmidt')

    parser.add_argument('url', metavar='USER_SHARE_URL',
                        help='shareable user solutions URL (at checkio.org, go to "Profile" > "Progress" '
                        'and copy the share URL)')
    parser.add_argument('-o', '--output-directory', default=os.getcwd(),
                        help='output directory for writing solution source files '
                        '(default: the current working directory)')
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
