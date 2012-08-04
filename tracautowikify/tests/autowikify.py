# -*- coding: utf-8 -*-

import unittest

from genshi.core import Markup

from trac.mimeview.api import Context
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.web.href import Href
from trac.wiki.formatter import format_to_oneliner
from trac.wiki.model import WikiPage

from tracautowikify.autowikify import AutoWikify


class AutoWikifyTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=[AutoWikify])
        self.req = Mock(
            authname='anonymous', perm=MockPerm(), tz=None, args={},
            href=Href('/'), abs_href=Href('http://www.example.com/'))
        self.autowikify = AutoWikify(self.env)

        for name in (u'autowikify', u'あいうName', u'Nameあいう',
                     u'かきくけこ'):
            page = WikiPage(self.env, name)
            page.text = name
            page.save('admin', '', '::1')
        self.context = Context.from_request(self.req, WikiPage(self.env, name))

    def tearDown(self):
        self.env.reset_db()

    def format_to_oneliner(self, wikidom):
        return format_to_oneliner(self.env, self.context, wikidom)

    def test_pages_re(self):
        self.assertEqual(None, self.autowikify._get_pages_re([]))
        self.assertEqual(
            ur'!?(?P<autowiki>\b(?:WikiStart|TracWiki)\b)',
            self.autowikify._get_pages_re([u'WikiStart', u'TracWiki']))
        self.assertEqual(
            ur'!?(?P<autowiki>\b(?:WikiStart|\ÅbcWiki)\b)',
            self.autowikify._get_pages_re([u'WikiStart', u'ÅbcWiki']))
        self.assertEqual(
                ur'!?(?P<autowiki>'
                ur'\b(?:WikiStart|TracWiki)\b|'
                ur'\b(?:Wiki\履\歴)|'
                ur'(?:\履\歴Log)\b|'
                ur'(?:\履\歴))',
            self.autowikify._get_pages_re([
                u'WikiStart', u'TracWiki', u'Wiki履歴', u'履歴Log', u'履歴']))

    def test_format(self):
        self.assertEqual(
            Markup(u'This plugin is <a class="wiki" '
                   u'href="/wiki/autowikify">autowikify</a>.'),
            self.format_to_oneliner(u'This plugin is autowikify.'))

    def test_format_cjk_name(self):
        self.assertEqual(
            Markup(
                u'Wiki'
                u'<a class="wiki" href="/wiki/%E3%81%82%E3%81%84%E3%81%86Name">あいうName</a>'
                u' '
                u'<a class="wiki" href="/wiki/Name%E3%81%82%E3%81%84%E3%81%86">Nameあいう</a>'
                u'Ａ'
                u'<a class="wiki" href="/wiki/%E3%81%8B%E3%81%8D%E3%81%8F%E3%81%91%E3%81%93">かきくけこ</a>'
                u'abc'),
            self.format_to_oneliner(
                u'WikiあいうName NameあいうＡかきくけこabc'))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AutoWikifyTestCase, 'test'))
    return suite
