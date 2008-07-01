from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin, IUserEnumerationPlugin, IAuthenticationPlugin, IExtractionPlugin
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


class RolesPlugin(object):
    """Grant everybody who comes in with a filled out auth header the Member role."""
    security = ClassSecurityInfo()

    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None):
        # We could just grant the role to everybody, but let's be conservative. Why not?
        if request and request.environ.get(self.config[usernameHeaderKey]) == principal.getUserName():
            import pdb;pdb.set_trace()
            return ['Member']
        else:
            return []

InitializeClass(RolesPlugin)


# Cribbed from OpenID plugin
class UserEnumerationPlugin(object):
    """Slightly evil enumerator.

    This is needed to be able to get PAS to return a user which it should
    be able to handle but who can not be enumerated.

    We do this by checking for the exact kind of call the PAS getUserById
    implementation makes.
    """
    security = ClassSecurityInfo()

    security.declarePrivate('enumerateUsers')
    def enumerateUsers(self, id=None, login=None, exact_match=False, sort_by=None, max_results=None, **kw):
        if id and login and id != login:
            return None

        if (id and not exact_match) or kw:
            return None

        key = id and id or login
        #
        # if not (key.startswith("http:") or key.startswith("https:")):
        #     return None
        # This will probably kick in too often due to the commented-out above.

        return [ {
                    "id": key,
                    "login": key,
                    "pluginid": self.getId(),
                } ]

InitializeClass(UserEnumerationPlugin)


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
        def setLoginTimes(username, membershipTool):
            """Do what the logged_in script usually does, with regard to login times, to users after they log in."""
            # Ripped off and simplified from CMFPlone.MembershipTool.MembershipTool.setLoginTimes():
            member = membershipTool.getMemberById(username)  # works thanks to our UserEnumerationPlugin
            now = self.ZopeTime()
            defaultDate = '2000/01/01'
            
            # Duplicate mysterious logic from MembershipTool.py:
            lastLoginTime = member.getProperty('login_time', defaultDate)  # In Plone 2.5, 'login_time' property is DateTime('2000/01/01') when a user has never logged in, so this default never kicks in. However, I'll assume it was in the MembershipTool code for a reason.
            if str(lastLoginTime) == defaultDate:
                lastLoginTime = now
            member.setMemberProperties({'login_time': now, 'last_login_time': lastLoginTime})

        username = credentials.get(usernameKey)
        if username is None:
            return None
        else:
            membershipTool = getToolByName(self, 'portal_membership')
            setLoginTimes(username, membershipTool)  # lets the user show up in member searches. We do this only when we first create the member. This means the login times are less accurate than in a stock Plone with form-based login, in which the times are set at each login. However, if we were to set login times at each request, that's an expensive DB write at each, and lots of ConflictErrors happen.
            membershipTool.createMemberArea(member_id=username)
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


class MultiPlugin(RolesPlugin, UserEnumerationPlugin, AuthPlugin, ExtractionPlugin, BasePlugin):
    """An aggregation of all the available apache PAS plugins."""
    security = ClassSecurityInfo()
    meta_type = 'WebServerAuth Plugin'

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

implementedInterfaces = [IRolesPlugin, IUserEnumerationPlugin, IAuthenticationPlugin, IExtractionPlugin]
classImplements(MultiPlugin, *implementedInterfaces)
InitializeClass(MultiPlugin)
