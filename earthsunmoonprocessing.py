# -*- coding: utf-8 -*-
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
