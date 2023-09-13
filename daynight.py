import os
from datetime import datetime
from .terminator import Terminator


from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField, QgsFields, QgsVectorLayer,
    QgsProject, QgsWkbTypes, QgsCoordinateReferenceSystem, QgsSvgMarkerSymbolLayer)

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime, Qt
from .utils import epsg4326, SolarObj

class DayNightAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to time zone attribute.
    """

    PrmSunOutput = 'SunOutput'
    PrmOutputLine = 'OutputLine'
    PrmOutputPolygons = 'OutputPolygons'
    PrmDateTime = 'DateTime'
    PrmStyle = 'Style'
    PrmShowSun = 'ShowSun'
    PrmCivilTwilight = 'CivilTwilight'
    PrmNauticalTwilight = 'NauticalTwilight'
    PrmAstronomicalTwilight = 'AstronomicalTwilight'
    PrmNight = 'Night'
    PrmDelta = 'Delta'
    PrmClipToCRS = 'ClipToCRS'
    PrmDayNightLine = 'DayNightLine'
    PrmSolarDisk = 'SolarDisk'

    def initAlgorithm(self, config):

        dt = QDateTime.currentDateTime()
        self.addParameter(
            QgsProcessingParameterDateTime(
                self.PrmDateTime,
                'Set date and time',
                type=QgsProcessingParameterDateTime.DateTime,
                defaultValue=dt,
                optional=False,
                )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmShowSun,
                'Sun position',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmDayNightLine,
                'Day, night terminator line',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmCivilTwilight,
                'Civil Twilight',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmNauticalTwilight,
                'Nautical Twilight',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmAstronomicalTwilight,
                'Astronomical Twilight',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmNight,
                'Night',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmDelta,
                'Delta/resoution of polygon (in degrees)',
                QgsProcessingParameterNumber.Double,
                defaultValue=1,
                minValue=0.001,
                maxValue = 10.0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmSolarDisk,
                'Add solar disk diameter for day/night terminator calculation',
                False,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmStyle,
                'Automatically style output',
                True,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmClipToCRS,
                'Clip polygons to project CRS brounds',
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmSunOutput,
                'Sun position')
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLine,
                'Day, night terminator line')
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputPolygons,
                'Twilight and night polygons')
        )

    def processAlgorithm(self, parameters, context, feedback):
        style_layer = self.parameterAsBool(parameters, self.PrmStyle, context)
        solar_disk = self.parameterAsBool(parameters, self.PrmSolarDisk, context)
        clip_to_crs = self.parameterAsBool(parameters, self.PrmClipToCRS, context)
        show_sun = self.parameterAsBool(parameters, self.PrmShowSun, context)
        day_night_line = self.parameterAsBool(parameters, self.PrmDayNightLine, context)
        civil_twilight = self.parameterAsBool(parameters, self.PrmCivilTwilight, context)
        nautical_twilight = self.parameterAsBool(parameters, self.PrmNauticalTwilight, context)
        astronomical_twilight = self.parameterAsBool(parameters, self.PrmAstronomicalTwilight, context)
        night = self.parameterAsBool(parameters, self.PrmNight, context)
        delta = self.parameterAsDouble(parameters, self.PrmDelta, context)
        qdt = self.parameterAsDateTime(parameters, self.PrmDateTime, context)
        qutc = qdt.toUTC()
        dt = qdt.toPyDateTime()
        utc = qutc.toPyDateTime()
        f = QgsFields()
        f.append(QgsField("object_id", QVariant.Int))
        f.append(QgsField("name", QVariant.String))
        f.append(QgsField("timestamp", QVariant.Double))
        f.append(QgsField("datetime", QVariant.String))
        f.append(QgsField("utc", QVariant.String))
        project_crs = QgsProject.instance().crs()
        if clip_to_crs and project_crs != epsg4326:
            project_bounds = project_crs.bounds()
        else:
            project_bounds = None
        
        if civil_twilight or nautical_twilight or astronomical_twilight or night:
            has_polygons = True
        else:
            has_polygons = False
        if show_sun:
            (sink_sun, dest_id_sun) = self.parameterAsSink(
                parameters, self.PrmSunOutput, context, f,
                QgsWkbTypes.Point, epsg4326)
            lon, lat = Terminator.solar_position(utc)
            pt = QgsPointXY(float(lon), float(lat))
            attr = [SolarObj.SUN.value, 'Sun', utc.timestamp(), qdt.toString('yyyy-MM-dd hh:mm:ss'), qutc.toString('yyyy-MM-ddThh:mm:ssZ')]
            feat = QgsFeature()
            feat.setAttributes(attr)
            feat.setGeometry(QgsGeometry.fromPointXY(pt))
            sink_sun.addFeature(feat)

        if solar_disk:
            sun_width = 0.833
        else:
            sun_width = 0

        if day_night_line:
            (sink_line, dest_id_line) = self.parameterAsSink(
                parameters, self.PrmOutputLine, context, f,
                QgsWkbTypes.LineString, epsg4326)
            geom = self.dayNightLineGeom(utc, delta, project_bounds, sun_width)
            attr = [SolarObj.DAY_NIGHT.value, 'Day, Night', utc.timestamp(), qdt.toString('yyyy-MM-dd hh:mm:ss'), qutc.toString('yyyy-MM-ddThh:mm:ssZ')]
            feat = QgsFeature()
            feat.setAttributes(attr)
            feat.setGeometry(geom)
            sink_line.addFeature(feat)
            

        if has_polygons:
            (sink, dest_id) = self.parameterAsSink(
                parameters, self.PrmOutputPolygons, context, f,
                QgsWkbTypes.MultiPolygon, epsg4326)

        if civil_twilight:
            t = Terminator(utc, delta=delta, refraction=sun_width)
            geom = self.arrayToGeom(t.polygons, project_bounds)
            if geom:
                attr = [SolarObj.CIVIL_TWILIGHT.value, 'Civil Twilight', utc.timestamp(), qdt.toString('yyyy-MM-dd hh:mm:ss'), qutc.toString('yyyy-MM-ddThh:mm:ssZ')]
                feat = QgsFeature()
                feat.setAttributes(attr)
                feat.setGeometry(geom)
                sink.addFeature(feat)

        if nautical_twilight:
            t = Terminator(utc, delta=delta, refraction=6)
            geom = self.arrayToGeom(t.polygons, project_bounds)
            if geom:
                attr = [SolarObj.NAUTICAL_TWILIGHT.value, 'Nautical Twilight', utc.timestamp(), qdt.toString('yyyy-MM-dd hh:mm:ss'), qutc.toString('yyyy-MM-ddThh:mm:ssZ')]
                feat = QgsFeature()
                feat.setAttributes(attr)
                feat.setGeometry(geom)
                sink.addFeature(feat)

        if astronomical_twilight:
            t = Terminator(utc, delta=delta, refraction=12)
            geom = self.arrayToGeom(t.polygons, project_bounds)
            if geom:
                attr = [SolarObj.ASTRONOMICAL_TWILIGHT.value, 'Astronomical Twilight', utc.timestamp(), qdt.toString('yyyy-MM-dd hh:mm:ss'), qutc.toString('yyyy-MM-ddThh:mm:ssZ')]
                feat = QgsFeature()
                feat.setAttributes(attr)
                feat.setGeometry(geom)
                sink.addFeature(feat)

        if night:
            t = Terminator(utc, delta=delta, refraction=18)
            geom = self.arrayToGeom(t.polygons, project_bounds)
            if geom:
                attr = [SolarObj.NIGHT.value, 'Night', utc.timestamp(), qdt.toString('yyyy-MM-dd hh:mm:ss'), qutc.toString('yyyy-MM-ddThh:mm:ssZ')]
                feat = QgsFeature()
                feat.setAttributes(attr)
                feat.setGeometry(geom)
                sink.addFeature(feat)
        
        r = {}
        if show_sun:
            if style_layer and context.willLoadLayerOnCompletion(dest_id_sun):
                context.layerToLoadOnCompletionDetails(dest_id_sun).setPostProcessor(SunStylePostProcessor.create())
            r[self.PrmSunOutput] = dest_id_sun
            
        if has_polygons:
            if style_layer and context.willLoadLayerOnCompletion(dest_id):
                context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(StylePostProcessor.create())
            r[self.PrmOutputPolygons] = dest_id
        if day_night_line:
            if style_layer and context.willLoadLayerOnCompletion(dest_id_line):
                context.layerToLoadOnCompletionDetails(dest_id_line).setPostProcessor(LineStylePostProcessor.create())
            r[self.PrmOutputLine] = dest_id_line

        return(r)

    def dayNightLineGeom(self, utc: datetime, delta: float, project_bounds=None, sun_width: float=0):
        t = Terminator(utc, delta=delta, refraction=sun_width)
        # We will only have one terminator polygon with refraction=0
        p = t.edges[0]
        pts = []
        for i in range(0, len(p[0])):
            lon = p[0][i]
            lat = p[1][i]
            pts.append(QgsPointXY(lon, lat))
        geom = QgsGeometry.fromPolylineXY(pts)
        if project_bounds:
            geom2 = geom.clipped(project_bounds) 
            return(geom2)
        return(geom)

    def arrayToGeom(self, varray, project_bounds=None):
        mpts = []
        for p in varray:
            pts = []
            '''previous_lat = 999
            previous_lon = 999'''
            for i in range(len(p[0])):
                lon = p[0][i]
                lat = p[1][i]
                '''if lon == previous_lon and lat == previous_lat:
                    continue
                previous_lat = lat
                previous_lon = lon'''
                pts.append(QgsPointXY(lon, lat))
            # Make sure it is a closed polygon
            '''if pts[0] != pts[-1]:
                pts.append(pts[0])'''
            mpts.append([pts])
        geom = QgsGeometry.fromMultiPolygonXY(mpts)
        if project_bounds:
            geom2 = geom.clipped(project_bounds) 
            return(geom2)
        return(geom)

    def name(self):
        return 'daynightterminator'

    def displayName(self):
        return 'Day/Night terminator'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/daynight.png')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return DayNightAlgorithm()

class StylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        symbol = layer.renderer().symbol()
        symbol.setColor(QColor(0,0,0,60))
        symbol_layer = symbol.symbolLayer(0)
        symbol_layer.setStrokeStyle(Qt.NoPen)
            

    @staticmethod
    def create() -> 'StylePostProcessor':
        """
        Returns a new instance of the post processor keeping a reference to the sip
        wrapper so that sip doesn't get confused with the Python subclass and call
        the base wrapper implemenation instead.
        """
        StylePostProcessor.instance = StylePostProcessor()
        return StylePostProcessor.instance


class LineStylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        symbol = layer.renderer().symbol()
        symbol.setColor(QColor(0,0,0,255))
        symbol.setWidth(0.4)
            

    @staticmethod
    def create() -> 'LineStylePostProcessor':
        """
        Returns a new instance of the post processor keeping a reference to the sip
        wrapper so that sip doesn't get confused with the Python subclass and call
        the base wrapper implemenation instead.
        """
        LineStylePostProcessor.instance = LineStylePostProcessor()
        return LineStylePostProcessor.instance

class SunStylePostProcessor(QgsProcessingLayerPostProcessorInterface):
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
    def create() -> 'SunStylePostProcessor':
        """
        Returns a new instance of the post processor keeping a reference to the sip
        wrapper so that sip doesn't get confused with the Python subclass and call
        the base wrapper implemenation instead.
        """
        SunStylePostProcessor.instance = SunStylePostProcessor()
        return SunStylePostProcessor.instance
