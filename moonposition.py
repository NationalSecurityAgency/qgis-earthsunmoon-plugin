import os
from skyfield.api import load, wgs84

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField, QgsFields, QgsVectorLayer,
    QgsWkbTypes, QgsCoordinateReferenceSystem, QgsRasterMarkerSymbolLayer)

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime
from .utils import epsg4326, settings

class MoonPositionAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to to displaye the moon postion directly overhead.
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
                'Moon Position')
        )

    def processAlgorithm(self, parameters, context, feedback):
        auto_style = self.parameterAsBool(parameters, self.PrmStyle, context)
        dt = self.parameterAsDateTime(parameters, self.PrmDateTime, context)
        utc = dt.toUTC()
        eph = load(settings.ephemPath())
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        moon = eph['moon'] # vector from solar system barycenter to moon
        geocentric_moon = moon - earth # vector from geocenter to moon
        ts = load.timescale()
        date = utc.date()
        time = utc.time()
        t = ts.utc(date.year(), date.month(), date.day(), time.hour(), time.minute(), time.second())
        try:
            moon_position = wgs84.geographic_position_of(geocentric_moon.at(t)) # geographic_position_of method requires a geocentric position
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
        attr = ['Moon',float(moon_position.latitude.degrees), float(moon_position.longitude.degrees), dt.toString('yyyy-MM-dd hh:mm:ss'), utc.toString('yyyy-MM-dd hh:mm:ss')]
        feat.setAttributes(attr)
        pt = QgsPointXY(moon_position.longitude.degrees, moon_position.latitude.degrees)
        feat.setGeometry(QgsGeometry.fromPointXY(pt))
        sink.addFeature(feat)
        if auto_style:
            context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(StylePostProcessor.create())

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'moonposition'

    def displayName(self):
        return 'Moon position directly overhead'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/moon.png')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return MoonPositionAlgorithm()

class StylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        '''symbol = layer.renderer().symbol()
        symbol.setSize(6)
        symbol.setColor(QColor(161,161,177))'''
        path = os.path.join(os.path.dirname(__file__), 'icons/moon.png')
        symbol = QgsRasterMarkerSymbolLayer(path)
        symbol.setSize(7)
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
