from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.WebServerAuth.plugin import MultiPlugin, implementedInterfaces
from Products.WebServerAuth.utils import firstIdOfClass
from Products.WebServerAuth.portlets import LoginPortletRenderer


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
    
    # Make the Challenge plugin the first in the list:
    for i in range(list(plugins.listPluginIds(IChallengePlugin)).index(id)):
        plugins.movePluginsUp(IChallengePlugin, [id])
    
    # Set up login and logout links:
    user_actions = getToolByName(portal, 'portal_actions')['user']
    user_actions['login']._updateProperty('url_expr', "python:request.ACTUAL_URL.replace('http://', 'https://', 1)")
    
    # Hide the Login portlet:
#     import pdb;pdb.set_trace()
#     wsa_login_portlet = getMultiAdapter()
#     sm = portal.getSiteManager()
#     sm.registerAdapter(wsa_login_portlet, name='portlets.LoginThatNeverShowsUp')
    
    
def uninstall(portal):
    # Delete the multiplugin instance:
    acl_users = getToolByName(portal, 'acl_users')
    id = firstIdOfClass(acl_users, MultiPlugin)
    if id:
        acl_users.manage_delObjects(ids=[id])  # implicitly deactivates
    
    # Revert login and logout links to their stock settings:
    user_actions = getToolByName(portal, 'portal_actions')['user']
    user_actions['login']._updateProperty('url_expr', "string:${portal_url}/login_form")
    
    # Put the Login portlet back how it was:
    #sm = portal.getSiteManager()
    #sm.unregisterAdapter(ILoginPortlet, name='portlets.Login')
