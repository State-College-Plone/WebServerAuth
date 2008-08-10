from Products.PloneTestCase import PloneTestCase
from Products.CMFCore.utils import getToolByName
from Products.WebServerAuth.utils import firstInstanceOfClass
from Products.WebServerAuth.plugin import MultiPlugin, usernameKey, defaultUsernameHeader, stripDomainNamesKey, usernameHeaderKey, authenticateEverybodyKey


PloneTestCase.installProduct('WebServerAuth')
PloneTestCase.setupPloneSite(products=['WebServerAuth'])


_username = 'someUsername'
_domain = 'example.com'
_userAtDomain = '%s@%s' % (_username, _domain)

class _MockRequest(object):
    def __init__(self, environ=None):
        self.environ = environ or {}

class TestExtraction(PloneTestCase.PloneTestCase):
    def afterSetUp(self):
        self.plugin = firstInstanceOfClass(getToolByName(self.portal, 'acl_users'), MultiPlugin)
    
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
        saveHeader = self.plugin.config[usernameHeaderKey]
        self.plugin.config[usernameHeaderKey] = alternateHeader
        try:
            self.failUnlessEqual(self.plugin.extractCredentials(request), {usernameKey: _username})
        finally:
            self.plugin.config[usernameHeaderKey] = saveHeader
    
    def testDomainStripping(self):
        """Assert choosing to not strip the domain off the end of a whatever@here.com username works."""
        request = _MockRequest(environ={defaultUsernameHeader: _userAtDomain})
        saveStrip = self.plugin.config[stripDomainNamesKey]
        self.plugin.config[stripDomainNamesKey] = False
        try:
            self.failUnlessEqual(self.plugin.extractCredentials(request), {usernameKey: _userAtDomain})
        finally:
            self.plugin.config[stripDomainNamesKey] = saveStrip
    
    def testNotMemberMaking(self):
        """Assert we don't recognize nonexistent users unless we're configured to."""
        self.app.REQUEST.set('PUBLISHED', self.portal)
        self.app.REQUEST.set('PARENTS', [self.app])
        self.app.REQUEST.steps = list(self.portal.getPhysicalPath())
        self.app.REQUEST.environ['HTTP_X_REMOTE_USER'] = _username
        
        saveAdmit = self.plugin.config[authenticateEverybodyKey]
        self.plugin.config[authenticateEverybodyKey] = False
        try:
            self.failUnlessEqual(getToolByName(self.portal, 'acl_users').validate(self.app.REQUEST), None, msg="Should fail but doesn't: Admitted a not-created-in-Plone user, even though I was configured not to.")
        finally:
            self.plugin.config[authenticateEverybodyKey] = saveAdmit


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestExtraction))
    return suite
