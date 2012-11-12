"""Integration tests"""

from Products.CMFCore.utils import getToolByName
from Products.WebServerAuth.plugin import authenticateEverybodyKey
from Products.WebServerAuth.tests.base import MockRequestTestCase, userId


class TestIntegration(MockRequestTestCase):
    def testMemberFolderMaking(self):
        """Assert we make a member folder if that option in Plone is enabled."""
        membershipTool = getToolByName(self.portal, 'portal_membership')
        folderCreationWasOn = membershipTool.getMemberareaCreationFlag()
        if not folderCreationWasOn:
            membershipTool.setMemberareaCreationFlag()  # so we can test member-folder-making, which is off by default in Plone 3.0
        self._acl_users().validate(self.app.REQUEST)  # Fire off the whole PAS stack so our unholy member-folder-making authentication plugin runs.
        self.failUnless(membershipTool.getHomeFolder(userId), msg="Failed to make a member folder for the new user.")
    
    def testNotMemberMaking(self):
        """Assert we don't recognize nonexistent users unless we're configured to."""
        plugin = self._plugin()
        plugin.config[authenticateEverybodyKey] = False
        self.failUnlessEqual(self._acl_users().validate(self.app.REQUEST), None, msg="Should fail but doesn't: Admitted a not-created-in-Plone user, even though I was configured not to.")

    # This feature is not implemented yet.
    # def testMemberSearch(self):
    #     """Make sure auto-made members show up in searches.
    #     
    #     (Before we started setting login times, this didn't happen.)
    #     
    #     """
    #     self.acl_users.validate(self.app.REQUEST)  # mock a login so the memberdata object is created. Miraculously, the memberdata object doesn't leak out of this test.
    #     self.failUnless(len(self.acl_users.searchUsers(login=userId)) == 1, "The automatically made user didn't show up in a search.")  # searchUsers is what Plone 3.0 indirectly calls from /Members.
        
    def testGetUserById(self):
        """Make sure our enumerator makes PAS.getUserById() believe nonexistent users exist. Otherwise, we'll have a lot of trouble getting WSA-authenticated users returned from PluggableAuthService.validate()."""
        self.failIfEqual(self._acl_users().getUserById(userId), None, msg="PAS.getUserById() isn't returning the web-server-dwelling user who is logged in.")
    
    def testSearchUsers(self):
        """PAS.searchUsers() calls our enumerator exactly like getUserById(). Make sure our enumerator can distinguish."""
        self.failIf(self._acl_users().searchUsers(exact_match=True, id=userId), msg="WebServerAuth's enumeration plugin returned an item when called by searchUsers(). It shouldn't have.")
    
    def testEnumerateUsernamesWithDomains(self):
        """Make sure our wacky fake enumerator works with usernames@like.this."""
        request = self.app.REQUEST
        request.environ['HTTP_X_REMOTE_USER'] = 'fred@fred.com'
        user = self._acl_users().validate(request)
        self.failUnless(user and user.getId() == 'fred', msg="Enumerator didn't dynamically manifest a user who had a domain in his name.")

#     def testEnumeration(self):
#         """Make sure our PAS enumeration plugin spits out the users who have a member folder; that's better than nothing."""


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestIntegration))
    return suite
