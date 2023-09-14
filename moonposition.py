import os
from datetime import timedelta
from zoneinfo import ZoneInfo
from skyfield.api import load, wgs84

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField, QgsFields, QgsVectorLayer,
    QgsWkbTypes, QgsCoordinateReferenceSystem, QgsRasterMarkerSymbolLayer)

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterString,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime
from .utils import epsg4326, settings, SolarObj, parse_timeseries

class MoonPositionAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to to displaye the moon postion directly overhead.
    """

    PrmOutputLayer = 'OutputLayer'
    PrmDateTime = 'DateTime'
    PrmTimeSeries = 'TimeSeries'
    PrmTimeIncrement = 'TimeIncrement'
    PrmTimeDuration = 'TimeDuration'
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
        param = QgsProcessingParameterBoolean(
                self.PrmTimeSeries,
                'Create moon time series',
                False,
                optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        param = QgsProcessingParameterString(
                self.PrmTimeIncrement,
                'Time increment between observations (DD:HH:MM:SS)',
                defaultValue='00:01:00:00',
                optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterString(
                self.PrmTimeDuration,
                'Total duration for moon positions (DD:HH:MM:SS)',
                defaultValue='1:00:00:00',
                optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                'Moon Position')
        )

    def processAlgorithm(self, parameters, context, feedback):
        auto_style = self.parameterAsBool(parameters, self.PrmStyle, context)
        qdt = self.parameterAsDateTime(parameters, self.PrmDateTime, context)
        generate_timeseries = self.parameterAsBool(parameters, self.PrmTimeSeries, context)
        time_increment = self.parameterAsString(parameters, self.PrmTimeIncrement, context)
        time_duration = self.parameterAsString(parameters, self.PrmTimeDuration, context)
        if generate_timeseries:
            num_events, time_delta = parse_timeseries(time_increment, time_duration)
        else:
            num_events = 1
            time_delta = 0
        if num_events == -1:
            raise QgsProcessingException('Invalid time increment and/or duration.')
        feedback.pushInfo('Number of moon observations: {}'.format(num_events))

        f = QgsFields()
        f.append(QgsField("object_id", QVariant.Int))
        f.append(QgsField("name", QVariant.String))
        f.append(QgsField("latitude", QVariant.Double))
        f.append(QgsField("longitude", QVariant.Double))
        f.append(QgsField("timestamp", QVariant.Double))
        f.append(QgsField("datetime", QVariant.String))
        f.append(QgsField("utc", QVariant.String))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, f,
            QgsWkbTypes.Point, epsg4326)

        qutc = qdt.toUTC()
        utc = qutc.toPyDateTime()
        utc = utc.replace(tzinfo=ZoneInfo('UTC'))  # Make sure it is an aware UTC
        eph = load(settings.ephemPath())
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        moon = eph['moon'] # vector from solar system barycenter to moon
        geocentric_moon = moon - earth # vector from geocenter to moon
        ts = load.timescale()

        for i in range(num_events):
            delta = i*time_delta
            utc_cur = utc + timedelta(seconds=delta)
            t = ts.from_datetime(utc_cur)
            try:
                moon_position = wgs84.geographic_position_of(geocentric_moon.at(t)) # geographic_position_of method requires a geocentric position
            except Exception:
                feedback.reportError('The ephemeris file does not cover the selected date range. Go to Settings and download and select an ephemeris file that contains your date range.')
                return {}

            feat = QgsFeature()
            attr = [SolarObj.MOON.value, 'Moon', float(moon_position.latitude.degrees), float(moon_position.longitude.degrees), utc_cur.timestamp(), qdt.toString('yyyy-MM-dd hh:mm:ss'), qutc.toString('yyyy-MM-dd hh:mm:ss')]
            feat.setAttributes(attr)
            pt = QgsPointXY(moon_position.longitude.degrees, moon_position.latitude.degrees)
            feat.setGeometry(QgsGeometry.fromPointXY(pt))
            sink.addFeature(feat)
        if auto_style and context.willLoadLayerOnCompletion(dest_id):
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
