import os
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo, available_timezones
from skyfield.api import load, load_file, wgs84
from skyfield import almanac
from timezonefinder import TimezoneFinder

from qgis.PyQt.QtGui import QIcon, QFont, QColor
from qgis.PyQt.QtWidgets import QDockWidget, QApplication
from qgis.PyQt.QtCore import pyqtSlot, Qt, QTime, QDate
from qgis.PyQt.uic import loadUiType
from qgis.core import Qgis, QgsPointXY, QgsLineString, QgsMultiPolygon, QgsPolygon, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsRubberBand
from .captureCoordinate import CaptureCoordinate
from .utils import epsg4326, settings
from .wintz import win_tz_map
from .dms import parseDMSString

# import traceback

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/info.ui'))

class SolarInfoDialog(QDockWidget, FORM_CLASS):
    def __init__(self, iface, parent):
        super(SolarInfoDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.savedMapTool = None
        self.cur_location = None
        self.tzf = TimezoneFinder()
        
        # Set up a polygon rubber band
        self.rubber = QgsRubberBand(self.canvas)
        self.rubber.setColor(QColor(255, 70, 0, 200))
        self.rubber.setWidth(3)
        self.rubber.setBrushStyle(Qt.NoBrush)

        # Set up a connection with the coordinate capture tool
        self.captureCoordinate = CaptureCoordinate(self.canvas)
        self.captureCoordinate.capturePoint.connect(self.capturedPoint)
        self.captureCoordinate.captureStopped.connect(self.stopCapture)
        self.coordCaptureButton.clicked.connect(self.startCapture)

        self.dateEdit.setCalendarPopup(True)
        self.coordCaptureButton.setIcon(QIcon(os.path.dirname(__file__) + "/icons/coordCapture.svg"))
        self.currentDateTimeButton.setIcon(QIcon(os.path.dirname(__file__) + "/icons/CurrentTime.png"))
        self.coordLineEdit.returnPressed.connect(self.coordCommitButton)

        self.dt_utc = datetime.now(ZoneInfo("UTC"))
        self.initialTimeZone()

    def showEvent(self, e):
        self.dt_utc = datetime.now(ZoneInfo("UTC"))
        self.updateGuiDateTime()

    def closeEvent(self, e):
        if self.savedMapTool:
            self.canvas.setMapTool(self.savedMapTool)
            self.savedMapTool = None
        self.rubber.reset()
        QDockWidget.closeEvent(self, e)

    def initialTimeZone(self):
        """
        This is to get a standardized UTC time and time zone from the system time
        that conforms to the known timezones used by zoneinfo. At bare minimum the
        system time zone offset is used. Timezones are a pain.
        """
        tz = tzlocal()
        dt = datetime.now(tz)
        try:
            name = dt.tzinfo.zone
        except Exception:
            name = dt.tzname()
        if name in win_tz_map:
            name = win_tz_map[name]
        if name not in available_timezones():
            offset = int(dt.tzinfo.utcoffset(dt).total_seconds()/3600.0)
            name = 'Etc/GMT{:+d}'.format(-offset)
        self.cur_tzname = name
        self.tz = ZoneInfo(name)

    def getLocalDateTime(self):
        dt = self.dt_utc.astimezone(self.tz)
        return(dt)

    def updateGuiDateTime(self):
        self.timezoneEdit.setText(self.cur_tzname)
        dt = self.dt_utc.astimezone(self.tz)
        offset = dt.strftime("%z")
        self.tzOffsetEdit.setText(offset)
        self.dateEdit.blockSignals(True)
        self.timeEdit.blockSignals(True)
        if self.useUtcCheckBox.isChecked():
            self.dateEdit.setDate(QDate(self.dt_utc.year, self.dt_utc.month, self.dt_utc.day))
            self.timeEdit.setTime(QTime(self.dt_utc.hour, self.dt_utc.minute, self.dt_utc.second))
        else:
            self.dateEdit.setDate(QDate(dt.year, dt.month, dt.day))
            self.timeEdit.setTime(QTime(dt.hour, dt.minute, dt.second))
        self.dateEdit.blockSignals(False)
        self.timeEdit.blockSignals(False)

    def updateSunInfo(self):
        self.updateGuiDateTime()
        self.clearInfo()
        try:
            if self.cur_location:
                # Set coordinate
                coord = '{:.8f}, {:.8f}'.format(self.cur_location.y(), self.cur_location.x())
                self.coordLineEdit.setText(coord)
                loc = wgs84.latlon(self.cur_location.y(), self.cur_location.x())
                ts = settings.timescale()
                dt = self.getLocalDateTime()
                year = dt.year
                cur_time = ts.from_datetime(dt)
                
                # Load  ephemeris
                eph = settings.ephem()
                earth = eph['earth']
                sun = eph['sun']
                moon = eph['moon']
                
                # Get sun azimuth and altitude
                observer = earth + loc
                astrometric = observer.at(cur_time).observe(sun)
                alt, az, d = astrometric.apparent().altaz()
                self.sunAzimuthLabel.setText('{:.6f}'.format(az.degrees))
                self.sunElevationLabel.setText('{:.6f}'.format(alt.degrees))
            
                # Get moon azimuth and altitude
                astrometric = observer.at(cur_time).observe(moon)
                alt, az, d = astrometric.apparent().altaz()
                self.moonAzimuthLabel.setText('{:.6f}'.format(az.degrees))
                self.moonElevationLabel.setText('{:.6f}'.format(alt.degrees))
                
                # Get solar noon
                midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                next_midnight = midnight + timedelta(days=1)
                t0 = ts.from_datetime(midnight) # Starting time to search for events
                t1 = ts.from_datetime(next_midnight) # Ending time to search for events
                
                f = almanac.meridian_transits(eph, sun, loc)
                times, events = almanac.find_discrete(t0, t1, f)
                if times:
                    # Select transits instead of antitransits.
                    times = times[events == 1]
                    t = times[0]
                    self.noonLabel.setText(self.formatDateTime(t))
                
                # Find the twlight hours
                f = almanac.dark_twilight_day(eph, loc)
                times, events = almanac.find_discrete(t0, t1, f)
                previous_e = f(t0)
                has_start = False
                has_end = False
                for t, e in zip(times, events):
                    if previous_e < e:
                        if e == 4: # Day starts
                            day_start = t
                            has_start = True
                            self.sunriseLabel.setText(self.formatDateTime(t))
                        elif e == 3: # Dawn
                            self.dawnLabel.setText(self.formatDateTime(t))
                    else:
                        if e == 3: # Civil twilight starts
                            day_end = t
                            has_end = True
                            self.civilTwilightLabel.setText(self.formatDateTime(t))
                            self.sunsetLabel.setText(self.formatDateTime(t))
                        elif e == 2: # Nautical twilight starts
                            self.nauticalTwilightLabel.setText(self.formatDateTime(t))
                        elif e == 1: # Astronomical twilight starts
                            self.astronomicalTwilightLabel.setText(self.formatDateTime(t))
                        elif e == 0: # Night starts
                            self.nightLabel.setText(self.formatDateTime(t))
                    previous_e = e
                if has_start and has_end:
                    diff = relativedelta(day_end.utc_datetime(), day_start.utc_datetime())
                    if diff.days == 1:
                        str = '24 hours'
                    else:
                        str = '{}h {}m {}s'.format(diff.hours, diff.minutes, diff.seconds)
                    self.daylightDurationLabel.setText(str)
                else:
                    f = almanac.sunrise_sunset(eph, loc)
                    str = 'Polar day' if f(t0) else 'Polar night'
                    self.sunriseLabel.setText(str)
                    self.sunsetLabel.setText(str)
                
                # Calculate the phase of the moon
                t = ts.from_datetime(self.dt_utc)
                phase = almanac.moon_phase(eph, t)
                self.moonPhaseLabel.setText('{:.1f} degrees'.format(phase.degrees))
                
                
                # Calculate the seasons
                t0 = ts.utc(year, 1, 1)
                t1 = ts.utc(year, 12, 31)
                t, y = almanac.find_discrete(t0, t1, almanac.seasons(eph))
                self.vernalEquinoxLabel.setText(self.formatDateTime(t[0]))
                self.summerSolsticeLabel.setText(self.formatDateTime(t[1]))
                self.autumnalEquinoxLabel.setText(self.formatDateTime(t[2]))
                self.winterSolsticeLabel.setText(self.formatDateTime(t[3]))
        except Exception:
            self.iface.messageBar().pushMessage("", "The ephemeris file does not cover the selected date range. Go to Settings and download and select an ephemeris file that contains your date range.", level=Qgis.Critical, duration=6)
                
            
    def clearInfo(self):
        self.sunAzimuthLabel.setText('')
        self.sunElevationLabel.setText('')
        self.dawnLabel.setText('')
        self.sunriseLabel.setText('')
        self.sunsetLabel.setText('')
        self.civilTwilightLabel.setText('')
        self.nauticalTwilightLabel.setText('')
        self.astronomicalTwilightLabel.setText('')
        self.nightLabel.setText('')
        self.daylightDurationLabel.setText('')
        self.noonLabel.setText('')
        self.moonAzimuthLabel.setText('')
        self.moonElevationLabel.setText('')
        self.vernalEquinoxLabel.setText('')
        self.summerSolsticeLabel.setText('')
        self.autumnalEquinoxLabel.setText('')
        self.winterSolsticeLabel.setText('')
        self.moonPhaseLabel.setText('')

    def formatDateTime(self, dt):
        if self.useUtcCheckBox.isChecked():
            return(dt.utc_iso())
        else:
            # return python utc datetime, round to nearest second, covert to local time zone
            tz_dt = (dt.utc_datetime() + timedelta(milliseconds=500)).astimezone(self.tz)
            fmt = '%Y-%m-%d %H:%M:%S'
            return( tz_dt.strftime(fmt) )

    def on_currentDateTimeButton_pressed(self):
        self.dt_utc = datetime.now(ZoneInfo("UTC"))
        self.updateSunInfo()

    def startCapture(self):
        # print('startCapture')
        if self.coordCaptureButton.isChecked():
            self.savedMapTool = self.canvas.mapTool()
            self.canvas.setMapTool(self.captureCoordinate)
        else:
            if self.savedMapTool:
                self.canvas.setMapTool(self.savedMapTool)
                self.savedMapTool = None

    @pyqtSlot(QgsPointXY)
    def capturedPoint(self, pt):
        # print('capturedPoint')
        lon = pt.x()
        lat = pt.y()
        if lat > 90 or lat < -90 or lon > 180 or lon < -180:
            self.cur_location = None
            self.coordLineEdit.setText('')
            self.updateSunInfo()
            return
        if self.isVisible() and self.coordCaptureButton.isChecked():
            self.cur_location = pt
            self.cur_tzname = self.tzf.timezone_at(lng=lon, lat=lat)
            self.tz = ZoneInfo(self.cur_tzname)
            self.updateSunInfo()
        else:
            self.cur_location = None

    @pyqtSlot()
    def stopCapture(self):
        # print('stopCapture')
        self.coordCaptureButton.setChecked(False)
        self.rubber.reset()

    def on_useUtcCheckBox_stateChanged(self, state):
        self.updateSunInfo()

    def on_dateEdit_dateChanged(self, date):
        if self.useUtcCheckBox.isChecked():
            self.dt_utc = self.dt_utc.replace(year=date.year(), month=date.month(), day=date.day())
        else:
            dt = self.getLocalDateTime()
            dt = dt.replace(year=date.year(), month=date.month(), day=date.day())
            self.dt_utc = dt.astimezone(ZoneInfo("UTC"))
        self.updateSunInfo()

    def on_timeEdit_timeChanged(self, time):
        if self.useUtcCheckBox.isChecked():
            self.dt_utc = self.dt_utc.replace(hour=time.hour(), minute=time.minute(), second=time.second())
        else:
            dt = self.getLocalDateTime()
            dt = dt.replace(hour=time.hour(), minute=time.minute(), second=time.second())
            self.dt_utc = dt.astimezone(ZoneInfo("UTC"))
        self.updateSunInfo()

    def coordCommitButton(self):
        # print('coordCommitButton Pressed')
        try:
            coord = self.coordLineEdit.text().strip()
            if not coord:
                self.clearInfo()
                return
            (lat, lon) = parseDMSString(coord)
            self.cur_location = QgsPointXY(lon, lat)
            self.cur_tzname = self.tzf.timezone_at(lng=lon, lat=lat)
            self.tz = ZoneInfo(self.cur_tzname)
            self.updateSunInfo()
        except Exception:
            self.clearInfo()
            self.iface.messageBar().pushMessage("", "Invalid 'latitude, longitude'", level=Qgis.Warning, duration=2)
            return
