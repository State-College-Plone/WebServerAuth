from plone.app.portlets.portlets.login import Renderer

class LoginPortletRenderer(Renderer):
    """Login portlet that never shows up, since it doesn't work and just confuses people"""
    
    def show(self):
        return False


# from zope.component import getUtility, getMultiAdapter
# from plone.app.portlets.portlets.login import ILoginPortlet
# getMultiAdapter((portal, portal.REQUEST, portal.restrictedTraverse('@@plone')), ILoginPortlet)