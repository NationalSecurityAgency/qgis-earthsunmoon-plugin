import os
from datetime import datetime
from skyfield.api import Loader, load, wgs84
from skyfield.positionlib import Geocentric

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField, QgsFields, QgsVectorLayer,
    QgsWkbTypes, QgsCoordinateReferenceSystem, QgsSvgMarkerSymbolLayer)

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime
from .utils import epsg4326, settings

class SunPositionAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to display the sun directly overhead.
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
                'Sun Position')
        )

    def processAlgorithm(self, parameters, context, feedback):
        auto_style = self.parameterAsBool(parameters, self.PrmStyle, context)
        dt = self.parameterAsDateTime(parameters, self.PrmDateTime, context)
        utc = dt.toUTC()
        eph = load(settings.ephemPath())
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        sun = eph['sun'] # vector from solar system barycenter to sun
        geocentric_sun = sun - earth # vector from geocenter to sun
        ts = load.timescale()
        date = utc.date()
        time = utc.time()
        t = ts.utc(date.year(), date.month(), date.day(), time.hour(), time.minute(), time.second())
        try:
            sun_position = wgs84.geographic_position_of(geocentric_sun.at(t)) # geographic_position_of method requires a geocentric position
        except Exception:
            feedback.reportError('The ephemeris file does not cover the selected date range. Go to Settings and download and select an ephemeris file that contains your date range.')
            return {}

        f = QgsFields()
        f.append(QgsField("name", QVariant.String))
        f.append(QgsField("latitude", QVariant.Double))
        f.append(QgsField("longitude", QVariant.Double))
        f.append(QgsField("datetime", QVariant.String))
        f.append(QgsField("utc", QVariant.String))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, f,
            QgsWkbTypes.Point, epsg4326)
        
        feat = QgsFeature()
        attr = ['Sun', float(sun_position.latitude.degrees), float(sun_position.longitude.degrees), dt.toString('yyyy-MM-dd hh:mm:ss'), utc.toString('yyyy-MM-dd hh:mm:ss')]
        feat.setAttributes(attr)
        pt = QgsPointXY(sun_position.longitude.degrees, sun_position.latitude.degrees)
        feat.setGeometry(QgsGeometry.fromPointXY(pt))
        sink.addFeature(feat)
        if auto_style and context.willLoadLayerOnCompletion(dest_id):
            context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(StylePostProcessor.create())

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'sunposition'

    def displayName(self):
        return 'Sun position directly overhead'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/sun.svg')

    '''def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)'''

    def createInstance(self):
        return SunPositionAlgorithm()

class StylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        path = os.path.join(os.path.dirname(__file__), 'icons/sun.svg')
        symbol = QgsSvgMarkerSymbolLayer(path)
        symbol.setSize(10)
        layer.renderer().symbol().changeSymbolLayer(0, symbol )
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
