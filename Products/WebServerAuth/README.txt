Description

    Authentication modules for web servers, like Apache or IIS, are more
    plentiful than those for Zope and Plone. WebServerAuth lets you take
    advantage of these in your site: just configure your web server to
    authenticate the user and store his or her login name in a request header,
    and WebServerAuth will convince Plone that that user is logged in.
    WebServerAuth has been used with LDAP, Active Directory, Kerberos,
    Shibboleth, Pubcookie, and CoSign and should work with anything else that
    can put a username into a header.


Use

    Once your web server is happily passing an authenticated login name to Plone
    via a request header, WebServerAuth kicks in and makes Plone consider that
    user logged in. To grant privileges to such a web-server-authenticated
    user...
    
        1. In Plone, create a user with the same login name as he or she uses
           to authenticate to the web server. (The old AutoMemberMaker product
           would automatically create Plone users. This led to a profusion of
           uninteresting users in large organizations.)
        
        2. Assign privileges to that user as you normally would.


Requirements

    * Plone 3.0 or maybe even 3.1.3 or higher. (If it works with 3.0, please let
      me know.)
    
    * Also works on Zope without Plone, as long as you have
      PluggableAuthService. I've tested with Zenoss 2.3.3 and 2.5.0, which
      suggests it works with Zope 2.8.8 or better and PluggableAuthService 1.4
      or better.


Upgrading

    From an older version of WebServerAuth
    
        1. Shut down Zope.
        
        2. Install the new WebServerAuth as described in the *Installation*
           section below (either by copying it to your Products folder or by
           running buildout).
        
        3. Start up Zope.
        
        4. Go to your-plone-site &rarr; site setup &rarr; Add-on Products, and
           reinstall WebServerAuth. (Your settings will be preserved.) If you
           are using Plone 3.3 or later and don't see the option to reinstall,
           just skip this step. If the message in the Add-on Product control
           panel bothers you, you can effect a reinstall using
           portal_quickinstaller in the ZMI.

    
    From apachepas and/or AutoMemberMakerPasPlugin
        
        1. Follow the installation instructions under *Installation*, then
           return here. (Installing WebServerAuth before removing the old
           products will let you do the whole installation as a
           web-server-authenticated user.)
        
        2. Note your apachepas settings: in the ZMI, your-plone-site &rarr;
           acl_users &rarr; apachepas.
        
        3. Go to your-plone-site &rarr; site setup &rarr; Add-on Products,
           and uninstall both apachepas and AutoMemberMakerPasPlugin. If you
           like, remove them from your Products folder as well.
        
        4. Visit the WebServerAuth configuration page (in the ZMI,
           your-plone-site &rarr; acl_users &rarr; web_server_auth), and restore
           the settings you used with apachepas.
        
        5. If you were using AutoMemberMakerPasPlugin, select *Any user the
           web server authenticates*. (This is almost equivalent; see below.) If
           not, select *Only users with pre-existing Plone accounts*.
        
        6. Click "Save Changes".
    
    
    A subtle but important change from AutoMemberMakerPasPlugin
        
        WebServerAuth does not grant users the Member role, only the
        Authenticated role (now that Plone supports that sort of thing without
        behaving erratically). This gives you the power to treat
        honest-to-goodness, explicitly endowed Members of your site differently
        than any idiot who authenticates to your web server. However, if you are
        upgrading from AutoMemberMakerPasPlugin, be sure to reexamine your
        site's permissions and workflows. If you want the same behavior as
        before, give Authenticated users all the privileges that Members
        previously had. If not, take this opportunity to differentiate the two
        roles.


Installation

    1. "Secure Zope":https://weblion.psu.edu/wiki/SecureZope against HTTP
       requests from things other than Apache, because the following
       configuration will make it accept whatever login name comes in. Also
       secure any intermediaries between Apache and Zope (Pound, Varnish, Squid,
       etc.) from direct access, as they could also be used to inject a login
       name.
    
    2. Move the WebServerAuth folder into the Products folder of your Zope
       instance. Alternatively, add *Products.WebServerAuth* to your
       buildout.cfg like this and re-run buildout::
    
        [instance]
        eggs =
            ...(other eggs)...
            Products.WebServerAuth

    3. Go to your-plone-site &rarr; site setup &rarr; Add-on Products, and
       install WebServerAuth.
        
    4. Have your web server always prompt for authentication on the HTTPS side.
       Then, have it pass the login name of the logged in user in a header (for
       which you'll need the mod_headers module). For example, if you're using
       Apache, you might use something like this::
       
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
            
                # Put the login name (stored below) into the HTTP_X_REMOTE_USER
                # request header. This has to be in the <Location> block for
                # some Apache auth modules, such as PubCookie, which don't set
                # REMOTE_USER until very late.
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
            
            # Do the typical VirtualHostMonster rewrite, adding an E= option
            # that puts the Apache-provided login name into the remoteUser
            # variable.
            RewriteRule ^/(.*)$ http://127.0.0.1:8080/VirtualHostBase/https/%{SERVER_NAME}:443/VirtualHostRoot/$1 [L,P,E=remoteUser:%{LA-U:REMOTE_USER}]
        </VirtualHost>
    
    5. If you have a port-80 virtual host, be sure to clear out the
       HTTP_X_REMOTE_USER header so end users can't pass arbitrary login names
       directly to the web server and masquerade as any user they like::
       
        <VirtualHost *:80>
            ...
            RequestHeader unset X_REMOTE_USER
            ...
        </VirtualHost>
       
    6. Point Plone's Log Out link (in the ZMI: your-plone-site &rarr;
       portal_actions &rarr; user &rarr; logout) to something sensible. For
       example, if you're using a single-sign-on system that provides its own
       logout page, point to that. If you can't think of anything better, make a
       page that says "Sorry, Bub. You'll have to quit your web browser to log
       out", and point it to that. 'string:${portal_url}/logged_out' may serve.

    7. Point the Change Password link (in the ZMI: your-plone-site &rarr;
       portal_controlpanel) to something sensible, or hide it altogether.
    
    8. Hide the Login portlet; it isn't meant to work with WebServerAuth. Your
       visitors will try to use it, and they'll get confused when it doesn't
       work. A future version of WebServerAuth will do this automatically.


Troubleshooting

    In Plone's navigation bar, "(null)" shows up instead of the login name.
    
        For some reason, the web server is not passing the HTTP_X_REMOTE_USER
        header to Zope. If you are using Apache, make sure you included the
        <Proxy *> block above.

    I can't access any of the acl_users screens, add users, or do anythinguseful in the Plone site, but I can get into the root-level acl_users just fine.
        
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
    instance in the ZMI; it will be at your-plone-site &rarr; acl_users &rarr;
    web_server_auth. The configuration options are as follows:
    
    Authenticate...

        Any user the web server authenticates
        
            To recognize everybody your web server recognizes, leave this option
            selected. The downside of this is that, if you have user folders
            enabled, anybody your web server knows will be able to make one.
            However, this option is the recommended one, because the UI is the
            most consistent (read on).

        Only users with a pre-existing Plone account
        
            If you want to authenticate only some of the users your web server
            recognizes, select this option, and use the *Users and Groups* page
            in *Site Setup* to create the users you want to have recognized.
            Users you don't create will still be able to get past your web
            server's login prompt but will not be recognized by Plone. This
            option is discouraged, because the UI is terrible: people will log
            in and apparently succeed, only to be greeted with a Plone page that
            still has a "Log In" link. However, it's the only way to have user
            folders and yet not give them out to every Tom, Dick, and Harry your
            web server recognizes. If somebody cares to donate themes that fix
            the UI, I'll be happy to include them.
        
        Using the login name in the such-and-such header
    
            If, for some reason, you cannot use the default HTTP_X_REMOTE_USER
            header (for instance, if you are using IISCosign, which has
            "HTTP_REMOTE_USER" hard-coded in), change the header WebServerAuth
            looks in here.
    
        Only when...
        
            The such-and-such cookie is present
        
                In some situations, it is useful to be able to control whether
                the user is logged in or not based on a cookie, even if the
                actual authentication takes place outside Zope. For example,
                IIS can be configured to use integrated Windows authentication,
                in which case NTLM or Kerberos authentication will be used to
                set the X-Remote-User header. However, you may not want your
                users to appear logged in to Zope at all times, for example
                because you can cache content much more efficiently if everyone
                is anonymous.
    
                The solution is to use a custom view or something outside Zope
                to set a cookie to indicate that the user should be logged in,
                and then enable this option. If the cookie is absent, the user
                will not be authenticated.
            
            The such-and-such header contains the (shared secret) value
                this-and-that
        
                To protect against local forgery attacks a header
                (HTTP_WSA_SECRET by default) may be required to contain a
                shared secret value before credential extraction will take
                place.  If this option is enabled and the header does not
                contain the shared secret value, the user will not be
                authenticated.
    
    To prompt the user for credentials, redirect...
    
        To the HTTPS version of wherever he was going
        
            When an anonymous user tries to access
            _http://example.com/something-requiring-authentication_, redirect
            him to _https://example.com/something-requiring-authentication_
            (note the "https").
        
        To a custom URL
        
            If the above doesn't suit you, you can customize the redirection
            behavior. In the *Matching pattern* box, enter a "regular
            expression":http://en.wikipedia.org/wiki/Regular_expression which
            matches every URL on your site and captures (using parentheses) the
            parts you'll need when constructing the URL to redirect to. In the
            *Replacement pattern* box, enter the URL to redirect to. Make sure
            it's an HTTPS URL, and "use
            backreferences":http://docs.python.org/library/re.html#re.sub (like
            \1, \2, and so on) to substitute in the parts you captured above.
        
        Only when the such-and-such request header is present
        
            In some scenarios, WebServerAuth's redirection to HTTPS is
            counterproductive. For example, if you ssh tunnel directly to Zope
            to avoid a web server and caching proxy, redirecting to HTTPS would
            mean speaking HTTPS directly to Zope, which doesn't even listen on
            port 443. This option lets you automatically disable such
            redirections when there is no web server in front of Zope.

            If you turn this option on, you must also have your web server (or
            something in front of Zope) set the specified header, at least for
            all requests that could result in a WebServerAuth redirect. In a
            typical Apache setup, doing this in your port-80 vhost would
            suffice::

              RequestHeader set WSA_SHOULD_CHALLENGE yep

            What you set the header to is immaterial; as long as it's present,
            WebServerAuth is happy.
            
            Note that you'll probably still have to first authenticate at the
            root level of the ZMI and then wend your way into your Plone sites
            (if any), since WebServerAuth's redirecting override of login_form
            still redirects unconditionally. We might fix this later if we can
            bring ourselves to duplicate the custom acquisition logic of
            portal_skins.
            
            A variety of configuration-free heuristics were considered before
            arriving at this explicit-header option, but there was always some
            special case to confound them: for example, custom redirect patterns
            that include strange explicit ports or setups that use a special
            login page rather than just any HTTPS-protocol request.

    Strip domains from login names containing...
    
        Email-like domains
        
            If your web server returns a login name that looks like
            fred@example.com, WebServerAuth will, by default, strip off
            everything from the @ onward. If you don't want it to do this (for
            example, if you are using a cross-domain authorization system like
            Shibboleth where this could cause name collisions), turn off this
            option.

            Note that Plone will not let you create a user with an @ or a period
            in its login name. In order to assign privileges to a user with a
            domain in its name...

                1. In Plone, create a user with a temporary name.
    
                2. In source_users (in the ZMI: your-plone-site &rarr; acl_users
                   &rarr; source_users), change the Login Name of the user to
                   the full, domain-having name.

        Windows domains
        
            If your web server includes a Windows/Active Directory domain in the
            login name, turn this on to strip it off. For example, if the server
            sets HTTP_X_REMOTE_USER to "EXAMPLE\fred", turning this option on
            will shorten it to "fred". This can be useful if you are using
            Active Directory and sAMAccountName as the user id name, for
            example.



Ancestry

    WebServerAuth obsoletes and improves upon apachepas and
    AutoMemberMakerPasPlugin, which come significantly and entirely,
    respectively, from the same author.
    
    Improvements over apachepas and AutoMemberMakerPasPlugin
    
        * When an anonymous user tries to access something unpermitted,
          we redirect him to the HTTPS side, which triggers a proper login
          prompt. There are no more nonworking login forms popping up as in
          the old products.
        
        * No longer does every user who has ever logged in clutter up your Users
          and Groups control panel.
        
        * Grants all logged-in users the Authenticated role rather than the
          Member role, allowing site admins to treat the two differently. (Plone
          now supports this properly.) This means someone who authenticates to
          your web server doesn't necessarily get any privileges in your Plone
          site, making it safe to authenticate everyone; previously, when
          everyone got the Member role, certain default Plone workflows would
          grant them some capabilities.
        
        * Twiddles Plone's login link as necessary, reducing the need for
          manual configuration
        
        * Jettisons a lot of legacy code and requirements
        
        * Increases test coverage and does away with doctests
        
        * Is one product instead of two
        
        * Takes over the login_form so people can't log in wrong even if they
          try


Testing

    To run the WebServerAuth tests, use the standard Zope testrunner::
    
        bin/instance test -pvvm Products.WebServerAuth


Future Plans

    * Execute political machinations necessary to let PAS find users who aren't
      enumerable so we can junk the hackish user enumerator.
    
    * Scheme and connive until Plone fires the IUserCreatedEvent properly, not
      just if the login form is used. Then we can get rid of the
      make-users-inside-an-auth-handler madness.
    
    * In stock Plone, users show up in the Users tab search (I'm not talking
      about the Users and Groups control panel, mind you) immediately after
      they're created. With WebServerAuth, they never show up.


Authors

    * Erik Rose of the WebLion group at Penn State University

    * Rocky Burt wrote the pre-1.1 versions of apachepas, which, along with
      Erik's AutoMemberMakerPasPlugin, led to WebServerAuth.

    * Mark James created the ZMI icon, available from
      http://www.famfamfam.com/lab/icons/silk/ .

    * Martin Aspeli drove the features in versions 1.4 and 1.5.
    
    * Craig Haynal conceived and implemented the shared secret feature.


Support

    Contact the WebLion team at support@weblion.psu.edu or join our IRC
    channel, #weblion on irc.freenode.net. The
    "WebLion wiki":http://weblion.psu.edu/trac/weblion is full of good
    stuff.


Version History
     
    ' ' 1.6 -- ' '
    
        * Added option to check for the presence of a header before
          challenging, which makes ssh tunneling to Zope less impossible.
        
        * Factored the configuration and upgrade stuff, which was getting pretty
          long, out of plugin.py.
          
        * Added shared secret support.  A header (HTTP_WSA_SECRET by default)
          can be checked for an optional shared secret value.  When enabled and
          specfied, this value must match the header value for credential
          extraction to take place.
          
        * Reworked the ZMI options page to be more consistent.

    ' ' 1.5 -- ' '
    
        * Added option to check for the presence of a cookie before
          authenticating, which makes some Windows domain-based authentication
          scenarios easier.

        * Fixed a bug where configuration was accidentally shared
          instance-wide. Having different configs in different Plone sites works
          now.

        * Refactored tests, which had been working around this bug.

        * Fixed a bug where we were removing the wrong skin layer on uninstall.
        
        * Improved labeling on configuration page.

    ' ' 1.4 -- ' '
    
        * Added Windows domain stripping, thanks to Martin Aspeli.

    ' ' 1.3.1 -- ' '
    
        * Corrected egg installation instructions in readme.

    ' ' 1.3 -- ' '
    
        * Repackaged as an egg so buildout users can install it more easily.

    ' ' 1.2 -- ' '
    
        * Added redirection of login_form so it logs you in using WebServerAuth.
          Apparently, Plone's default commenting setup comes with a "Log in to
          add comments" button hard-coded to point to login_form. Blech!
        
        * A call to the WebServerAuth PAS plugin is used to compute the login
          link. Previously, it was hard-coded to use the portal-level acl_users
          folder. Now it uses the nearest one, in case somebody is crazy enough
          to define another.

    ' ' 1.1.2 -- ' '
    
        * Corrected "a bug":https://weblion.psu.edu/trac/weblion/ticket/1156
          that kept users from being recognized when they had a domain in their
          login name and domain stripping was on.
        
        * Made the example regex a little tighter; I'd forgot to backslash the
          period.
        
        * Added experimental support for running on Zope without Plone. Works
          with Zenoss 2.3.3, anyway.

    ' ' 1.1.1 -- ' '
    
        * Fixed "spurious &ldquo;Your custom WebServerAuth Matching Pattern did
          not match&rdquo; error":https://weblion.psu.edu/trac/weblion/ticket/941
        
        * Added instructions to the config page.

    ' ' 1.1 -- ' '
               
        * Provided for customization of where the challenge handler and login
          link send users.
        
        * Added even more instructions on setting up a secure Zope
          instance to the readme.

    ' ' 1.0 -- ' '
    
        * Polished the readme a bit. No code changes since 1.0b1.

    ' ' 1.0b1 -- ' '
    
        * First beta. No known bugs.


License

    Copyright (c) 2008-2011 The Pennsylvania State University. WebLion products
    are developed and maintained by the WebLion Project Team, its partners, and
    members of the Penn State Plone Users Group.

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
