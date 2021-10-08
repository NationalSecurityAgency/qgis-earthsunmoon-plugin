import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .sunposition import SunPositionAlgorithm
from .moonposition import MoonPositionAlgorithm
from .daynight import DayNightAlgorithm
from .planetpositions import PlanetPositionsAlgorithm

class EarthSunMoonProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(SunPositionAlgorithm())
        self.addAlgorithm(MoonPositionAlgorithm())
        self.addAlgorithm(DayNightAlgorithm())
        self.addAlgorithm(PlanetPositionsAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/sun.svg')

    def id(self):
        return 'earthsunmoon'

    def name(self):
        return 'Earth, sun, moon & planets'

    def longName(self):
        return self.name()
