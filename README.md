# CheckiO Downloader

## What is it?

This script parses a user's share URL at [CheckiO](https://checkio.org),
parses each linked solution and downloads the source to single files in a
given directory (if the solution is missing there).

The share URL is public, you can find it by accessing your "Profile" at 
[CheckiO](https://checkio.org) and navigating to "Progress".

## Usage

    $ python checkio_downloader.py --help
    usage: checkio_downloader.py [-h] [-o OUTPUT_DIRECTORY] [--overwrite]
                                [--dry-run]
                                USER_SHARE_URL

    Parses and downloads checkio solutions

    positional arguments:
    USER_SHARE_URL        shareable user solutions URL (at checkio.org, go to
                            "Profile" > "Progress" and copy the share URL)

    optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                            output directory for writing solution source files
                            (default: the current working directory)
    --overwrite           overwrite existing files
    --dry-run             dry run, do not (over-)write files

    Written by Christoph Haunschmidt

## Examples

    TODO...

## TODOs / Roadmap

 - Multi-solutions for a single task
 - Auto-commit to a git repo in the output directory for any new solution

## Requirements

  - A [Python 3.6+](https://www.python.org/) installation on your system
  - [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/):
    Install via `pip install beautifulsoup4` or your distribution's package
    manager. 
    
    Note: [Soup Sieve](https://facelessuser.github.io/soupsieve/)
    is also required, but usually installed automatically with bs4 

## License

[GNU GPL3](https://www.gnu.org/licenses/gpl-3.0.html)

## Contributors

 - Christoph Haunschmidt (original author)