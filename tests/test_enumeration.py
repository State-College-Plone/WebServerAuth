from Products.PloneTestCase import PloneTestCase
from Products.CMFCore.utils import getToolByName
from Products.WebServerAuth.utils import firstInstanceOfClass
from Products.WebServerAuth.plugin import MultiPlugin


PloneTestCase.installProduct('WebServerAuth')
PloneTestCase.setupPloneSite(products=['WebServerAuth'])


# TODO: Don't bother subclassing PloneTestCase for this simple unit test.
class TestEnumeration(PloneTestCase.PloneTestCase):
    def afterSetUp(self):
        self.plugin = firstInstanceOfClass(getToolByName(self.portal, 'acl_users'), MultiPlugin)
    
    def testNonexistent(self):
        """Make sure nonexistent users show up in searches like the Sharing tab does."""
        self.failUnless(self.plugin.enumerateUsers(id='zxq756', exact_match=True)[0]['id'] == 'zxq756', msg="Nonexistent users aren't being enumerated.")


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestEnumeration))
    return suite
