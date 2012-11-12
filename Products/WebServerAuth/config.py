"""Configuration defaults used for initializing new instances or upgrading old ones"""

import re

# Keys for storing config:
stripDomainNamesKey = 'strip_domain_names'
stripWindowsDomainKey = 'strip_windows_domain'
usernameHeaderKey = 'username_header'
authenticateEverybodyKey = 'authenticate_everybody'
useCustomRedirectionKey = 'use_custom_redirection'
challengePatternKey = 'challenge_pattern'
challengeReplacementKey = 'challenge_replacement'
cookieCheckEnabledKey = 'cookie_check_enabled'
cookieNameKey = 'cookie_name'
challengeHeaderEnabledKey = 'challenge_header_enabled'
challengeHeaderNameKey = 'challenge_header_name'
secretEnabledKey = 'secret_enabled'
secretHeaderKey = 'secret_header'
secretValueKey = 'secret_value'

# Configuration defaults for various versions:

defaultUsernameHeader = 'HTTP_X_REMOTE_USER'
defaultChallengeHeader = 'HTTP_WSA_SHOULD_CHALLENGE'
defaultSecretHeader = 'HTTP_WSA_SECRET'

configDefaults = {
        # It's useful to be able to turn this off for Shibboleth and
        # other federated auth systems:
        stripDomainNamesKey: True,
        
        # For Active Directory:
        stripWindowsDomainKey: False,
        
        # IISCosign insists on using HTTP_REMOTE_USER instead of
        # HTTP_X_REMOTE_USER:
        usernameHeaderKey: defaultUsernameHeader,
        
        authenticateEverybodyKey: True
    }

configDefaults1_1 = {
        # Config defaults new in version 1.1, when we migrated to a config
        # property:
        useCustomRedirectionKey: False,
        challengePatternKey: re.compile(r'http://example\.com/(.*)'),
        challengeReplacementKey: r'https://secure.example.com/some-site/\1'
    }
configDefaults.update(configDefaults1_1)

configDefaults1_5 = {
        cookieNameKey: 'wsa_should_auth',
        cookieCheckEnabledKey: False
    }
configDefaults.update(configDefaults1_5)

configDefaults1_6 = {
    challengeHeaderEnabledKey: False,
    challengeHeaderNameKey: defaultChallengeHeader,
    secretHeaderKey: defaultSecretHeader,
    secretValueKey: '',
    secretEnabledKey: False
}
configDefaults.update(configDefaults1_6)

defaultChallengePattern = re.compile('http://(.*)')
defaultChallengeReplacement = r'https://\1'
