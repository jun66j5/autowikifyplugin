# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
import unicodedata

from genshi.builder import tag
from trac.config import IntOption, ListOption
from trac.core import Component, implements
from trac.util.compat import set
from trac.wiki.api import IWikiChangeListener, IWikiSyntaxProvider, WikiParser, WikiSystem


def _init_breakable_re():
    # From trac:source:branches/0.12-stable/trac/util/text.py, introduced in
    # trac:r10539
    _breakable_char_ranges = [
        (0x1100, 0x11FF),   # Hangul Jamo
        (0x2E80, 0x2EFF),   # CJK Radicals Supplement
        (0x3000, 0x303F),   # CJK Symbols and Punctuation
        (0x3040, 0x309F),   # Hiragana
        (0x30A0, 0x30FF),   # Katakana
        (0x3130, 0x318F),   # Hangul Compatibility Jamo
        (0x3190, 0x319F),   # Kanbun
        (0x31C0, 0x31EF),   # CJK Strokes
        (0x3200, 0x32FF),   # Enclosed CJK Letters and Months
        (0x3300, 0x33FF),   # CJK Compatibility
        (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
        (0x4E00, 0x9FFF),   # CJK Unified Ideographs
        (0xA960, 0xA97F),   # Hangul Jamo Extended-A
        (0xAC00, 0xD7AF),   # Hangul Syllables
        (0xD7B0, 0xD7FF),   # Hangul Jamo Extended-B
        (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
        (0xFE30, 0xFE4F),   # CJK Compatibility Forms
        (0xFF00, 0xFFEF),   # Halfwidth and Fullwidth Forms
        (0x20000, 0x2FFFF, u'[\uD840-\uD87F][\uDC00-\uDFFF]'), # Plane 2
        (0x30000, 0x3FFFF, u'[\uD880-\uD8BF][\uDC00-\uDFFF]'), # Plane 3
    ]
    char_ranges = []
    surrogate_pairs = []
    for val in _breakable_char_ranges:
        try:
            high = unichr(val[0])
            low = unichr(val[1])
            char_ranges.append(u'%s-%s' % (high, low))
        except ValueError:
            # Narrow build, `re` cannot use characters >= 0x10000
            surrogate_pairs.append(val[2])
    char_ranges = u''.join(char_ranges)
    if surrogate_pairs:
        pattern = u'(?:[%s]|%s)+' % (char_ranges,
                                     u'|'.join(surrogate_pairs))
    else:
        pattern = u'[%s]+' % char_ranges
    return re.compile(pattern)

_breakable_re = _init_breakable_re()


class AutoWikify(Component):
    """ Automatically create links for all known Wiki pages, even those that
    are not in CamelCase. """
    implements(IWikiChangeListener, IWikiSyntaxProvider)

    exclude = ListOption('autowikify', 'exclude', doc=
        """List of Wiki pages to exclude from auto-wikification.""")
    explicitly_wikify = ListOption('autowikify', 'explicitly_wikify', doc=
        """List of Wiki pages to always Wikify, regardless of size.""")
    minimum_length = IntOption('autowikify', 'minimum_length', 3,
        """Minimum length of wiki page name to perform auto-wikification on.""")

    pages = set()
    pages_re = None

    def __init__(self):
        self._update_pages()
        self._update_pages_re()

    ### IWikiChangeListener methods

    def wiki_page_added(self, page):
        self.pages.add(page.name)
        self._update_pages_re()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass

    def wiki_page_deleted(self, page):
        if page.name in self.pages:
            self.pages.remove(page.name)
            self._update_pages_re()

    def wiki_page_renamed(self, page, old_name):
        self.pages.discard(old_name)
        self.pages.add(page.name)
        self._update_pages_re()

    def wiki_page_version_deleted(self, page):
        pass

    ### IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        if self.pages_re:
            yield (self.pages_re, self._page_formatter)

    def get_link_resolvers(self):
        return []

    ### Internal methods

    def _page_formatter(self, formatter, ns, match):
        page = match.group('autowiki')
        return tag.a(page, href=self.env.href.wiki(page), class_='wiki')

    def _update_pages(self):
        all_pages = set(WikiSystem(self.env).get_pages())
        self.pages = set([p for p in all_pages if len(p) >= self.minimum_length])
        self.pages.difference_update(self.exclude)
        explicitly_wikified = set([p.strip() for p in (self.explicitly_wikify or '') if p.strip()])
        self.pages.update(explicitly_wikified)

    def _update_pages_re(self):
        self.pages_re = self._get_pages_re(self.pages)
        # Force an update of cached WikiParser.rules
        WikiParser(self.env)._compiled_rules = None

    def _get_pages_re(self, pages):
        alnum_re = re.compile(r'\w', re.UNICODE)
        def isalnum(c):
            return alnum_re.match(c) and not _breakable_re.match(c)
        groups = [list() for i in xrange(4)]
        for page in pages:
            idx = (not isalnum(page)) * 2 + (not isalnum(page[-1])) * 1
            groups[idx].append(re.escape(page))

        fmts = [r'\b(?:%s)\b', r'\b(?:%s)', r'(?:%s)\b', r'(?:%s)']
        groups = [fmts[idx] % '|'.join(group)
                  for idx, group in enumerate(groups) if group]
        if groups:
            return '!?(?P<autowiki>%s)' % '|'.join(groups)
        else:
            return None
