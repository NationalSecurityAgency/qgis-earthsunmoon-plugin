import os
from qgis.core import QgsCoordinateReferenceSystem, QgsApplication


epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

# ephem_path = os.path.join(QgsApplication.qgisSettingsDirPath(), "EarthSunMoon")
ephem_file = "de440.bsp"
ephem_path = os.path.dirname(__file__) + '/data/de440.bsp'
