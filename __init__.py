from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from Products.WebServerAuth.plugin import MultiPlugin
from Products.WebServerAuth.utils import wwwDirectory
from Products.WebServerAuth.zmi import manage_addWebServerAuthForm, manage_addWebServerAuth

try:
    registerMultiPlugin(MultiPlugin.meta_type)
except RuntimeError:
    # Don't explode upon re-registering the plugin:
    pass

from Products.CMFCore.DirectoryView import registerDirectory

registerDirectory('skins', globals())  # Without this, portal_skins/webserverauth shows up, but it's empty.

def initialize(context):
    # If we're running under Plone, register the GenericSetup profiles that let us replace login_form:
    try:
        from Products.GenericSetup import EXTENSION, profile_registry
        from Products.CMFPlone.interfaces import IPloneSiteRoot
    except ImportError:
        pass  # We're not running under Plone. Let the user use the PAS plugin without all the inapplicable login_form overriding.
    else:
        profile_registry.registerProfile(
            "default",
            "WebServerAuth",
            "Delegates authentication to the web server.",
            "profiles/default",
            product="Products.WebServerAuth",
            profile_type=EXTENSION,
            for_=IPloneSiteRoot)
        profile_registry.registerProfile(
            "uninstall",
            "WebServerAuth Uninstall",
            "Removes the login_form redirection.",
            "profiles/uninstall",
            product="Products.WebServerAuth",
            profile_type=EXTENSION,
            for_=IPloneSiteRoot)
    
    context.registerClass(MultiPlugin,
                          permission=add_user_folders,
                          constructors=(manage_addWebServerAuthForm,
                                        manage_addWebServerAuth),
                          visibility=None,
                          icon='%s/multiplugin.gif' % wwwDirectory
                         )
