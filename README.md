# CheckiO Downloader

## What is it?

This script parses a user's share URL at [CheckiO](https://checkio.org),
parses each linked solution and downloads the source to single files in a
given directory (if the solution is missing there).

The share URL is public, you can find it by accessing your "Profile" at 
[CheckiO](https://checkio.org) and navigating to "Progress".

__NOTE__: Be careful with the output file format, if you have multiple
solutions for a mission, they could be overwritten if the filename results in
the same names.

## Usage

    $ python checkio_downloader.py --help
    usage: checkio_downloader.py [-h] [-o OUTPUT_DIRECTORY]
                                [--filename-format FORMAT_IN_PYTHON_FORMAT_SYNTAX]
                                [--overwrite] [--dry-run]
                                CHECKIO_URL

    Parses and downloads CheckiO solutions

    positional arguments:
    CHECKIO_URL           shareable user solutions (at checkio.org, go to
                            "Profile" > "Progress" and copy the share URL) or
                            single solution URL

    optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                            output directory for writing solution source files
                            (default: the current working directory)
    --filename-format FORMAT_IN_PYTHON_FORMAT_SYNTAX
                            filename format for the solution files (without
                            extension). This is in Pythons string formatting
                            syntax. All values are strings except "posted_at",
                            which is of type "datetime.date". Possible keys are:
                            "extension", "mission_title", "mission_title_slug",
                            "posted_at", "solution_category", "solution_hash",
                            "solution_title", "solution_title_slug", "url",
                            "user_name" (default:
                            "{mission_title_slug}.{extension})"
    --overwrite           overwrite existing files
    --dry-run             dry run, do not (over-)write files

    Written by Christoph Haunschmidt

## Examples

_Note: The URLs are made up, adapt them_

    python checkio_downloader.py "https://py.checkio.org/user/SomeUser/solutions/share/abcde543215bff5903597c48ce40dc53/"

Downloads files to the current working directory, not overwriting existing
files and naming them like the mission slug, e.g. `stressful-subject.py`.

    python checkio_downloader.py "https://py.checkio.org/mission/stressful-subject/publications/SomeUser/python-3/using-itertoolsgroupby/share/6345cabf80faff4e29cddd2dd9eb1bd0/" --output-directory "test" --overwrite --filename-format "{user_name} - {mission_title} - {posted_at} - {solution_title}.{extension}"

Results in a file like `test/SomeUser - Stressful Subject - 2019-07-15 - My awesome solution`,
possibly overwriting existing files with that name.

## TODOs / Roadmap

 - Multi-solutions for a single task
 - Auto-commit to a git repo in the output directory for any new solution

## Requirements

  - A [Python 3.6+](https://www.python.org/) installation on your system
  - [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/):
    Install via `pip install beautifulsoup4` or your distributions package
    manager. 
    
    Note: [Soup Sieve](https://facelessuser.github.io/soupsieve/)
    is also required, but usually installed automatically with bs4 

## License

[GNU GPL3](https://www.gnu.org/licenses/gpl-3.0.html)

## Contributors

 - Christoph Haunschmidt (original author)