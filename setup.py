from setuptools import setup, find_packages
import os

setup(
    name='Products.WebServerAuth',
    version=open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Products', 'WebServerAuth', 'version.txt')).read().strip(),
    description="Delegates Plone's authentication concerns to a web server",
    long_description="""WebServerAuth allows Plone to delegate authentication concerns to a web server like Apache or IIS. Using WebServerAuth, Plone can be configured so any user known to your LDAP, Kerberos, Shibboleth, or Pubcookie system|mdash|or any other system for which your web server has an authentication module|mdash|can transparently log in using enterprise-wide credentials.

`Read the whole readme. <http://plone.org/products/webserverauth/>`_

.. |mdash| unicode:: U+02014 .. em dash""",
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
    author='Erik Rose',
    author_email='support@weblion.psu.edu',
    url='http://plone.org/products/webserverauth',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
      'setuptools',
      'Products.CMFCore',
      'Products.PluggableAuthService'
    ],
    entry_points={}
)
