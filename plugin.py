from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin, IExtractionPlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.permissions import ManageUsers
from Products.WebServerAuth.utils import wwwDirectory

# Keys for storing config:
stripDomainNamesKey = 'strip_domain_names'
usernameHeaderKey = 'username_header'

# Key for PAS extraction dict:
usernameKey = 'apache_username'

defaultUsernameHeader = 'HTTP_X_REMOTE_USER'


class AuthPlugin(object):
    """An authentication mixin that expects credentials in the format returned by the ExtractionPlugin below

    Example:
      >>> AuthPlugin().authenticateCredentials({usernameKey: 'foobar'})
      ('foobar', 'foobar')

    """
    security = ClassSecurityInfo()

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """See IAuthenticationPlugin."""
        username = credentials.get(usernameKey)
        if username is None:
            return None
        else:
            return username, username

InitializeClass(AuthPlugin)  # Make the security declarations work.


class ExtractionPlugin(object):
    """An extraction mixin that gets credentials from a request header passed into Zope

    Example:
      >>> class MockRequest:
      ...     def __init__(self, environ={}):
      ...         self.environ = environ

      >>> request = MockRequest({'HTTP_X_REMOTE_USER': 'foobar'})

      >>> handler = MultiPlugin('someId')  # ExtractionPlugin is an abstract class, but MultiPlugin fills it out.
      >>> handler.extractCredentials(request)
      {'apache_username': 'foobar'}

    """
    security = ClassSecurityInfo()

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """See IExtractionPlugin."""
        username = request.environ.get(self.config[usernameHeaderKey])
        if not username:
            return None
        if self.config[stripDomainNamesKey] and '@' in username:
            # With some setups, the username is returned as 'user123@some.domain.name'.
            username = username.split('@', 1)[0]
        return {usernameKey: username}

InitializeClass(ExtractionPlugin)


class MultiPlugin(AuthPlugin, ExtractionPlugin, BasePlugin):
    """An aggregation of all the available apache PAS plugins."""
    security = ClassSecurityInfo()
    meta_type = 'WebServerMultiPlugin'

    def __init__(self, id, title=None):
        AuthPlugin.__init__(self)
        ExtractionPlugin.__init__(self)
        BasePlugin.__init__(self)

        self._setId(id)
        self.title = title
        self.config = {
                # It's useful to be able to turn this off for Shibboleth and
                # other federated auth systems:
                stripDomainNamesKey: True,
                
                # IISCosign insists on using HTTP_REMOTE_USER instead of
                # HTTP_X_REMOTE_USER:
                usernameHeaderKey: defaultUsernameHeader,
            }

    # A method to return the configuration page:
    security.declareProtected(ManageUsers, 'manage_config')
    manage_config = PageTemplateFile('config.pt', wwwDirectory)

    # Add a tab that calls that method:
    manage_options = ({'label': 'Options',
                       'action': 'manage_config'},) + BasePlugin.manage_options

    security.declareProtected(ManageUsers, 'getConfig')
    def getConfig(self):
        """Return a mapping of my configuration values, for use in a page
        template."""
        return self.config

    security.declareProtected(ManageUsers, 'manage_changeConfig')
    def manage_changeConfig(self, REQUEST=None):
        """Update my configuration based on form data."""
        self.config[stripDomainNamesKey] = REQUEST.form.get(stripDomainNamesKey) == '1'  # Don't raise an exception; unchecked checkboxes don't get submitted.
        self.config[usernameHeaderKey] = REQUEST.form[usernameHeaderKey]
        self.config = self.config  # Makes ZODB know something changed.
        return REQUEST.RESPONSE.redirect('%s/manage_config' % self.absolute_url())

classImplements(MultiPlugin, IAuthenticationPlugin, IExtractionPlugin)
InitializeClass(MultiPlugin)
