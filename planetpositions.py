import os
from datetime import datetime
from skyfield.api import load, wgs84
from skyfield.positionlib import Geocentric

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField, QgsFields, QgsVectorLayer,
    QgsProject, QgsWkbTypes, QgsCoordinateReferenceSystem)

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime
from .utils import epsg4326, ephem_path

class PlanetPositionsAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to to display the planetary postions directly overhead.
    """

    PrmOutputLayer = 'OutputLayer'
    PrmDateTime = 'DateTime'
    PrmStyle = 'Style'

    def initAlgorithm(self, config):

        dt = QDateTime.currentDateTime()
        self.addParameter(
            QgsProcessingParameterDateTime(
                self.PrmDateTime,
                'Select date and time for calculations',
                type=QgsProcessingParameterDateTime.DateTime,
                defaultValue=dt,
                optional=False,
                )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmStyle,
                'Automatically style output',
                True,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                'Planetary Positions')
        )

    def processAlgorithm(self, parameters, context, feedback):
        auto_style = self.parameterAsBool(parameters, self.PrmStyle, context)
        dt = self.parameterAsDateTime(parameters, self.PrmDateTime, context)
        utc = dt.toUTC()
        f = QgsFields()
        f.append(QgsField("name", QVariant.String))
        f.append(QgsField("latitude", QVariant.Double))
        f.append(QgsField("longitude", QVariant.Double))
        f.append(QgsField("datetime", QVariant.String))
        f.append(QgsField("utc", QVariant.String))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, f,
            QgsWkbTypes.Point, epsg4326)
        
        eph = load(ephem_path)
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        ts = load.timescale()
        date = utc.date()
        time = utc.time()
        t_utc = ts.utc(date.year(), date.month(), date.day(), time.hour(), time.minute(), time.second())
        
        f = self.returnPlanetaryZenith('Mercury', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)
        f = self.returnPlanetaryZenith('Venus', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)
        f = self.returnPlanetaryZenith('Mars Barycenter', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)
        f = self.returnPlanetaryZenith('Jupiter Barycenter', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)
        f = self.returnPlanetaryZenith('Saturn Barycenter', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)
        f = self.returnPlanetaryZenith('Uranus Barycenter', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)
        f = self.returnPlanetaryZenith('Neptune Barycenter', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)
        f = self.returnPlanetaryZenith('Pluto Barycenter', eph, earth, t_utc, dt, utc)
        sink.addFeature(f)

        if auto_style:
            context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(StylePostProcessor.create())

        return {self.PrmOutputLayer: dest_id}

    def returnPlanetaryZenith(self, body, eph, earth, t_utc, dt, utc):
        planet = eph[body] # vector from solar system barycenter to planet
        geocentric_planet = planet - earth # vector from geocenter to planet
        planet_subpoint = wgs84.subpoint(geocentric_planet.at(t_utc)) # subpoint method requires a geocentric position
        f = QgsFeature()
        name =  body.split()[0]
        attr = [name, float(planet_subpoint.latitude.degrees), float(planet_subpoint.longitude.degrees), dt.toString('yyyy-MM-dd hh:mm:ss'), utc.toString('yyyy-MM-dd hh:mm:ss')]
        f.setAttributes(attr)
        pt = QgsPointXY(planet_subpoint.longitude.degrees, planet_subpoint.latitude.degrees)
        f.setGeometry(QgsGeometry.fromPointXY(pt))
        return(f)

    def name(self):
        return 'planetpositions'

    def displayName(self):
        return 'Planetary positions directly overhead'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/venus.png')

    '''def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)'''

    def createInstance(self):
        return PlanetPositionsAlgorithm()

class StylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        path = os.path.join(os.path.dirname(__file__), 'data/planet_style.qml')
        layer.loadNamedStyle(path)
        layer.triggerRepaint()

    @staticmethod
    def create() -> 'StylePostProcessor':
        """
        Returns a new instance of the post processor keeping a reference to the sip
        wrapper so that sip doesn't get confused with the Python subclass and call
        the base wrapper implemenation instead.
        """
        StylePostProcessor.instance = StylePostProcessor()
        return StylePostProcessor.instance
