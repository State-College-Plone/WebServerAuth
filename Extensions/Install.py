from OFS.Folder import manage_addFolder
from Products.CMFCore.utils import getToolByName
from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.WebLionLibrary.skins import deleteLayers
from Products.WebServerAuth.plugin import MultiPlugin, implementedInterfaces
from Products.WebServerAuth.utils import firstIdOfClass, pluginId

_externalMethodsFolderId = 'webserverauth_external_methods'

def install(portal):
    acl_users = getToolByName(portal, 'acl_users')
    
    # Put a WebServerAuth multiplugin in the acl_users folder, if there isn't one:
    id = firstIdOfClass(acl_users, MultiPlugin)
    if not id:
        id = pluginId
        constructors = acl_users.manage_addProduct['WebServerAuth']  # http://wiki.zope.org/zope2/ObjectManager
        constructors.manage_addWebServerAuth(id, title='WebServerAuth Plugin')
    
    # Activate it:
    plugins = acl_users.plugins
    for interface in implementedInterfaces:
        plugins.activatePlugin(interface, id)  # plugins is a PluginRegistry
    
    # Make the Challenge plugin the first in the list:
    for i in range(list(plugins.listPluginIds(IChallengePlugin)).index(id)):
        plugins.movePluginsUp(IChallengePlugin, [id])
    
    # Set up login link:
    ## Install external method:
    skinsTool = getToolByName(portal, 'portal_skins')
    manage_addFolder(skinsTool, _externalMethodsFolderId)
    manage_addExternalMethod(skinsTool[_externalMethodsFolderId], 'webserverauth_login_url', 'webserverauth_login_url', 'WebServerAuth.login_link', 'loginLink')
    setupTool = getToolByName(portal, 'portal_setup')
    setupTool.runAllImportStepsFromProfile('profile-Products.WebServerAuth:default')
    ## Frob login link:    
    user_actions = getToolByName(portal, 'portal_actions')['user']
    user_actions['login']._updateProperty('url_expr', "python:here.webserverauth_login_url(request.ACTUAL_URL)")
    
def uninstall(portal):
    # Delete the multiplugin instance:
    acl_users = getToolByName(portal, 'acl_users')
    id = firstIdOfClass(acl_users, MultiPlugin)
    if id:
        acl_users.manage_delObjects(ids=[id])  # implicitly deactivates
    
    # Revert login link to its stock setting:
    user_actions = getToolByName(portal, 'portal_actions')['user']
    user_actions['login']._updateProperty('url_expr', "string:${portal_url}/login_form")
    setupTool = getToolByName(portal, 'portal_setup')
    setupTool.runAllImportStepsFromProfile('profile-Products.WebServerAuth:uninstall')
    skinsTool = getToolByName(portal, 'portal_skins')
    deleteLayers(skinsTool, [_externalMethodsFolderId])
