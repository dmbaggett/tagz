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

from chardet import detect

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

if __name__ == '__main__':
    cwd = os.getcwd()

    root = None
    prune_dirs = ['.AppleDouble']
    prune_files = ['.DS_Store']
    substitutions = {
        # Stuff we don't want in filenames
        '#': "No.",
        '/': "-",
        '\\': "-",
        '[': "",
        ']': "",
        ':': "-",

        # Whitespace
        u'\xa0': ' ',

        # Quote characters
        "''": "'",        # doubled single quote
        '"': "'",         # double quote
        u'\x22': "'",     # quotation mark
        u'\xbf': "?",     # upside-down question mark
        u'\xab': "'",     # left-pointing double-angle quotation mark (guillemet)
        u'\xbb': "'",     # left-pointing double-angle quotation mark (guillemet)
        u'\u201c': "'",   # left double quotation mark
        u'\u201d': "'",   # left double quotation mark
        u'\u201e': "'",   # double low-9 quotation mark
        u'\u201f': "'",   # double high-reversed-9 quotation mark
        u'\u2039': "'",   # single left-pointing angle quotation mark
        u'\u203a': "'",   # single right-pointing angle quotation mark
        u'\u301d': "'",   # reversed double prime quotation mark
        u'\u301e': "'",   # double prime quotation mark
        u'\u301f': "'",   # low double prime quotation mark
        u'\uff02': "'",   # fullwidth quotation mark
        u'\uff07': "'",   # fullwidth apostrophe

        # Small form variants
        u'\ufe50': "'",
        u'\ufe51': "'",
        u'\ufe52': "-",
        u'\ufe53': "-",
        u'\ufe54': ";",
        u'\ufe55': "-",
        u'\ufe56': "?",
        u'\ufe57': "!",
        u'\ufe58': "-",
        u'\ufe59': "(",
        u'\ufe5a': ")",
        u'\ufe5b': "{",
        u'\ufe5c': "}",
        u'\ufe5d': "",
        u'\ufe5e': "",
        u'\ufe5f': "No.",
        u'\ufe60': "&",
        u'\ufe61': "*",
        u'\ufe62': "+",
        u'\ufe63': "-",
        u'\ufe64': "<",
        u'\ufe65': ">",
        u'\ufe66': "=",
        u'\ufe67': "",
        u'\ufe68': "-",
        u'\ufe69': "$",
        u'\ufe6a': "%",
        u'\ufe6b': "@",

        # Half-width and full-width forms (TBD)
        u'\uff01': "!",

        # Bullets and other miscellany
        u'\u2027': '-',
        u'\u2116': 'No.', # numero sign
        u'\xb0': 'o.', # superscript o
        u'\xa1E': ' - ',

        # Keys
        u'FNo.': "F sharp",
        u'CNo.': "C sharp",
        u'F#': "F sharp",
        u'C#': "C sharp",
        u'Bb': "B flat",
        u'Eb': "E flat",
        u'Ab': "A flat",
        u'Db': "D flat",
        u'Gb': "G flat",
        u'Cb': "C flat",
        }

    parser = argparse.ArgumentParser("correct filenames and tags of music files")
    parser.add_argument('-r', '--root', action='store', default=None, dest='root', help='specify root of filesystem tree to examine (default: %s)' % cwd)
    parser.add_argument('-l', '--follow-links', action='store_true', default=False, dest='followlinks', help='follow symlinks')
    parser.add_argument('-n', '--just-testing', action='store_true', default=False, dest='testing', help='do not make changes; just display what actions would be taken')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose', help='be verbose')
    flags = parser.parse_args()

    root = root or flags.root or cwd
    os.chdir(root)

    fsencoding = sys.getfilesystemencoding()
    print("file system encoding is %s" % fsencoding)

    print("scanning %s..." % root)

    F = []
    for info in os.walk('.', topdown=True, followlinks=flags.followlinks):
        dirpath, dirnames, filenames = info

        # Prune directories and files whose names being with a dot
        for p in list(dirnames):
            if p[0] == '.':
                dirnames.remove(p)
        for fn in list(filenames):
            if fn[0] == '.':
                filenames.remove(fn)

        # Prune directories we shouldn't recurse into
        for p in prune_dirs:
            if p in dirnames:
                dirnames.remove(p)

        # Prune filenames that we know aren't music files
        for fn in prune_files:
            if fn in filenames:
                filenames.remove(fn)

        F.extend([os.path.join(dirpath, fn) for fn in filenames])

    # Examine filenames sorted order
    F.sort()

    encodings = {}
    for pathname in F:
        path, fn =  os.path.split(pathname)
        try:
            encoding = "ascii"
            unicode_filename = fn.decode(encoding)
        except UnicodeDecodeError:
            try:
                encoding = "utf8"
                unicode_filename = fn.decode(encoding)
            except UnicodeDecodeError:
                try:
                    encoding = 'iso-8859-1'
                    unicode_filename = fn.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    try:
                        encoding = 'windows-1252'
                        unicode_filename = fn.decode(encoding)
                    except:
                        chardet_info = detect(fn)
                        encoding = chardet_info.get('encoding') or 'ascii'
                        try:
                            unicode_filename = fn.decode(encoding)
                        except (UnicodeDecodeError, LookupError):
                            encoding = None
                            print("WARNING: failed to decode this filename: %s" % repr(fn))
            if encoding:
                if encoding not in encodings:
                    encodings[encoding] = unicode_filename

        # Make some helpful substitutions
        for from_string, to_string in substitutions.items():
            unicode_filename = unicode_filename.replace(from_string, to_string)

        try:
            encoded_filename = unicode_filename.encode(fsencoding)
        except UnicodeEncodeError:
            print("WARNING: could not encode %s using file system encoding %s; skipping this file" % (unicode_pathname, fsencoding))
            continue

        # Paste the correct filename onto the original path
        encoded_pathname = os.path.join(path, encoded_filename)

        # Rename if necessary
        if encoded_pathname != pathname:
            if not flags.testing:
                os.rename(pathname, encoded_pathname)
            if flags.verbose:
                print("renamed %s -> %s (detected charset: %s)" % (repr(fn), repr(encoded_filename), encoding))

    print("filename encodings found:")
    for e in sorted(encodings.keys()):
        print("%s (example: %s)" % (e, encodings[e]))
