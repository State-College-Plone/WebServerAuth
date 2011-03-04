from setuptools import setup, find_packages
import os

version = open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Products', 'WebServerAuth', 'version.txt')).read().strip()
if version.endswith('dev'):
    version = version[:-3]

setup(
    name='Products.WebServerAuth',
    version=version,
    description="Delegates Plone's authentication concerns to a web server",
    long_description="""Authentication modules for web servers, like Apache or IIS, are more plentiful than those for Zope and Plone. WebServerAuth lets you take advantage of these in your site: just configure your web server to authenticate the user and store his or her login name in a request header, and WebServerAuth will convince Plone that that user is logged in. WebServerAuth has been used with LDAP, Active Directory, Kerberos, Shibboleth, Pubcookie, and CoSign and should work with anything else that can put a username into a header.

`Read more at the WebServerAuth product page... <http://plone.org/products/webserverauth/>`_
""",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration :: Authentication/Directory"
    ],
    keywords='web zope plone authentication pas zope2',
    author='WebLion Group, Penn State',
    author_email='support@weblion.psu.edu',
    url='http://plone.org/products/webserverauth',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        # Older versions of the following weren't eggified. Including them as requirements would preclude WebServerAuth's use with them, when in fact they work.
        # 'Products.CMFCore',
        # 'Products.PluggableAuthService',
        # 'Zope2'
    ],
    extras_require={
        # Older versions of Plone weren't eggified. Including them as requirements would preclude WebServerAuth's use with them, when in fact they work.
        # 'Plone': ['Plone>=3.1.3']  # Plone-savvy but also works with raw Zope 2
    },
    entry_points={}
)
