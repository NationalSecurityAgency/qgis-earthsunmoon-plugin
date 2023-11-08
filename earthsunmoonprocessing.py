# -*- coding: utf-8 -*-
"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import QgsApplication
# Check to see if the TimeZoneFinder and Skyfield libraries are installed
try:
    from timezonefinder import TimezoneFinder
    from skyfield.api import wgs84
    from jplephem.spk import SPK
    from .provider import EarthSunMoonProvider
except Exception:
    # traceback.print_exc()
    from .provider_limited import EarthSunMoonProvider

class EarthSunMoon(object):
    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = EarthSunMoonProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
