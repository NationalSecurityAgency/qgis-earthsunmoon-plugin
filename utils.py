import os
from qgis.core import QgsCoordinateReferenceSystem


epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

ephem_path = os.path.dirname(__file__) + '/data/de440.bsp'