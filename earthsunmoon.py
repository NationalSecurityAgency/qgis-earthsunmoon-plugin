# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EarthSunMoon
    
                              -------------------
        begin                : 2021-06-06
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
import processing
from .provider import EarthSunMoonProvider

import os

class EarthSunMoon(object):
    solarInfoDialog = None

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.provider = EarthSunMoonProvider()

    def initGui(self):
        self.toolbar = self.iface.addToolBar('Day/Night Tools Toolbar')
        self.toolbar.setObjectName('DayNightToolsToolbar')
        
        '''icon = QIcon(os.path.dirname(__file__) + "/icons/daynight.png")
        self.dayNightAction = QAction(icon, "Day/Night terminator", self.iface.mainWindow())
        self.dayNightAction.triggered.connect(self.dayNight)
        self.iface.addPluginToMenu("Earth, sun, moon && planets", self.dayNightAction)
        self.toolbar.addAction(self.dayNightAction)'''
        
        icon = QIcon(os.path.dirname(__file__) + "/icons/sun_icon.svg")
        self.sunPositionAction = QAction(icon, "Sun position directly overhead", self.iface.mainWindow())
        self.sunPositionAction.triggered.connect(self.sunPosition)
        self.iface.addPluginToMenu("Earth, sun, moon && planets", self.sunPositionAction)
        self.toolbar.addAction(self.sunPositionAction)

        icon = QIcon(os.path.dirname(__file__) + "/icons/moon.png")
        self.moonPositionAction = QAction(icon, "Moon position directly overhead", self.iface.mainWindow())
        self.moonPositionAction.triggered.connect(self.moonPosition)
        self.iface.addPluginToMenu("Earth, sun, moon && planets", self.moonPositionAction)
        self.toolbar.addAction(self.moonPositionAction)

        icon = QIcon(os.path.dirname(__file__) + "/icons/venus.png")
        self.planetsAction = QAction(icon, "Planetary positions directly overhead", self.iface.mainWindow())
        self.planetsAction.triggered.connect(self.planetPositions)
        self.iface.addPluginToMenu("Earth, sun, moon && planets", self.planetsAction)
        self.toolbar.addAction(self.planetsAction)

        icon = QIcon(os.path.dirname(__file__) + "/icons/info.svg")
        self.solarInfoAction = QAction(icon, "Solar/lunar information", self.iface.mainWindow())
        self.solarInfoAction.triggered.connect(self.solarInfo)
        self.iface.addPluginToMenu("Earth, sun, moon && planets", self.solarInfoAction)
        self.toolbar.addAction(self.solarInfoAction)
    
        # Help
        icon = QIcon(os.path.dirname(__file__) + '/icons/help.svg')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Earth, sun, moon && planets', self.helpAction)

        # Add the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.dayNightAction)
        self.iface.removeToolBarIcon(self.dayNightAction)
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.sunPositionAction)
        self.iface.removeToolBarIcon(self.sunPositionAction)
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.moonPositionAction)
        self.iface.removeToolBarIcon(self.moonPositionAction)
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.planetsAction)
        self.iface.removeToolBarIcon(self.planetsAction)
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.solarInfoAction)
        self.iface.removeToolBarIcon(self.solarInfoAction)
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.helpAction)
        if self.solarInfoDialog:
            self.iface.removeDockWidget(self.solarInfoDialog)
            self.solarInfoDialog = None
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def sunPosition(self):
        processing.execAlgorithmDialog('earthsunmoon:sunposition', {})

    def moonPosition(self):
        processing.execAlgorithmDialog('earthsunmoon:moonposition', {})

    def dayNight(self):
        processing.execAlgorithmDialog('earthsunmoon:daynightterminator', {})

    def planetPositions(self):
        processing.execAlgorithmDialog('earthsunmoon:planetpositions', {})
        
    def solarInfo(self):
        if not self.solarInfoDialog:
            from .infoDialog import SolarInfoDialog
            self.solarInfoDialog = SolarInfoDialog(self.iface, self.iface.mainWindow())
            # self.solarInfoDialog.setFloating(True)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.solarInfoDialog)
        self.solarInfoDialog.show()
        

    def help(self):
        '''Display a help page'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)


