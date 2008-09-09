"""Unit tests for authentication plugin"""

from Products.PloneTestCase import PloneTestCase
from Products.CMFCore.utils import getToolByName
from Products.WebServerAuth.utils import firstInstanceOfClass
from Products.WebServerAuth.plugin import MultiPlugin, usernameKey


class WebServerAuthTestCase(PloneTestCase.PloneTestCase):
    def _acl_users(self):
        """Return the acl_users folder in the Plone site."""
        return getToolByName(self.portal, 'acl_users')
    
    def _plugin(self):
        """Return the installed multiplugin or, if none is installed, None."""
        return firstInstanceOfClass(self._acl_users(), MultiPlugin)
