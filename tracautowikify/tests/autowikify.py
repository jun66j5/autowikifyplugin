# -*- coding: utf-8 -*-

import unittest

from trac.test import EnvironmentStub

from tracautowikify.autowikify import AutoWikify


class AutoWikifyTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=[AutoWikify])
        self.autowikify = AutoWikify(self.env)

    def tearDown(self):
        self.env.reset_db()

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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AutoWikifyTestCase, 'test'))
    return suite
