from Products.CMFCore.utils import getToolByName
from Products.WebServerAuth.utils import pluginId

def loginLink(self, currentUrl):
    """Return the login link computed from the regexes selected in the defaultly installed WebServerAuth plugin."""
    return getToolByName(self, 'acl_users')[pluginId].loginUrl(currentUrl)
    # I'd use firstIdOfClass(), but this is called on every page, so I'd like to be fast.
