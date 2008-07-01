Description

    WebServerAuth is a PAS multiplugin which allows Plone to delegate
    authentication concerns to a web server like Apache or IIS. Using
    WebServerAuth, Plone can be configured so any user known to your LDAP,
    Kerberos, Shibboleth, or Pubcookie system&mdash;or any other system for
    which your web server has an authentication module&mdash;can transparently
    log in using enterprise-wide credentials.
    
    Relationship to apachepas and AutoMemberMakerPasPlugin
    
        WebServerAuth replaces both apachepas and AutoMemberMakerPasPlugin.
        It...
        
            * Jettisons a lot of legacy code and requirements
            
            * Improves test coverage
            
            * Provides a challenge handler: no more bogus login forms popping
              up
            
            * Is unapologetically a Plone product: no more plain Zope support
            
            * Twiddles Plone's login and logout links as necessary: less manual
              configuration
            
            * Uses better login hooks exclusive to Plone 3: no more hacky making
              of members within an auth handler


Requirements

    * Plone 3.0 or higher


Upgrading

    From apachepas and AutoMemberMakerPasPlugin

        1. Write me. Probably just uninstall the former and install this.


Installation

    1. Copy WebServerAuth to your '$INSTANCE_HOME/Products' directory.

    2. Install the plugin:
    
        1. Go to your-plone-site &rarr; site setup &rarr; Add/Remove Products, and
           install WebServerAuth.
        
    3. Tell your web server to pass the username of the logged in user in a
       header. For example, to configure Apache, you might use these
       directives::
     
        # Some Linux distributions (e.g., Debian Etch and Red Hat Enterprise
        # Linux AS Release 4) have default settings which prevent the header
        # rewrites below from working. Fix that:
        <Proxy *>
            Order deny,allow
            Allow from all
        </Proxy>
        
        RewriteEngine On
        
        # Grab the remote user as environment variable.
        # (This RewriteRule doesn't actually rewrite anything URL-wise.)
        RewriteCond %{LA-U:REMOTE_USER} (.+)
        RewriteRule .* - [E=RU:%1]
        
        # Put the username into the HTTP_X_REMOTE_USER request header:
        RequestHeader set X_REMOTE_USER %{RU}e
        
        # Do the typical VirtualHostMonster rewrite:
        RewriteRule ^/port_8080(.*) http://localhost:8080/VirtualHostBase/http//localhost:80/VirtualHostRoot/_vh_port_8080/$1 [L,P]


Troubleshooting

    In Plone's navigation bar, "(null)" shows up instead of the username.
    
        For some reason, the web server is not passing the HTTP_X_REMOTE_USER
        header to Zope. If you are using Apache, make sure you included the
        <Proxy *> block above.

    I can't access any of the acl_users screens, add users, or do anything useful in the Plone site, but it works with the root acl_users.
        
        If you have an existing user with the same ID as your user inside the
        Plone site, this will override your permission/role settings, so you
        can't access these things on an admin level anymore. Solution: Create
        a new user with a non-conflicting ID in the root folder, give him the
        Manager role, and log in with this user instead. Now the acl_users
        should behave normally again, and you should be able to change the
        settings.


Configuration
    
    WebServerAuth ships with sensible defaults, so you probably won't need to
    configure it at all. If, however, you do, first navigate to your
    WebServerAuth instance in the ZMI; it will be in '/acl_users' or
    '/your-plone-site/acl_users'. Click your WebServerAuth instance, then see
    one of the following sections:

    Strip domain names from usernames
    
        If your web server includes a domain in the username, WebServerAuth
        will, by default, strip it off. For example, if the server sets
        X_REMOTE_USER to "fred@example.com", WebServerAuth will shorten it to
        "fred". If you don't want it to do this (for example, if you are using a
        cross-domain authorization system like Shibboleth where this could cause
        name collisions), turn off "Strip domain names from usernames".
        
    HTTP header containing username
    
        If, for some reason, you cannot use the default HTTP_X_REMOTE_USER
        header (for instance, if you are using IISCosign, which has
        "HTTP_REMOTE_USER" hard-coded in), you can change the header
        WebServerAuth looks in here.
        
    Admit only manually created users
    
        If you want to admit only a subset of the users that your web server
        recognizes, check this, and use the *Users and Groups Administration*
        page in Plone to create the users you want to admit. Users you have not
        added will still be able to satisfy Apache's login prompt but will not
        be recognized by Plone.


Testing

    To run the WebServerAuth tests, use the standard Zope testrunner::
    
        $INSTANCE_HOME/bin/zopectl test -pvvm Products.WebServerAuth


Authorship

    WebServerAuth is written by Erik Rose of the WebLion group at Penn State
    University.


Thanks

    Thanks to Rocky Burt, who wrote the pre-1.1 versions of apachepas, which,
    along with AutoMemberMakerPasPlugin, led to WebServerAuth.

    Thanks to Mark James for the ZMI icon, available from
    http://www.famfamfam.com/lab/icons/silk/.


Support

    Contact the WebLion team at support@weblion.psu.edu or join our IRC
    channel, #weblion on irc.freenode.net. The
    "WebLion wiki":http://weblion.psu.edu/trac/weblion is full of good
    stuff.

    Please report bugs using the
    "WebLion issue tracker":https://weblion.psu.edu/trac/weblion/newticket?component=WebServerAuth&version=0.1.


Version History
    
    ' ' 0.1 -- Initial release. Future releases might not be compatible with
               this one.
