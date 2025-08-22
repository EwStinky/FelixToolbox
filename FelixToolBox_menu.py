"""
/***************************************************************************
    __init__ - FelixToolBox QGIS plugins menu class
                             -------------------
        start                : 05/03/2025
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""

from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtGui import QIcon
import os
from  .library import *
from .ui import *

class felixtoolbox_menu:
    def __init__(self, iface):
        self.iface = iface
        self.menu = None
    
    def add_submenu(self, submenu, icon):
        """"took it from HCMGIS plugin"""
        if self.menu != None:
            submenu.setIcon(QIcon(icon))
            self.menu.addMenu(submenu)
        else:
            self.iface.addPluginToMenu("&Félix's toolbox", submenu.menuAction())

    def initGui(self):
        #main menu
        self.menu = QMenu("Félix's toolbox", self.iface.mainWindow().menuBar())
        self.iface.mainWindow().menuBar().insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

        #1. Cartographie submenu
        self.mapping_menu = QMenu(u'Mapping')
        icon = QIcon(os.path.dirname(__file__) + "/icons/1F5FA_color.png")
        self.add_submenu(self.mapping_menu, icon)

        #1.A. Map Screenshot action
        icon = QIcon(os.path.dirname(__file__) + "/icons/1F4F7_color.png")  
        self.mapscreenshot_action = QAction(icon, u'Map Screenshot', self.iface.mainWindow())
        self.mapscreenshot_action.triggered.connect(mapscreenshot.run)
        self.mapping_menu.addAction(self.mapscreenshot_action)

        #2. Accessibility submenu
        self.accessibility_menu = QMenu(u'Accessibility')
        icon = QIcon(os.path.dirname(__file__) + "/icons/1F680_color.png")
        self.add_submenu(self.accessibility_menu, icon)

        #2.A. Isochrone ORS Tools API action
        icon = QIcon(os.path.dirname(__file__) + "/icons/1F698_color.png")  
        self.isochrone_ors_tools_api = QAction(icon, u'Isochrone ORS API', self.iface.mainWindow())
        self.isochrone_ors_tools_api.triggered.connect(lambda: ui_run_isochrone().run())
        self.accessibility_menu.addAction(self.isochrone_ors_tools_api)

        #2.B. Isochrone IGN API action
        icon = QIcon(os.path.dirname(__file__) + "/icons/1F699_color.png")  
        self.isochrone_ign_api = QAction(icon, u'Isochrone IGN API', self.iface.mainWindow())
        self.isochrone_ign_api.triggered.connect(lambda: ui_run_isochrone_ign().run())
        self.accessibility_menu.addAction(self.isochrone_ign_api)

        #3. Geocoding submenu
        self.geocoding_menu = QMenu(u'Geocoding')
        icon = QIcon(os.path.dirname(__file__) + "/icons/1F9ED_color.png")
        self.add_submenu(self.geocoding_menu, icon)

        #3.A. Address to point action
        icon = QIcon(os.path.dirname(__file__) + "/icons/E0A9_color.png")  
        self.adress2point = QAction(icon, u'Address to Point', self.iface.mainWindow())
        self.adress2point.triggered.connect(lambda: ui_run_address2point().run())
        self.geocoding_menu.addAction(self.adress2point)

        #3.B. Request API SIRENE action
        icon = QIcon(os.path.dirname(__file__) + "/icons/1F4BC_color.png")  
        self.requestSirene = QAction(icon, u'Siret located within polygon', self.iface.mainWindow())
        self.requestSirene.triggered.connect(lambda: ui_run_request_sirene().run())
        self.geocoding_menu.addAction(self.requestSirene)

    def unload(self):
        if self.menu != None:
            self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        else:
            self.iface.removePluginMenu("&Félix's toolbox", self.mapping_menu.menuAction())
            self.iface.removePluginMenu("&Félix's toolbox", self.accessibility_menu.menuAction())
            self.iface.removePluginMenu("&Félix's toolbox", self.geocoding_menu.menuAction())
