#!/usr/bin/env python
#
# Fix music file names and tags.
#
# dmb 24-Feb-2013
#
from __future__ import print_function
import sys
import os
import argparse
import codecs

import name

sys.stdout = codecs.getwriter('utf8')(sys.stdout)
if __name__ == '__main__':
    cwd = os.getcwd()
    root = None

    parser = argparse.ArgumentParser("correct filenames and tags of music files")
    parser.add_argument('-r', '--root', action='store', default=None, dest='root', help='specify root of filesystem tree to examine (default: %s)' % cwd)
    parser.add_argument('-l', '--follow-links', action='store_true', default=False, dest='followlinks', help='follow symlinks')
    parser.add_argument('-n', '--just-testing', action='store_true', default=False, dest='testing', help='do not make changes; just display what actions would be taken')
    parser.add_argument('-e', '--encoding', action='store', default='utf8', dest='encoding', help='output encoding for filenames (default: utf8)')
    parser.add_argument('-s', '--strip-diacritics', action='store_true', default='False', dest='stripdiacritics', help='replace characters with accents and other diacritics with plain ASCII variants')
    parser.add_argument('-g', '--set-group', action='store', default=None, dest='group', help='set group of all files and directories')
    parser.add_argument('-o', '--set-owner', action='store', default=None, dest='owner', help='set owner of all files and directories')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose', help='be verbose')
    flags = parser.parse_args()

    root = root or flags.root or cwd

    print("scanning %s..." % root)

    # Make a name fixer and use it to fix pathnames
    namefixer = name.fixer(flags.stripdiacritics, flags.encoding, flags.followlinks)
    namefixer.fix(root, flags.owner, flags.group, flags.testing, flags.verbose)
    namefixer.report()
