Description

    WebServerAuth is a PAS multiplugin which allows Plone to delegate
    authentication concerns to a web server like Apache or IIS. Using
    WebServerAuth, Plone can be configured so any user known to your LDAP,
    Kerberos, Shibboleth, or Pubcookie system&mdash;or any other system for
    which your web server has an authentication module&mdash;can transparently
    log in using enterprise-wide credentials.
    
    WebServerAuth is intended to replace and improve upon apachepas and
    AutoMemberMakerPasPlugin, which come significantly and entirely,
    respectively, from the same author.
    
    Improvements over apachepas and AutoMemberMakerPasPlugin
    
        * When an anonymous user tries to access something unpermitted,
          we redirect him to the HTTPS side, which triggers a proper login
          prompt. There are no more nonworking login forms popping up as in
          the old products.
        
        * No longer does every user who has ever logged in clutter up your Users
          and Groups control panel. Similarly, the Member role is now granted
          dynamically.
        
        * Twiddles Plone's login link as necessary, reducing the need for
          manual configuration
        
        * Jettisons a lot of legacy code and requirements
        
        * Increases test coverage and does away with doctests
        
        * Is unapologetically a Plone product: no more of the architectural
          compromises needed to support plain Zope use. This is why we can have
          one product instead of two!


Requirements

    * Plone 3.0 or higher


Upgrading

    From apachepas and AutoMemberMakerPasPlugin
        
        1. Note your apachepas settings: in the ZMI, your-plone-site &rarr;
           acl_users &rarr; apachepas.
        
        2. Go to your-plone-site &rarr; site setup &rarr; Add/Remove Products,
           and uninstall both apachepas and AutoMemberMakerPasPlugin. If you
           like, remove them from your Products folder as well.
        
        3. Follow the installation instructions below.
        
        4. Visit the WebServerAuth configuration page (in the ZMI,
           your-plone-site &rarr; acl_users &rarr; web_server_auth), and restore
           the settings you used with apachepas.


Installation

    1. Copy WebServerAuth to your '$INSTANCE_HOME/Products' directory.

    2. Go to your-plone-site &rarr; site setup &rarr; Add/Remove Products, and
       install WebServerAuth.
        
    3. Have your web server always prompt for authentication on the HTTPS side.
       Then, have it pass the username of the logged in user in a header. For
       example, if you're using Apache, you might use something like this::
       
        <VirtualHost *:443>
            ServerName www.example.com
            
            # Prompt for authentication:
            <Location />
                SSLRequireSSL
                AuthType Basic
                AuthName "My Funky Web Site"
                AuthUserFile /etc/such-and-such
                # etc.
                Require valid-user
            
                # Put the username (stored below) into the HTTP_X_REMOTE_USER request header.
                # This has to be in the <Location> block for some Apache auth modules, such as PubCookie, which don't set REMOTE_USER until very late.
                RequestHeader set X_REMOTE_USER %{remoteUser}e
            </Location>
            
            # Some Linux distributions (e.g., Debian Etch and Red Hat Enterprise
            # Linux AS Release 4) have default settings which prevent the header
            # rewrites below from working. Fix that:
            <Proxy *>
                Order deny,allow
                Allow from all
            </Proxy>
            
            RewriteEngine On
            
            # Do the typical VirtualHostMonster rewrite, adding an E= option that puts the Apache-provided username into the remoteUser variable.
            RewriteRule ^/(.*)$ http://127.0.0.1:8080/VirtualHostBase/https/%{SERVER_NAME}:443/VirtualHostRoot/$1 [L,P,E=remoteUser:%{LA-U:REMOTE_USER}]
        </VirtualHost>
    
    4. Point Plone's Log Out link (in the ZMI: your-plone-site &rarr;
       portal_actions &rarr; user &rarr; logout) to something sensible. For
       example, if you're using a single-sign-on system that provides its own
       logout page, point to that. If you can't think of anything better, make a
       page that says "Sorry, Bub. You'll have to quit your web browser to log
       out", and point it at that.

    5. Point the Change Password link (in the ZMI: your-plone-site &rarr;
       portal_controlpanel) to something sensible, or hide it altogether.


Troubleshooting

    In Plone's navigation bar, "(null)" shows up instead of the username.
    
        For some reason, the web server is not passing the HTTP_X_REMOTE_USER
        header to Zope. If you are using Apache, make sure you included the
        <Proxy *> block above.

    I can't access any of the acl_users screens, add users, or do anything useful in the Plone site, but it works with the root acl_users.
        
        If you have an existing user with the same ID as your user inside the
        Plone site, this will override your permission/role settings, so you
        can't access these things on an admin level anymore. Solution: Create
        a new user with a non-conflicting ID in the root folder, give it the
        Manager role, and log in with this user instead. Now the acl_users
        should behave normally again, and you should be able to change the
        settings.


Configuration
    
    WebServerAuth ships with sensible defaults, so you probably won't need to
    configure it at all. But if you do, first navigate to your WebServerAuth
    instance in the ZMI; it will be in '/your-plone-site/acl_users'. The
    configuration options are as follows:
        
    Admit...
    
        If you want to admit only a subset of the users your web server
        recognizes, select "Only users made within Plone", and use the *Users
        and Groups* page in *Site Setup* to create the users you want to admit.
        Users you have not created will still be able to get past your web
        server's login prompt but will not be recognized by Plone.

        To admit everybody your web server admits, leave "Any user the web
        server authenticates" selected.

    Strip domain names from usernames
    
        If your web server includes a domain in the username, WebServerAuth
        will, by default, strip it off. For example, if the server sets
        X_REMOTE_USER to "fred@example.com", WebServerAuth will shorten it to
        "fred". If you don't want it to do this (for example, if you are using a
        cross-domain authorization system like Shibboleth where this could cause
        name collisions), turn off "Strip domain names from usernames".
        
    Username is in the such-and-such header
    
        If, for some reason, you cannot use the default HTTP_X_REMOTE_USER
        header (for instance, if you are using IISCosign, which has
        "HTTP_REMOTE_USER" hard-coded in), change the header WebServerAuth looks
        in here.


Testing

    To run the WebServerAuth tests, use the standard Zope testrunner::
    
        $INSTANCE_HOME/bin/zopectl test -pvvm Products.WebServerAuth


Future Plans

    * Execute political machinations necessary to let PAS find users who aren't
      enumerable so we can junk the hackish user enumerator.
    
    * Scheme and connive until Plone fires the IUserCreatedEvent properly, not
      just if the login form is used. Then we can get rid of the
      make-users-inside-an-auth-handler madness.
    
    * In stock Plone, users show up in the Users tab search (I'm not talking
      about the Users and Groups control panel, mind you) immediately after
      they're created. With WebServerAuth, auto-created users show up in the
      search after they've logged in at least once. Is this the best compromise
      between technical constraints and UI consistency? Opinions from people who
      actually use this search are most welcome.


Authorship

    Erik Rose of the WebLion group at Penn State University


Thanks

    Thanks to Rocky Burt, who wrote the pre-1.1 versions of apachepas, which,
    along with my AutoMemberMakerPasPlugin, led to WebServerAuth.

    Thanks to Mark James for the ZMI icon, available from
    http://www.famfamfam.com/lab/icons/silk/.


Support

    Contact the WebLion team at support@weblion.psu.edu or join our IRC
    channel, #weblion on irc.freenode.net. The
    "WebLion wiki":http://weblion.psu.edu/trac/weblion is full of good
    stuff.

    Please report bugs using the
    "WebLion issue tracker":https://weblion.psu.edu/trac/weblion/newticket?component=WebServerAuth&version=1.0b1.


Version History
    
    ' ' 1.0b1 -- First release. Not quite feature-complete but should be stable
                 and future-compatible.


License

    Copyright (c) 2008 The Pennsylvania State University. WebLion products are
    developed and maintained by the WebLion Project Team, its partners, and
    members of the Penn State Zope Users Group.

    This program is free software; you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the Free
    Software Foundation; either version 2 of the License, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
    more details.

    You should have received a copy of the GNU General Public License along with
    this program; if not, write to the Free Software Foundation, Inc., 59 Temple
    Place, Suite 330, Boston, MA 02111-1307 USA.

    This document is written using the Structured Text format for conversion
    into alternative formats.