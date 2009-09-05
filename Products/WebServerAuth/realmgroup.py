from AccessControl import getSecurityManager
from Globals import InitializeClass
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PlonePAS.plugins.autogroup import AutoGroup
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin, IGroupsPlugin
from Products.PluggableAuthService.utils import classImplements

class RealmGroup(AutoGroup):
    meta_type = "Realm Group Plugin"

    _properties = AutoGroup._properties + (
        { 'id'      : 'realm', 
          'label'   : 'Realm',
          'type'    : 'string',
          'mode'    : 'w',
        },
        { 'id'      : 'header',
          'label'   : 'Header',
          'type'    : 'string',
          'mode'    : 'w',
        },
    )

    def __init__(self, id, title='', group=None, description='', realm='', header=''):
        AutoGroup.__init__(self, id=id, title=title, group=group, description=description)
        self.realm = realm
        self.header = header

    def getGroupsForPrincipal(self, principal, request=None):
        if getSecurityManager().getUser().getId()!=principal:
            return ()

        # TODO: check if we should indicate membership in our group
        return (self.group,)

implementedInterfaces = [IGroupEnumerationPlugin, IGroupsPlugin, IGroupIntrospection]
classImplements(RealmGroup, *implementedInterfaces)
InitializeClass(RealmGroup)
