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
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication
import processing
# Check to see if the TimeZoneFinder and Skyfield libraries are installed
# If not display a message that they need to be installed first
# import traceback
try:
    from timezonefinder import TimezoneFinder
    from skyfield.api import wgs84
    from jplephem.spk import SPK
    from .functions import InitFunctions, UnloadFunctions
    libraries_found = True
except Exception:
    # traceback.print_exc()
    libraries_found = False

import os
from .utils import settings, SettingsWidget

class EarthSunMoon(object):
    solarInfoDialog = None
    ephemInfoDialog = None
    settingsDialog = None

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()

        # Make sure the path to the ephemeris file exists
        path = settings.ephemDir()
        # if path doesn't exist, make it
        if not os.path.exists(path):
            os.makedirs(path)
        # If the default ephemeris is not in the EarthSunMoon directory copy it to there.
        default_ephem_path = settings.defaultEphemPath()
        if not os.path.exists(default_ephem_path):
            from shutil import copyfile
            src = os.path.join(os.path.dirname(__file__), 'data', settings.defaultEphemFile())
            copyfile(src, default_ephem_path)            

        if libraries_found:
            from .provider import EarthSunMoonProvider
            self.provider = EarthSunMoonProvider()
        else:
            from .provider_limited import EarthSunMoonProvider
            self.provider = EarthSunMoonProvider()

    def initGui(self):
        self.toolbar = self.iface.addToolBar('Earth/Sun/Moon Toolbar')
        self.toolbar.setObjectName('EarthSunMoonToolbar')
    
        icon = QIcon(os.path.dirname(__file__) + "/icons/daynight.png")
        self.dayNightAction = QAction(icon, "Day/Night terminator", self.iface.mainWindow())
        self.dayNightAction.triggered.connect(self.dayNight)
        self.iface.addPluginToMenu("Earth, sun, moon && planets", self.dayNightAction)
        self.toolbar.addAction(self.dayNightAction)

        icon = QIcon(os.path.dirname(__file__) + "/icons/sun_icon.svg")
        self.sunPositionAction = QAction(icon, "Sun position directly overhead", self.iface.mainWindow())
        self.sunPositionAction.triggered.connect(self.sunPosition)
        self.iface.addPluginToMenu("Earth, sun, moon && planets", self.sunPositionAction)
        self.toolbar.addAction(self.sunPositionAction)

        if libraries_found:
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
    
            # Selected ephemeris information
            icon = QIcon(os.path.dirname(__file__) + "/icons/ephem.svg")
            self.ephemAction = QAction(icon, "Ephemeris information", self.iface.mainWindow())
            self.ephemAction.triggered.connect(self.ephemInfo)
            self.iface.addPluginToMenu('Earth, sun, moon && planets', self.ephemAction)
        else:
            icon = QIcon(":images/themes/default/mIndicatorBadLayer.svg")
            self.requirementsActions = QAction(icon, "Install python libraries for more capabilities", self.iface.mainWindow())
            self.requirementsActions.triggered.connect(self.requirements)
            self.iface.addPluginToMenu("Earth, sun, moon && planets", self.requirementsActions)

        # Settings
        icon = QIcon(':/images/themes/default/mActionOptions.svg')
        self.settingsAction = QAction(icon, 'Settings', self.iface.mainWindow())
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('Earth, sun, moon && planets', self.settingsAction)
        
        # Help
        icon = QIcon(os.path.dirname(__file__) + '/icons/help.svg')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Earth, sun, moon && planets', self.helpAction)

        # Add the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

        if libraries_found:
            InitFunctions()

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.dayNightAction)
        self.iface.removeToolBarIcon(self.dayNightAction)
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.sunPositionAction)
        self.iface.removeToolBarIcon(self.sunPositionAction)
        if libraries_found:
            self.iface.removePluginMenu('Earth, sun, moon && planets', self.moonPositionAction)
            self.iface.removeToolBarIcon(self.moonPositionAction)
            self.iface.removePluginMenu('Earth, sun, moon && planets', self.planetsAction)
            self.iface.removeToolBarIcon(self.planetsAction)
            self.iface.removePluginMenu('Earth, sun, moon && planets', self.solarInfoAction)
            self.iface.removeToolBarIcon(self.solarInfoAction)
            self.iface.removePluginMenu('Earth, sun, moon && planets', self.ephemAction)
            if self.solarInfoDialog:
                self.iface.removeDockWidget(self.solarInfoDialog)
                self.solarInfoDialog = None
        else:
            self.iface.removePluginMenu('Earth, sun, moon && planets', self.requirementsActions)
    
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.settingsAction)
        self.iface.removePluginMenu('Earth, sun, moon && planets', self.helpAction)
        del self.toolbar
        QgsApplication.processingRegistry().removeProvider(self.provider)
        if libraries_found:
            UnloadFunctions()

    def requirements(self):
        message = '''
        <p>Enhance this plugin with the <a href="https://timezonefinder.readthedocs.io/en/latest/">TimeZoneFinder</a> and <a href="https://rhodesmill.org/skyfield/">Skyfiled</a> libraries.<br/><br/>
        These libraries can be installed by running the OSGeo4W shell and running 'pip install skyfield timezonefinder' or whatever method you use to install python packages.<p>
        <p>Once the libraries are installed, please restart QGIS.</p>
        '''
        QMessageBox.information(self.iface.mainWindow(), 'How to enhance this plugin', message)

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

    def ephemInfo(self):
        if not self.ephemInfoDialog:
            from .ephemInfo import EphemerisInfo
            self.ephemInfoDialog = EphemerisInfo(self.iface, self.iface.mainWindow())
        self.ephemInfoDialog.show()

    def settings(self):
        if self.settingsDialog is None:
            self.settingsDialog = SettingsWidget(self.iface, self.iface.mainWindow())
        self.settingsDialog.show()

    def help(self):
        '''Display a help page'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)


