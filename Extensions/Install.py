from Products.CMFCore.utils import getToolByName
from Products.WebServerAuth.plugin import MultiPlugin, implementedInterfaces
from Products.WebServerAuth.utils import firstIdOfClass


def install(portal):
    acl_users = getToolByName(portal, 'acl_users')
    
    # Put a WebServerAuth multiplugin in the acl_users folder, if there isn't one:
    id = firstIdOfClass(acl_users, MultiPlugin)
    if not id:
        id = 'web_server_auth'
        constructors = acl_users.manage_addProduct['WebServerAuth']  # http://wiki.zope.org/zope2/ObjectManager
        constructors.manage_addWebServerAuth(id, title='WebServerAuth Plugin')
    
    # Activate it:
    plugins = acl_users.plugins
    for interface in implementedInterfaces:
        plugins.activatePlugin(interface, id)  # plugins is a PluginRegistry
 
def uninstall(portal):
    acl_users = getToolByName(portal, 'acl_users')
    id = firstIdOfClass(acl_users, MultiPlugin)
    if id:
        acl_users.manage_delObjects(ids=[id])  # implicitly deactivates
