from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin, IUserEnumerationPlugin, IAuthenticationPlugin, IExtractionPlugin, IChallengePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.permissions import ManageUsers
from Products.WebServerAuth.utils import wwwDirectory

# Keys for storing config:
stripDomainNamesKey = 'strip_domain_names'
usernameHeaderKey = 'username_header'
autocreateUsersKey = 'auto_create_users'

# Key for PAS extraction dict:
usernameKey = 'apache_username'

defaultUsernameHeader = 'HTTP_X_REMOTE_USER'
idPrefix = 'wsa_'


class MultiPlugin(BasePlugin):
    security = ClassSecurityInfo()
    meta_type = 'WebServerAuth Plugin'
    
    ## PAS interface implementations: ############################
    
    protocol = 'http'
    security.declarePrivate('challenge')
    def challenge(self, request, response):
        if request.ACTUAL_URL.startswith('http://'):
            # Let the web server auth have a swing at it:
            response.redirect(request.ACTUAL_URL.replace('http://', 'https://', 1), lock=True)
            return True
        else:  # There's nothing more we can do.
            return False
    
    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None):
        """Grant everybody who comes in with a filled out auth header the Member role."""
        # We could just grant the role to everybody, but let's be conservative. Why not?
        if request and request.environ.get(self.config[usernameHeaderKey]) == principal.getUserName():
            return ['Member']
        else:
            return []

    security.declarePrivate('enumerateUsers')
    # Cribbed from OpenID plugin
    def enumerateUsers(self, id=None, login=None, exact_match=False, sort_by=None, max_results=None, **kw):
        """Enumerator to make ordinarily unenumerable users able to be returned from PluggableAuthService.validate().
        
        PAS doesn't seem to make an allowance for authorizing (IIRC) an existing user if that user cannot be enumerated, so we sock away a disgusting little this-is-a-fake-WSA-user token in the user ID and enumerate the user here if we find said token.
        
        """
        def normalized(id, login):
            """`id` and `login` can be strings, None, or sequences, according to IUserEnumerationPlugin. It's unspecified whether they're parallel sequences if they're sequences, but I assume they are. Return sequence-ized version of `id` and `login` which might be different lengths. None turns into [].
            """
            def toList(thing):
                if thing is None:
                    return []
                elif isinstance(thing, basestring):
                    return [thing]
                elif isinstance(thing, tuple):
                    return list(thing)  # so we can .append() to it
                else:
                    return thing
            
            id = toList(id)
            login = toList(login)
            
            # Filter out IDs and the parallel logins where the ID doesn't start with our prefix:
            x = 0
            while x < len(id):
                if not id[x].startswith(idPrefix):
                    del id[x]
                    try:
                        del login[x]
                    except IndexError:
                        pass
                else:
                    x += 1
            
            # If one of {login, id} is longer, pad it out with computed values:
            lenPrefix = len(idPrefix)
            for curId in id[len(login):]:
                login.append(curId[lenPrefix:])
            for curLogin in login[len(id):]:
                id.append('%s%s' % (idPrefix, curLogin))
            
            return id, login
            
        # If we're not auto-creating users, then don't pretend they're there:
        if self.config[autocreateUsersKey] and exact_match:  # We can't very well do inexact (wildcard) searches, since we have no user store to search. TODO: Maybe search portal_memberdata in the future.
            ids, logins = normalized(id, login)
            pluginId = self.getId()
            return [ { 'id': curId,
                       'login': curLogin,
                       'pluginid': pluginId
                    } for (curId, curLogin) in zip(ids, logins)]
        else:
            return []
    
    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """Expects credentials in the format returned by extractCredentials() below.
    
        Example:
          >>> authenticateCredentials({usernameKey: 'foobar'})
          ('web_server_auth_foobar', 'foobar')
    
        """
        def setLoginTimes(member):
            """Do what the logged_in script usually does, with regard to login times, to users after they log in."""
            # Ripped off and simplified from CMFPlone.MembershipTool.MembershipTool.setLoginTimes():
            now = self.ZopeTime()
            defaultDate = '2000/01/01'
            
            # Duplicate mysterious logic from MembershipTool.py:
            lastLoginTime = member.getProperty('login_time', defaultDate)  # In Plone 2.5, 'login_time' property is DateTime('2000/01/01') when a user has never logged in, so this default never kicks in. However, I'll assume it was in the MembershipTool code for a reason.
            if str(lastLoginTime) == defaultDate:
                lastLoginTime = now
            member.setMemberProperties({'login_time': now, 'last_login_time': lastLoginTime})

        login = credentials.get(usernameKey)
        if login is None:
            return None
        else:
            userId = '%s%s' % (idPrefix, login)
            membershipTool = getToolByName(self, 'portal_membership')
            member = membershipTool.getMemberById(userId)  # works thanks to our UserEnumerationPlugin
            if member is None:
                return None
            setLoginTimes(member)  # lets the user show up in member searches. We do this only when we first create the member. This means the login times are less accurate than in a stock Plone with form-based login, in which the times are set at each login. However, if we were to set login times at each request, that's an expensive DB write at each, and lots of ConflictErrors happen.
            membershipTool.createMemberArea(member_id=userId)
            return userId, login

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """Get credentials from a request header passed into Zope.
    
        Example:
          >>> class MockRequest:
          ...     def __init__(self, environ={}):
          ...         self.environ = environ
    
          >>> request = MockRequest({'HTTP_X_REMOTE_USER': 'foobar'})
    
          >>> handler = MultiPlugin('someId')
          >>> handler.extractCredentials(request)
          {'apache_username': 'foobar'}
    
        """
        username = request.environ.get(self.config[usernameHeaderKey])
        if not username:
            return None
        if self.config[stripDomainNamesKey] and '@' in username:
            # With some setups, the username is returned as 'user123@some.domain.name'.
            username = username.split('@', 1)[0]
        return {usernameKey: username}
    
    
    ## ZMI crap: ############################
    
    def __init__(self, id, title=None):
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
                
                autocreateUsersKey: True,
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
        self.config[autocreateUsersKey] = REQUEST.form[autocreateUsersKey] == '1'
        self.config = self.config  # Makes ZODB know something changed.
        return REQUEST.RESPONSE.redirect('%s/manage_config' % self.absolute_url())

implementedInterfaces = [IRolesPlugin, IUserEnumerationPlugin, IAuthenticationPlugin, IExtractionPlugin, IChallengePlugin]
classImplements(MultiPlugin, *implementedInterfaces)
InitializeClass(MultiPlugin)  # Make the security declarations work.
