"""Unit tests for extraction plugin"""

from Products.WebServerAuth.plugin import usernameKey, defaultUsernameHeader, stripDomainNamesKey, stripWindowsDomainKey, usernameHeaderKey, cookieNameKey, cookieCheckEnabledKey
from Products.WebServerAuth.config import defaultSecretHeader, secretValueKey, secretEnabledKey
from Products.WebServerAuth.tests.base import WebServerAuthTestCase

_username = 'someUsername'
_domain = 'example.com'
_userAtDomain = '%s@%s' % (_username, _domain)
_userWinDomain = 'EXAMPLE\%s' % _username


class _MockRequest(object):
    def __init__(self, environ=None):
        self.environ = environ or {}


class TestExtraction(WebServerAuthTestCase):
    def afterSetUp(self):
        self.plugin = self._plugin()
    
    def testDefaultExtraction(self):
        """Assert default behavior of extraction works."""
        request = _MockRequest()
        self.failUnless(self.plugin.extractCredentials(request) is None, msg="Found credentials to extract, even though we shouldn't have.")
        
        request.environ[defaultUsernameHeader] = _username
        self.failUnlessEqual(self.plugin.extractCredentials(request), {usernameKey: _username})
        
        # Make sure the domain name gets stripped off the end of the username by default:
        request.environ[defaultUsernameHeader] = _userAtDomain
        self.failUnlessEqual(self.plugin.extractCredentials(request), {usernameKey: _username})
    
    def testUsernameHeaderCustomization(self):
        """Assert the name of the header in which the username is passed can be changed."""
        alternateHeader = 'HTTP_REMOTE_USER'
        request = _MockRequest(environ={alternateHeader: _username})
        self.plugin.config[usernameHeaderKey] = alternateHeader
        self.failUnlessEqual(self.plugin.extractCredentials(request), {usernameKey: _username})
    
    def testCookieCheck(self):
        """If configured to look for a cookie, check that we don't extract
        credentials if the cookie is missing."""
        
        request = _MockRequest(environ={defaultUsernameHeader: _username})
        request.cookies = {}
        
        self.plugin.config[cookieNameKey] = 'foo'
        self.plugin.config[cookieCheckEnabledKey] = True
        
        self.failUnless(self.plugin.extractCredentials(request) is None, msg="Found credentials to extract, even though we shouldn't have.")
        request.cookies['foo'] = 'bar'
        self.failUnlessEqual(self.plugin.extractCredentials(request), {usernameKey: _username})
        
    def testSharedSecret(self):
        """If configured to look for a shared secret, check that we don't extract credentials if the secret does not match."""
        secret = '123456'
        
        badRequest = _MockRequest(environ={defaultUsernameHeader: _username})
        badRequest2 = _MockRequest(environ={defaultUsernameHeader: _username, defaultSecretHeader: secret + 'X'})
        goodRequest = _MockRequest(environ={defaultUsernameHeader: _username, defaultSecretHeader: secret})
        
        self.plugin.config[secretValueKey] = secret
        self.plugin.config[secretEnabledKey] = True
        
        self.failUnless(self.plugin.extractCredentials(badRequest) is None, msg="Found credentials to extract, even though we shouldn't have.")
        self.failUnless(self.plugin.extractCredentials(badRequest2) is None, msg="Found credentials to extract, even though we shouldn't have.")
        self.failUnlessEqual(self.plugin.extractCredentials(goodRequest), {usernameKey: _username})
    
    def _testDomainStripping(self, configKey, configSetting, incomingUsername, outgoingUsername):
        """Set the `configKey` config setting to `configSetting`, and make sure the username `incomingUsername` is transformed to `outgoingUsername` upon extraction."""
        request = _MockRequest(environ={defaultUsernameHeader: incomingUsername})
        self.plugin.config[configKey] = configSetting
        self.failUnlessEqual(self.plugin.extractCredentials(request), {usernameKey: outgoingUsername})
    
    def testEmailDomainStripping(self):
        """Assert choosing to not strip the domain off the end of a whatever@here.com username works."""
        self._testDomainStripping(stripDomainNamesKey, False, _userAtDomain, _userAtDomain)
    
    def testWinDomainStrippingOff(self):
        """Assert choosing to not strip the domain off the end of a domain\user works."""
        self._testDomainStripping(stripWindowsDomainKey, False, _userWinDomain, _userWinDomain)
    
    def testWinDomainStrippingOn(self):
        """Assert choosing to strip the domain off the end of a domain\user works."""
        self._testDomainStripping(stripWindowsDomainKey, True, _userWinDomain, _username)
    
            
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestExtraction))
    return suite
