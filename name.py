#
# Correct and simplify filenames. Autodetects the encoding of each
# name and converts it to either UTF-8 or ASCII. Removes probelmatic
# characters from filenames.
#
# dmb 24-Feb-2013
#
import sys
import os
import codecs
from chardet import detect

class Skip(Exception): pass

class fixer(object):
    "Correct and simplify filenames."
    DEFAULT_PRUNE_DIRS = ['.AppleDouble']
    DEFAULT_PRUNE_FILES = ['.DS_Store']
    DEFAULT_SUBSTITUTIONS = {
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

    def __init__(self, strip_diacritics=False, encoding='utf8', follow_links=True, prune_dirs=None, prune_files=None, substitutions=None):
        self.strip_diacritics = strip_diacritics
        self.encoding = encoding
        self.follow_links = follow_links
        self.prune_dirs = prune_dirs or self.DEFAULT_PRUNE_DIRS
        self.prune_files = prune_files or self.DEFAULT_PRUNE_FILES
        self.substitutions = substitutions or self.DEFAULT_SUBSTITUTIONS
        self.fsencoding = sys.getfilesystemencoding()
        print("file system encoding is %s" % self.fsencoding)

    def fix(self, root, testing=False, verbose=False):
        cwd = os.getcwd()
        os.chdir(root)
        try:
            return self._fix(root, testing=testing, verbose=verbose)
        finally:
            os.chdir(cwd)
    
    def _fix(self, root, testing=False, verbose=False):
        self.encodings = {}
        self.testing = testing
        self.verbose = verbose

        for info in os.walk('.', topdown=True, followlinks=self.follow_links):
            #
            # dirpath: the directory the walker is currently in
            # dirnames: names of subdirectories within this directory
            # filenames: names of files within this directory
            #
            dirpath, dirnames, filenames = info
            #print("dipath = %s, dirnames = %s, filenames = %s" % (repr(dirpath), repr(dirnames), repr(filenames)))

            # Prune directories and files whose names being with a dot
            for names in (dirnames, filenames):
                for name in list(names):
                    if name[0] == '.':
                        names.remove(name)

            # Prune directories we shouldn't recurse into
            for p in self.prune_dirs:
                if p in dirnames:
                    dirnames.remove(p)

            # Prune filenames that we know aren't music files
            for fn in self.prune_files:
                if fn in filenames:
                    filenames.remove(fn)

            # Rename subdirectories, then files
            for names in (dirnames, filenames):
                for name in names:
                    try:
                        encoded_name = self._fix_name(name)
                    except Skip:
                        # couldn't fix for some reason; skip
                        pass
                    
                    # Rename if necessary
                    if encoded_name != name:
                        if not self.testing:
                            cwd = os.getcwd()
                            os.chdir(dirpath)
                            try:
                                os.rename(name, encoded_name)
                            finally:
                                os.chdir(cwd)
                        if self.verbose:
                            print("renamed %s -> %s (detected charset: %s)" % 
                                  (repr(name), repr(encoded_name), self.detected_encoding))

    def _fix_name(self, name):
        try:
            self.detected_encoding = "ascii"
            unicode_filename = name.decode(self.detected_encoding)
        except UnicodeDecodeError:
            try:
                self.detected_encoding = "utf8"
                unicode_filename = name.decode(self.detected_encoding)
            except UnicodeDecodeError:
                try:
                    self.detected_encoding = 'iso-8859-1'
                    unicode_filename = name.decode(self.detected_encoding)
                except (UnicodeDecodeError, LookupError):
                    try:
                        self.detected_encoding = 'windows-1252'
                        unicode_filename = name.decode(self.detected_encoding)
                    except:
                        chardet_info = detect(name)
                        self.detected_encoding = chardet_info.get('self.detected_encoding') or 'ascii'
                        try:
                            unicode_filename = name.decode(self.detected_encoding)
                        except (UnicodeDecodeError, LookupError):
                            self.detected_encoding = None
                            print("WARNING: failed to decode this filename: %s" % repr(name))
            if self.detected_encoding:
                if self.detected_encoding not in self.encodings:
                    self.encodings[self.detected_encoding] = unicode_filename

        # Make some helpful substitutions
        for from_string, to_string in self.substitutions.items():
            unicode_filename = unicode_filename.replace(from_string, to_string)

        # Strip diacritics if so requested
        if self.strip_diacritics:
            unicode_filename = self._strip_diacritics(unicode_filename)

        #
        # Now downgrade filename to use only chars in the desired
        # self.detected_encoding (e.g., ASCII), then convert back into Unicode.
        #
        if self.detected_encoding != 'utf8':
            unicode_filename = unicode_filename.encode(self.encoding, 'replace').decode(self.encoding)

        # Now encode Unicode filename into destination file system charset.
        try:
            encoded_filename = unicode_filename.encode(self.fsencoding)
        except UnicodeEncodeError:
            print("WARNING: could not encode %s using file system encoding %s; skipping this file" % (unicode_pathname, self.fsencoding))
            raise Skip()

        return encoded_filename

    def report(self):
        "Report stats about the last fix."
        print("filename encodings found:")
        for e in sorted(self.encodings.keys()):
            print("%s (example: %s)" % (e, self.encodings[e]))

    @staticmethod
    def _strip_diacritics(s):
        from unicodedata import normalize, category
        return u''.join(
            (c for c in normalize('NFD', s) 
             if category(c) != 'Mn')
            )
