# This lets you install WebServerAuth through Plone, if you're into that. If you aren't using Plone, it doesn't hurt anything.

from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin, IExtractionPlugin
from Products.WebServerAuth.plugin import MultiPlugin
from Products.WebServerAuth.utils import firstIdOfClass


def install(portal):
    acl_users = getToolByName(portal, 'acl_users')
    
    # Put a WebServerAuth multiplugin in the acl_users folder, if there isn't one:
    id = firstIdOfClass(acl_users, MultiPlugin)
    if not id:
        id = 'web-server-auth'
        constructors = acl_users.manage_addProduct['WebServerAuth']  # http://wiki.zope.org/zope2/ObjectManager
        constructors.manage_addWebServerAuth(id, title='WebServerAuth Plugin')
    
    # Activate it:
    plugins = acl_users.plugins
    for interface in [IAuthenticationPlugin, IExtractionPlugin]:
        plugins.activatePlugin(interface, id)  # plugins is a PluginRegistry
 
def uninstall(portal):
    acl_users = getToolByName(portal, 'acl_users')
    id = firstIdOfClass(acl_users, MultiPlugin)
    if id:
        acl_users.manage_delObjects(ids=[id])  # implicitly deactivates
