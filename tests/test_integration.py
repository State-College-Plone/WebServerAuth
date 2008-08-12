"""Integration tests"""

from Products.PloneTestCase import PloneTestCase
from Products.CMFCore.utils import getToolByName
from Products.WebServerAuth.plugin import MultiPlugin, authenticateEverybodyKey
from Products.WebServerAuth.utils import firstInstanceOfClass

PloneTestCase.installProduct('WebServerAuth')
PloneTestCase.setupPloneSite(products=['WebServerAuth'])

_userId = 'fred'

class TestIntegration(PloneTestCase.PloneTestCase):
    def afterSetUp(self):
        def getMockRequest():
            """Return a request that looks like we traversed to the root of the Plone site."""
            old_parents = self.app.REQUEST.get('PARENTS')
            self.app.REQUEST.set('PARENTS', [self.app])  # make clone() work
            request = self.app.REQUEST.clone()
            self.app.REQUEST.set('PARENTS', old_parents)
            
            request.set('PUBLISHED', self.portal)
            request.steps = list(self.portal.getPhysicalPath())
            request.environ['HTTP_X_REMOTE_USER'] = _userId
            return request
            
        self.logout()
        self.acl_users = getToolByName(self.portal, 'acl_users')
        
        # Rig the REQUEST that looks like we traversed to the root of the Plone site:
        self.old_request = self.app.REQUEST
        self.app.REQUEST = getMockRequest()
    
    def beforeTearDown(self):
        self.app.REQUEST = self.old_request
    
    def _plugin(self):
        return firstInstanceOfClass(self.acl_users, MultiPlugin)
    
    def testMemberFolderMaking(self):
        """Assert we make a member folder if that option in Plone is enabled."""
        membershipTool = getToolByName(self.portal, 'portal_membership')
        folderCreationWasOn = membershipTool.getMemberareaCreationFlag()
        if not folderCreationWasOn:
            membershipTool.setMemberareaCreationFlag()  # so we can test member-folder-making, which is off by default in Plone 3.0
        try:
            self.acl_users.validate(self.app.REQUEST)  # Fire off the whole PAS stack so our unholy member-folder-making authentication plugin runs.
        finally:  # Put things back as we found them.
            if not folderCreationWasOn:
                membershipTool.setMemberareaCreationFlag()
        self.failUnless(membershipTool.getHomeFolder(_userId), msg="Failed to make a member folder for the new user.")
    
    def testNotMemberMaking(self):
        """Assert we don't recognize nonexistent users unless we're configured to."""
        plugin = self._plugin()
        saveAdmit = plugin.config[authenticateEverybodyKey]
        plugin.config[authenticateEverybodyKey] = False
        try:
            self.failUnlessEqual(self.acl_users.validate(self.app.REQUEST), None, msg="Should fail but doesn't: Admitted a not-created-in-Plone user, even though I was configured not to.")
        finally:
            plugin.config[authenticateEverybodyKey] = saveAdmit

    # This feature is not implemented yet.
    # def testMemberSearch(self):
    #     """Make sure auto-made members show up in searches.
    #     
    #     (Before we started setting login times, this didn't happen.)
    #     
    #     """
    #     self.acl_users.validate(self.app.REQUEST)  # mock a login so the memberdata object is created. Miraculously, the memberdata object doesn't leak out of this test.
    #     self.failUnless(len(self.acl_users.searchUsers(login=_userId)) == 1, "The automatically made user didn't show up in a search.")  # searchUsers is what Plone 3.0 indirectly calls from /Members.
        
    def testGetUserById(self):
        """Make sure PAS.getUserById() thinks nonexistent users exist. Otherwise, we'll have a lot of trouble getting WSA-authenticated users returned from PluggableAuthService.validate()."""
        self.failIfEqual(self._plugin().getUserById(_userId), None, msg="PAS.getUserById() isn't returning the web-server-dwelling user who is logged in.")
        
#     def testEnumeration(self):
#         """Make sure our PAS enumeration plugin spits out the users who have a member folder; that's better than nothing."""


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestIntegration))
    return suite
