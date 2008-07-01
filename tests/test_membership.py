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
        # TODO: Does this leak out of this testcase?
        self.app.REQUEST.set('PUBLISHED', self.portal)
        self.app.REQUEST.set('PARENTS', [self.app])
        self.app.REQUEST.steps = list(self.portal.getPhysicalPath())
        self.app.REQUEST.environ['HTTP_X_REMOTE_USER'] = _userId
    
    def testMemberRole(self):
        """Assert we grant Member role to users."""
        user = self.acl_users.validate(self.app.REQUEST)
        self.failUnless(user.has_role('Member'), msg="Failed to grant the Member role to the user I made.")
    
    def testMemberFolderMaking(self):
        """Assert we make a member folder if that option in Plone is enabled."""
        folderCreationWasOn = self.membershipTool.getMemberareaCreationFlag()
        if not folderCreationWasOn:
            self.membershipTool.setMemberareaCreationFlag()  # so we can test member-folder-making, which is off by default in Plone 3.0
        try:
            user = self.acl_users.validate(self.app.REQUEST)  # Fire off the whole PAS stack so our unholy member-making authentication plugin runs.
        finally:  # Put things back as we found them.
            if not folderCreationWasOn:
                self.membershipTool.setMemberareaCreationFlag()
        self.failUnless(self.membershipTool.getHomeFolder(_userId), msg="Failed to make a member folder for the new user.")
        
#     def testEnumeration(self):
#         """Make sure our PAS enumeration plugin spits out the users who have a member folder; that's better than nothing."""


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMembership))
    return suite
