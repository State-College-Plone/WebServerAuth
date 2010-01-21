"""Unit tests for challenge plugin"""

import re
from Products.WebServerAuth.config import useCustomRedirectionKey, challengePatternKey, challengeReplacementKey, challengeHeaderEnabledKey, defaultChallengeHeader
from Products.WebServerAuth.tests.base import MockRequestTestCase


class ChallengeTestCase(MockRequestTestCase):
    def afterSetUp(self):
        super(ChallengeTestCase, self).afterSetUp()
        self.app.REQUEST.set('ACTUAL_URL', 'http://example.com/some/place')


class TestChallenge(ChallengeTestCase):
    def testDefaultPattern(self):
        """Make sure the default regex works."""
        worked = self._plugin().challenge(self.app.REQUEST, self.app.REQUEST.response)
        self.failUnlessEqual(self.app.REQUEST.response.getHeader('Location'), 'https://example.com/some/place')
        self.failUnless(worked, msg="Challenge handler did the redirect but then passed control to the next challenge handler.")

    def testChallengeHeaderPresent(self):
        """Make sure challenge still happens when the header is present but the checkbox is off."""
        req = self.app.REQUEST
        old_environ = req.environ.copy()  # REQUEST.clone() doesn't copy ACTUAL_URL, so we'll do it ourselves
        try:
            req.environ[defaultChallengeHeader] = 'anything at all'
            challenged = self._plugin().challenge(req, req.response)
            self.failUnless(challenged, "Challenge didn't happen when the %s header was present, even though the challenge_header_name checkbox was off." % defaultChallengeHeader)
        finally:
            req.environ = old_environ
    
    def testChallengeHeaderAbsent(self):
        """Make sure challenge doesn't happen when the header is absent but the checkbox is on."""
        plugin = self._plugin()
        plugin.config[challengeHeaderEnabledKey] = True
        challenged = plugin.challenge(self.app.REQUEST, self.app.REQUEST.response)
        self.failIf(challenged, "Challenge happened even though the challenge header was absent.")


class TestCustomChallenge(ChallengeTestCase):
    """Challenge handler tests with custom regexes on"""
    
    def afterSetUp(self):
        super(TestCustomChallenge, self).afterSetUp()
        self._plugin().config[useCustomRedirectionKey] = True
    
    def testCustomPattern(self):
        """Make sure custom regexes work."""
        self._plugin().challenge(self.app.REQUEST, self.app.REQUEST.response)
        self.failUnlessEqual(self.app.REQUEST.response.getHeader('Location'), 'https://secure.example.com/some-site/some/place')
    
    def testBadCustomPattern(self):
        """Make sure bad custom regexes fail gracefully."""
        plugin = self._plugin()
        plugin.config[challengePatternKey] = re.compile('http://example.com/some-crap-that-doesnt-match')
        worked = plugin.challenge(self.app.REQUEST, self.app.REQUEST.response)
        self.failIf(worked, msg="A nonmatching custom challenge regex made the challenge handler succeed.")
    
    def testBadCustomReplacement(self):
        """Make sure bad custom replacement patterns fail gracefully."""
        plugin = self._plugin()
        plugin.config[challengeReplacementKey] = r'https://\1\2'
        worked = plugin.challenge(self.app.REQUEST, self.app.REQUEST.response)
        self.failIf(worked, msg="A bad custom replacement pattern made the challenge handler succeed.")


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestChallenge))
    suite.addTest(makeSuite(TestCustomChallenge))
    return suite
