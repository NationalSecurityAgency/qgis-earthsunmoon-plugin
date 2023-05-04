# -*- coding: utf-8 -*-
from qgis.core import QgsApplication
# Check to see if the TimeZoneFinder and Skyfield libraries are installed
try:
    from timezonefinder import TimezoneFinder
    from skyfield.api import wgs84
    from jplephem.spk import SPK
    libraries_found = True
    from .provider import EarthSunMoonProvider
except Exception:
    # traceback.print_exc()
    libraries_found = False

class EarthSunMoon(object):
    def __init__(self):
        self.provider = None

    def initProcessing(self):
        if libraries_found:
            self.provider = EarthSunMoonProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
