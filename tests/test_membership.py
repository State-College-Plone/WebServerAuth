"""Test the stuff that goes beyond simple PAS user functionality and into Plone membership."""

from Products.PloneTestCase import PloneTestCase
from Products.CMFCore.utils import getToolByName


PloneTestCase.installProduct('WebServerAuth')
PloneTestCase.setupPloneSite(products=['WebServerAuth'])

_userId = 'fred'

class TestMembership(PloneTestCase.PloneTestCase):
    def afterSetUp(self):
        self.logout()
        self.membershipTool = getToolByName(self.portal, 'portal_membership')
        self.acl_users = getToolByName(self.portal, 'acl_users')
            
        # Rig the REQUEST so it looks like we traversed to the root of the Plone site:
        old_parents = self.app.REQUEST.get('PARENTS')
        self.app.REQUEST.set('PARENTS', [self.app])
        request = self.request = self.app.REQUEST.clone()
        self.app.REQUEST.set('PARENTS', old_parents)
        
        request.set('PUBLISHED', self.portal)
        request.steps = list(self.portal.getPhysicalPath())
        request.environ['HTTP_X_REMOTE_USER'] = _userId
    
    def testMemberRole(self):
        """Assert we grant Member role to users."""
        user = self.acl_users.validate(self.request)
        self.failUnless(user.has_role('Member'), msg="Failed to grant the Member role to the user I made.")
    
    def testMemberFolderMaking(self):
        """Assert we make a member folder if that option in Plone is enabled."""
        folderCreationWasOn = self.membershipTool.getMemberareaCreationFlag()
        if not folderCreationWasOn:
            self.membershipTool.setMemberareaCreationFlag()  # so we can test member-folder-making, which is off by default in Plone 3.0
        try:
            user = self.acl_users.validate(self.request)  # Fire off the whole PAS stack so our unholy member-folder-making authentication plugin runs.
        finally:  # Put things back as we found them.
            if not folderCreationWasOn:
                self.membershipTool.setMemberareaCreationFlag()
        self.failUnless(self.membershipTool.getHomeFolder(_userId), msg="Failed to make a member folder for the new user.")
    
    def testMemberSearch(self):
        """Make sure auto-made members show up in searches.
        
        (Before we started setting login times, this didn't happen.)
        
        """
        self.failUnless(len(self.acl_users.searchUsers(login=_userId)) == 1, "The automatically made user didn't show up in a search.")  # searchUsers is what Plone 3.0 indirectly calls from /Members.
        
#     def testEnumeration(self):
#         """Make sure our PAS enumeration plugin spits out the users who have a member folder; that's better than nothing."""


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMembership))
    return suite
