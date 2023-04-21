import os
import numpy as np
from skyfield.api import load, load_file, wgs84
from skyfield.positionlib import Geocentric

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField, QgsFields, QgsVectorLayer,
    QgsProject, QgsWkbTypes, QgsCoordinateReferenceSystem)

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime, Qt
from .utils import epsg4326

global_style_type = 0

class DayNightAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to time zone attribute.
    """

    PrmOutputLayer = 'OutputLayer'
    PrmDateTime = 'DateTime'
    PrmShapeType = 'ShapeType'
    PrmStyle = 'Style'
    PrmCivilTwilight = 'CivilTwilight'
    PrmNauticalTwilight = 'NauticalTwilight'
    PrmAstronomicalTwilight = 'AstronomicalTwilight'
    PrmNight = 'Night'
    PrmClipToCRS = 'ClipToCRS'
    CivilTwilight = 0
    NauticalTwilight = 1
    AstronomicalTwilight = 2
    Night = 3
    

    def initAlgorithm(self, config):

        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmShapeType,
                'Day/Night feature type',
                options=['Night Area Polygons', 'Day Area Polygon', 'Division Lines', 'Points'],
                defaultValue=0,
                optional=False)
        )
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
                self.PrmCivilTwilight,
                'Show night region: Civil Twilight',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmNauticalTwilight,
                'Show night region: Nautical Twilight',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmAstronomicalTwilight,
                'Show night region: Astronomical Twilight',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmNight,
                'Show night region: Night',
                True,
                optional=True)
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
                self.PrmOutputLayer,
                'Day/Night Terminator')
        )

    def processAlgorithm(self, parameters, context, feedback):
        global global_style_type
        shape_type = self.parameterAsInt(parameters, self.PrmShapeType, context)
        style_layer = self.parameterAsBool(parameters, self.PrmStyle, context)
        clip_to_crs = self.parameterAsBool(parameters, self.PrmClipToCRS, context)
        civil_twilight = self.parameterAsBool(parameters, self.PrmCivilTwilight, context)
        nautical_twilight = self.parameterAsBool(parameters, self.PrmNauticalTwilight, context)
        astronomical_twilight = self.parameterAsBool(parameters, self.PrmAstronomicalTwilight, context)
        night = self.parameterAsBool(parameters, self.PrmNight, context)
        global_style_type = shape_type
        dt = self.parameterAsDateTime(parameters, self.PrmDateTime, context)
        utc = dt.toUTC()
        f = QgsFields()
        if shape_type == 3:
            f.append(QgsField("id", QVariant.Int))
        f.append(QgsField("feature", QVariant.String))
        f.append(QgsField("datetime", QVariant.String))
        f.append(QgsField("utc", QVariant.String))
        project_crs = QgsProject.instance().crs()
        project_bounds = None
        if clip_to_crs and project_crs != epsg4326:
            project_bounds = project_crs.bounds()
        else:
            clip_to_crs = False  # Don't need to clip even if specified because CRS is 4326
            

        if shape_type == 2:  # Sun Line is a line string
            (sink, dest_id) = self.parameterAsSink(
                parameters, self.PrmOutputLayer, context, f,
                QgsWkbTypes.MultiLineString, epsg4326)
        if shape_type == 3:  # Points
            (sink, dest_id) = self.parameterAsSink(
                parameters, self.PrmOutputLayer, context, f,
                QgsWkbTypes.Point, epsg4326)
        else:
            (sink, dest_id) = self.parameterAsSink(
                parameters, self.PrmOutputLayer, context, f,
                QgsWkbTypes.MultiPolygon, epsg4326)

        eph = load_file(os.path.dirname(__file__) + '/data/de440.bsp')
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        sun = eph['sun'] # vector from solar system barycenter to sun
        geocentric_sun = sun - earth # vector from geocenter to sun
        ts = load.timescale()
        date = utc.date()
        time = utc.time()
        t = ts.utc(date.year(), date.month(), date.day(), time.hour(), time.minute(), time.second())
        if shape_type == 1: # Day
            self.getDayNightFeature(shape_type, geocentric_sun, t, self.CivilTwilight, dt, utc, project_bounds, sink)
            # sink.addFeature(feat)
        else:
            if civil_twilight:
                self.getDayNightFeature(shape_type, geocentric_sun, t, self.CivilTwilight, dt, utc, project_bounds, sink)
                # sink.addFeature(feat)
            if nautical_twilight:
                self.getDayNightFeature(shape_type, geocentric_sun, t, self.NauticalTwilight, dt, utc, project_bounds, sink)
                # sink.addFeature(feat)
            if astronomical_twilight:
                self.getDayNightFeature(shape_type, geocentric_sun, t, self.AstronomicalTwilight, dt, utc, project_bounds, sink)
                # sink.addFeature(feat)
            if night:
                self.getDayNightFeature(shape_type, geocentric_sun, t, self.Night, dt, utc, project_bounds, sink)
                # sink.addFeature(feat)
        
        if style_layer:
            context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(StylePostProcessor.create())

        return {self.PrmOutputLayer: dest_id}
        
    def getDayNightFeature(self, shape_type, geocentric_sun, t, area_type, dt, utc, project_bounds, sink):
        if shape_type == 1:
            terminator_angle_from_sun = 90.833 # 90 degrees + sun's semidiameter + refraction at horizon
            feature_name = "Day"
        else:
            if area_type == self.CivilTwilight:
                terminator_angle_from_sun = 90.833 # 90 degrees + sun's semidiameter + refraction at horizon
                # terminator_angle_from_sun = 90
                feature_name = "Civil twilight"
            elif area_type == self.NauticalTwilight:
                terminator_angle_from_sun = 96 # 90 degrees + 6 for start of nautical Twilight
                feature_name = "Nautical twilight"
            elif area_type == self.AstronomicalTwilight:
                terminator_angle_from_sun = 102 # 90 degrees + 12 for start of astronomical Twilight
                feature_name = "Astronomical twilight"
            else:
                terminator_angle_from_sun = 108 # 90 degrees + 16 for start of night
                feature_name = "Night"

        sun_vec = geocentric_sun.at(t).position.au # numpy array of sun's position vector
        normal_vec = np.cross(sun_vec, np.array([1,0,0])) # vector normal to sun position and x-axis
        first_terminator_vec = rotation_matrix_around_axis(normal_vec, terminator_angle_from_sun) @ sun_vec # arbitrary first position on terminator

        date_line = QgsGeometry.fromPolylineXY([QgsPointXY(180,-90), QgsPointXY(180,+90)])
        num_points_on_terminator = 200
        pts_results = []
        
        for angle in np.linspace(0, 360, num_points_on_terminator):
            terminator_vector = rotation_matrix_around_axis(sun_vec, angle) @ first_terminator_vec
            # terminator_vector = rotation_matrix_around_axis(sun_vec, angle) @ normal_vec
            terminator_position = Geocentric(terminator_vector, t=t)
            geographic_position = wgs84.geographic_position_of(terminator_position)
            lon = geographic_position.longitude.degrees
            lat = geographic_position.latitude.degrees
            # print('lat: {} lon: {}'.format(lat,lon))
            pts_results.append(QgsPointXY(lon, lat))
        
        if shape_type == 3:
            for i, pt in enumerate(pts_results):
                feat = QgsFeature()
                attr = [i, feature_name, dt.toString('yyyy-MM-dd hh:mm:ss'), utc.toString('yyyy-MM-ddThh:mm:ssZ')]
                feat.setAttributes(attr)
                feat.setGeometry(QgsGeometry.fromPointXY(pt))
                sink.addFeature(feat)
            return

        # Check to see if the values are increasing or decreasing
        is_positive = CheckDirection(pts_results)
        if not is_positive:
            pts_results.reverse()
        # Fix the list when it crosses the international date line
        last = -180
        index = -1
        for i, pt in enumerate(pts_results):
            if pt.x() < last:
                index = i
                break
            else:
                last = pt.x()
        if index != -1:
            pts = pts_results[index:] + pts_results[0:index]
        else:
            pts = pts_results
        first_pt = pts[0]
        last_pt = pts[-1]
        # There is no guarentee that points will land on the -180 to 180 boundary
        # Here we make sure we have those points added.
        if first_pt.x() == -180.0:
            if last_pt.x() == 180.0:
                terminator_pts = pts
            else:
                pt_last = QgsPointXY(180.0, first_pt.y())
                terminator_pts = pts + [pt_last]
        elif last_pt.x() == 180.0:
                pt_first = QgsPointXY(-180.0, last_pt.y())
                terminator_pts = [pt_first] + pts
        else: # Find the point on the international dateline crossing
            first_pt = QgsPointXY(first_pt.x()+360.0, first_pt.y()) # Make this so it isn't negative
            datelinecross = QgsGeometry.fromPolylineXY([last_pt, first_pt])
            intersect_pt = date_line.intersection(datelinecross).asPoint() # Retruns geometry of point intersections
            pt_first = QgsPointXY(-180.0, intersect_pt.y())
            pt_last = QgsPointXY(180.0, intersect_pt.y())
            terminator_pts = [pt_first] + pts + [pt_last]
        feat = QgsFeature()
        attr = [feature_name, dt.toString('yyyy-MM-dd hh:mm:ss'), utc.toString('yyyy-MM-ddThh:mm:ssZ')]
        feat.setAttributes(attr)
        if shape_type == 0:  # Night area polygon
            if is_positive:
                extra = [QgsPointXY(180.0, -90), QgsPointXY(-180, -90), QgsPointXY(-180, terminator_pts[0].y())]
            else:
                extra = [QgsPointXY(180.0, 90), QgsPointXY(-180, 90), QgsPointXY(-180, terminator_pts[0].y())]
            geom = QgsGeometry.fromMultiPolygonXY([[terminator_pts + extra]])
            if project_bounds:  # If true we are cliping to the project bounds
                geom2 = geom.clipped(project_bounds)
                if geom2.type() == QgsWkbTypes.PolygonGeometry:
                    geom = geom2
            feat.setGeometry(geom)
        elif shape_type == 1:  # Day area polygon
            if is_positive:
                extra = [QgsPointXY(180.0, 90), QgsPointXY(-180, 90), QgsPointXY(-180, terminator_pts[0].y())]
            else:
                extra = [QgsPointXY(180.0, -90), QgsPointXY(-180, -90), QgsPointXY(-180, terminator_pts[0].y())]
            geom = QgsGeometry.fromMultiPolygonXY([[terminator_pts + extra]])
            if project_bounds:  # If true we are cliping to the project bounds
                geom2 = geom.clipped(project_bounds)
                if not geom2.isNull():
                    geom = geom2
            feat.setGeometry(geom)
        else:  # Sun line - line string
            feat.setGeometry(QgsGeometry.fromMultiPolylineXY([terminator_pts]))

        sink.addFeature(feat)

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
        if global_style_type == 0:
            symbol.setColor(QColor(0,0,0,30))
            symbol_layer = symbol.symbolLayer(0)
            symbol_layer.setStrokeStyle(Qt.NoPen)
        elif global_style_type == 1:
            layer.setOpacity(0.25)
            symbol.setColor(QColor(255,255,255))
        else:
            symbol.setColor(QColor('#000000'))
            

    @staticmethod
    def create() -> 'StylePostProcessor':
        """
        Returns a new instance of the post processor keeping a reference to the sip
        wrapper so that sip doesn't get confused with the Python subclass and call
        the base wrapper implemenation instead.
        """
        StylePostProcessor.instance = StylePostProcessor()
        return StylePostProcessor.instance

def CheckDirection(pts):
    cnt=0
    last = pts[0].x()
    for i in range(1,4):
        if pts[i].x() > last:
            cnt += 1
        last = pts[i].x()
    if cnt >= 2:
        return(True)
    return(False)
    
def cross_product_matrix(a):
    """ computes the cross product matrix

    see https://en.wikipedia.org/wiki/Cross_product#Conversion_to_matrix_multiplication
    code from https://stackoverflow.com/questions/66707295/numpy-cross-product-matrix-function
    """
    return np.cross(a, np.identity(3) * -1)

def rotation_matrix_around_axis(axis_vector, rotation_degrees):
    """ creates a rotation matrix that rotates around a given axis

    see https://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle
    """
    rotation_radians = rotation_degrees / 180 * np.pi
    return (
        np.cos(rotation_radians) * np.identity(3)
        + np.sin(rotation_radians) * cross_product_matrix(axis_vector)
        + (1 - np.cos(rotation_radians)) * np.outer(axis_vector, axis_vector)
        )
