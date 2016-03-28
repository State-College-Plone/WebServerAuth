import inspect
import logging
import re

from AccessControl import ClassSecurityInfo
try:
    from AccessControl.class_init import InitializeClass # Zope >=2.13
except:
    try:
        from App.class_init import InitializeClass # Zope>=2.11.13 and Zope>=2.10.8
    except:
        from Globals import InitializeClass # Zope <2.10.8 and <2.11.13
from persistent.dict import PersistentDict
from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin, IAuthenticationPlugin, IExtractionPlugin, IChallengePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.permissions import ManageUsers

from Products.WebServerAuth.utils import wwwDirectory
from Products.WebServerAuth.config import configDefaults, configDefaults1_1, configDefaults1_5, configDefaults1_6, configDefaults1_7, defaultChallengePattern, defaultChallengeReplacement, stripDomainNamesKey, stripWindowsDomainKey, usernameHeaderKey, authenticateEverybodyKey, useCustomRedirectionKey, challengePatternKey, challengeReplacementKey, cookieCheckEnabledKey, cookieNameKey, challengeHeaderEnabledKey, challengeHeaderNameKey, defaultUsernameHeader, secretHeaderKey, secretValueKey, secretEnabledKey, forceLowercaseUsernamesKey

try:
    from plone.protect.interfaces import IDisableCSRFProtection
except:
    IDisableCSRFProtection = None
from zope.interface import alsoProvides


# Key for PAS extraction dict:
usernameKey = 'apache_username'

logger = logging.getLogger('Products.WebServerAuth')


class MultiPlugin(BasePlugin):
    security = ClassSecurityInfo()
    meta_type = 'WebServerAuth Plugin'
    ## PAS interface implementations: ############################

    security.declarePublic('loginUrl')
    def loginUrl(self, currentUrl):
        """Given the URL of the page where the user presently is, return the URL which will prompt him for authentication and land him at the same place.

        If something goes wrong, return ''.

        """
        usingCustomRedirection = self.config[useCustomRedirectionKey]
        pattern, replacement = usingCustomRedirection and (self.config[challengePatternKey], self.config[challengeReplacementKey]) or (defaultChallengePattern, defaultChallengeReplacement)
        match = pattern.match(currentUrl)
        # Let the web server's auth have a swing at it:
        if match:  # will usually start with http:// but may start with https:// (and thus not match) if you're already logged in and try to access something you're not privileged to
            try:
                destination = match.expand(replacement)
            except re.error:  # Don't screw up your replacement string, please. If you do, we at least try not to punish the user with a traceback.
                if usingCustomRedirection:
                    logger.error("Your custom WebServerAuth Replacement Pattern could not be applied to a URL which needs authentication: %s. Please correct it." % currentUrl)
            else:
                return destination
        # Our regex didn't match, or something went wrong.
        return ''

    protocol = 'http'
    security.declarePrivate('challenge')
    def challenge(self, request, response):
        config = self.config
        if config[challengeHeaderEnabledKey]:
            if request.get_header(config[challengeHeaderNameKey]) is None:
                return False

        url = self.loginUrl(request.ACTUAL_URL)
        if url:
            response.redirect(url, lock=True)
            return True
        else:  # Pass off control to the next challenge plugin.
            return False

    security.declarePrivate('enumerateUsers')
    # Inspired by the OpenID plugin
    def enumerateUsers(self, id=None, login=None, exact_match=False, sort_by=None, max_results=None, **kw):
        """Evil, layer-violating enumerator to get the logged in user, though unenumerable, to be validatable.

        PAS doesn't seem to make an allowance for authorizing (IIRC) an existing user if that user cannot be enumerated, so we try to guess who's calling and make that happen.

        """
        # Unless we're admitting non-Plone-dwelling users, don't pretend the user is there. Also, don't enumerate unless we seem to have been called by getUserById(). We're very conservative, even checking the types of things like exact_match. Also also, don't enumerate unless we're searching for the currently logged in user. Heck, we even look at the stack now, because searchUsers() (as called by searchPrincipals()) calls us the same way getUserById() does.
        if self.config[authenticateEverybodyKey] and (id is not None and login is None and exact_match is True and sort_by is None and max_results is None and not kw) and (self.REQUEST and self._normalizedLoginName(self.REQUEST.environ.get(self.config[usernameHeaderKey])) == id):  # may be redundant with the stack inspection below, but it makes me feel warm and fuzzy for now
            stack = inspect.stack()
            try:
                calledByGetUserById = stack[2][3] == 'getUserById'  # getUserById calls _verifyUser, which calls us
            finally:
                del stack  # Dispose of frames, as recommended by http://docs.python.org/lib/inspect-stack.html
            if calledByGetUserById:
                return [ {
                            "id": id,
                            "login": id,
                            "pluginid": self.getId()
                        } ]
        return []

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """Expects a login name in the form returned by extractCredentials() below.

        Example:
          >>> authenticateCredentials({usernameKey: 'foobar'})
          ('foobar', 'foobar')

        """
        defaultDate = '2000/01/01'
        def setLoginTimes(member):
            """Do what the logged_in script usually does, with regard to login times, to users after they log in."""
            # Ripped off and simplified from CMFPlone.MembershipTool.MembershipTool.setLoginTimes():
            now = self.ZopeTime()

            # Duplicate mysterious logic from MembershipTool.py:
            lastLoginTime = member.getProperty('login_time', defaultDate)  # In Plone 2.5, 'login_time' property is DateTime('2000/01/01') when a user has never logged in, so this default never kicks in. However, I'll assume it was in the MembershipTool code for a reason.
            if str(lastLoginTime) == defaultDate:
                lastLoginTime = now
            member.setMemberProperties({'login_time': now, 'last_login_time': lastLoginTime})

        login = credentials.get(usernameKey)
        if login is None:
            return None
        else:
            user = self._getPAS().getUser(login)  # Our enumerator doesn't respond to getUser() calls.
            userId = user and user.getId() or login

            membershipTool = getToolByName(self, 'portal_membership', default=None)
            if membershipTool is not None:  # Tolerate running in plain Zope, sans Plone.
                member = membershipTool.getMemberById(userId)  # works thanks to our UserEnumerationPlugin  # implicitly creates the record in portal_memberdata, at least when authenticate_everybody is on: see memberdata.py:67

                if member is None:  # happens only when authenticate_everybody is off
                    return None

                if IDisableCSRFProtection is not None:
                    alsoProvides(self.REQUEST, IDisableCSRFProtection)

                if str(member.getProperty('login_time')) == defaultDate:  # This member has never had his login time set; he's never logged in before.
                    setLoginTimes(member)  # lets the user show up in member searches. We do this only when the member record is first created. This means the login times are less accurate than in a stock Plone with form-based login, in which the times are set at each login. However, if we were to set login times at each request, that's an expensive DB write at each, and lots of ConflictErrors happen. The real answer is for somebody (Plone or PAS) to fire an event when somebody logs in.
                membershipTool.createMemberArea(member_id=userId)
            return userId, login

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """Get login name from a request header passed into Zope.

        Example:
          >>> class MockRequest:
          ...     def __init__(self, environ={}):
          ...         self.environ = environ

          >>> request = MockRequest({'HTTP_X_REMOTE_USER': 'foobar'})

          >>> handler = MultiPlugin('someId')
          >>> handler.extractCredentials(request)
          {'apache_username': 'foobar'}

        """

        # Do not extract credentials if we are configured to expect a cookie
        # but it is not found.
        if self.config[cookieCheckEnabledKey]:
            cookieName = self.config[cookieNameKey]
            if cookieName and cookieName not in request.cookies:
                return None

        # Do not extract credentials if a secret matching is enabled, but not matched.
        if self.config[secretEnabledKey]:
            secret = request.environ.get(self.config[secretHeaderKey])
            if secret != self.config[secretValueKey]:
                return None

        login = request.environ.get(self.config[usernameHeaderKey])
        if not login:
            return None
        return {usernameKey: self._normalizedLoginName(login)}


    ## Helper methods: ############################

    security.declarePrivate('_normalizedLoginName')
    def _normalizedLoginName(self, login):
        """Given a raw login name, return it modified according to the "Strip domain names from usernames" preference."""
        if login is not None:
            if self.config[stripDomainNamesKey] and '@' in login:
                # With some setups, the login name is returned as 'user123@some.domain.name'.
                login = login.split('@', 1)[0]
            elif self.config[stripWindowsDomainKey] and '\\' in login:
                # Active Directory user expressions have exactly 1 backslash.
                login = login.split('\\', 1)[1]
            if self.config[forceLowercaseUsernamesKey]:
                login = login.lower()
        return login

    @property
    def config(self):
        """Return the configuration mapping, in the latest format."""
        # Upgrade config to version 1.1 format:
        if not hasattr(self, '_config'):
            self._config = self.__dict__['config']  # sidestep descriptor
            del self.__dict__['config']
            self._config.update(configDefaults1_1)

        # Upgrade to 1.4 format:
        if stripWindowsDomainKey not in self._config:
            self._config[stripWindowsDomainKey] = configDefaults[stripWindowsDomainKey]

        # Upgrade to 1.5 format:
        if not isinstance(self._config, PersistentDict):
            self._config = PersistentDict(self._config)
            self._config.update(configDefaults1_5)

        # Upgrade to 1.6 format:
        if secretEnabledKey not in self._config:
            self._config.update(configDefaults1_6)

        # Upgrade to 1.7 format:
        if forceLowercaseUsernamesKey not in self._config:
            self._config.update(configDefaults1_7)

        return self._config


    ## ZMI crap: ############################

    def __init__(self, id, title=None):
        BasePlugin.__init__(self)

        self._setId(id)
        self.title = title
        self._config = PersistentDict(configDefaults)

    # A method to return the configuration page:
    security.declareProtected(ManageUsers, 'manage_config')
    manage_config = PageTemplateFile('config.pt', wwwDirectory)

    # Add a tab that calls that method:
    manage_options = ({'label': 'Options',
                       'action': 'manage_config'},) + BasePlugin.manage_options

    security.declareProtected(ManageUsers, 'configForView')
    def configForView(self):
        """Return a mapping of my configuration values, for use in a page template."""
        ret = dict(self.config)
        ret['challenge_pattern_uncompiled'] = ret['challenge_pattern'].pattern
        return ret

    security.declareProtected(ManageUsers, 'manage_changeConfig')
    def manage_changeConfig(self, REQUEST=None):
        """Update my configuration based on form data."""
        for key in [stripDomainNamesKey, stripWindowsDomainKey, authenticateEverybodyKey, useCustomRedirectionKey, cookieCheckEnabledKey, challengeHeaderEnabledKey, secretEnabledKey, forceLowercaseUsernamesKey]:
            self.config[key] = REQUEST.form.get(key) == '1'  # Don't raise an exception; unchecked checkboxes don't get submitted.
        for key in [usernameHeaderKey, challengeReplacementKey, cookieNameKey, challengeHeaderNameKey, secretHeaderKey, secretValueKey]:
            self.config[key] = REQUEST.form[key]
        self.config[challengePatternKey] = re.compile(REQUEST.form[challengePatternKey])

        return REQUEST.RESPONSE.redirect('%s/manage_config' % self.absolute_url())


implementedInterfaces = [IUserEnumerationPlugin, IAuthenticationPlugin, IExtractionPlugin, IChallengePlugin]
classImplements(MultiPlugin, *implementedInterfaces)
InitializeClass(MultiPlugin)  # Make the security declarations work.
