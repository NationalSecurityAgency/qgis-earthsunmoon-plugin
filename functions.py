"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import re
import json
from qgis.core import QgsPointXY, QgsGeometry, QgsExpression, QgsProject
from qgis.PyQt.QtCore import QDateTime
from qgis.utils import qgsfunction
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, available_timezones

from skyfield.api import load, load_file, wgs84
from skyfield import almanac
from .wintz import win_tz_map
from .utils import settings

# import traceback
group_name = 'Earth Sun Moon'

def InitFunctions():
    QgsExpression.registerFunction(esm_moon_phase)
    QgsExpression.registerFunction(esm_moon_zenith)
    QgsExpression.registerFunction(esm_sun_zenith)
    QgsExpression.registerFunction(esm_sun_moon_info)
    QgsExpression.registerFunction(esm_local_datetime)
    QgsExpression.registerFunction(esm_local_qdatetime)

def UnloadFunctions():
    QgsExpression.unregisterFunction('esm_moon_phase')
    QgsExpression.unregisterFunction('esm_moon_zenith')
    QgsExpression.unregisterFunction('esm_sun_zenith')
    QgsExpression.unregisterFunction('esm_sun_moon_info')
    QgsExpression.unregisterFunction('esm_local_datetime')
    QgsExpression.unregisterFunction('esm_local_qdatetime')

def get_datetime(dt, tz_name):
    if not tz_name:
        if isinstance(dt, QDateTime):  # QDateTime format - terrible timezone support
            tz_name = dt.timeZoneAbbreviation()
        elif isinstance(dt, (int,float)):  # Assume it is a Epoch timestamp
            tz_name = 'UTC'
        elif isinstance(dt, datetime):  # Python datetime format
            try:
                tz_name = dt.tzinfo.zone
            except Exception:
                tz_name = dt.tzname()
            
    if tz_name in win_tz_map:
        tz_name = win_tz_map[tz_name]
    if tz_name not in available_timezones():
        if isinstance(dt, datetime):
            if dt.tzinfo:
                offset = int(dt.tzinfo.utcoffset(dt).total_seconds()/3600.0)
                tz_name = 'Etc/GMT{:+d}'.format(-offset)
            else:
                tz_name = 'UTC'
        else:
            tz_name = 'UTC'
    tz = ZoneInfo(tz_name)

    if isinstance(dt, QDateTime):
        dt_aware = dt.toPyDateTime()
        dt_aware = dt_aware.replace(tzinfo=tz)
    elif isinstance(dt, (int,float)):
        dt_aware = datetime.fromtimestamp(dt/1000.0, tz)  # Assune input in ms and need to covert to s
    else:
        dt_aware = dt.replace(tzinfo=tz)
    return(dt_aware)

def utc_datetime(dt):
    return(dt.astimezone(ZoneInfo('UTC')))

@qgsfunction(-1, group=group_name)
def esm_moon_phase(values, feature, parent):
    """
    Given a date and time, return the moon's phase in degrees where 0° is the New Noon, 90° is First Quarter, 180° is Full Moon, and 270° is Last Quarter.

    <h4>Syntax</h4>
    <p><b>esm_moon_phase</b>( <i>datetime</i>[, tz_name] )</p>

    <h4>Arguments</h4>
    <p><i>datetime</i> &rarr; this can be a native QGIS QDateTime, a python datetime, or a timestamp in ms.</p>
    <p><i>tz_name</i> &rarr; optional timezone IANA formatted string such as 'UTC' or 'America/New_York'. If not specified and the input is a timestamp, then it is assumed to be UTC. If it is a python datetime format or QDateTime format, then the datetime is checked to see if there is an associated timezone to use. If not, UTC is used.</p>
    
    <h4>Example usage</h4>
    <ul>
      <li><b>esm_moon_phase</b>(1483225200000) &rarr; returns moon phase 30.601519722460964 for the timestamp</li>
      <li><b>esm_moon_phase</b>(<b>make_datetime</b>(2023,5,4,17,45,30), 'America/New_York') &rarr; Moon phase on 2023-05-04T17:45:30-0400 is 169.79073790632003.</li>
    </ul>
    """
    if len(values) < 1 or len(values) > 2:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    dt = values[0]
    if len(values) == 2:
        tz_name = values[1]
    else:
        tz_name = None
        
    try:
        dt = get_datetime(dt, tz_name)
        utc = dt.astimezone(ZoneInfo('UTC'))
        ts = settings.timescale()
        t = ts.from_datetime(utc)
        eph = settings.ephem()
        phase = almanac.moon_phase(eph, t)
        return(float(phase.degrees))
    except Exception:
        # traceback.print_exc()
        parent.setEvalErrorString("Error: datetime, timezone error in calculation moon phase")
        return

@qgsfunction(-1, group=group_name)
def esm_sun_zenith(values, feature, parent):
    """
    Given a date and time, return the EPSG:4326 coordinate point where the sun is directly overhead.

    <h4>Syntax</h4>
    <p><b>esm_sun_zenith</b>( <i>datetime</i>[, tz_name] )</p>

    <h4>Arguments</h4>
    <p><i>datetime</i> &rarr; this can be a native QGIS QDateTime, a python datetime, or a timestamp in ms.</p>
    <p><i>tz_name</i> &rarr; optional timezone IANA formatted string such as 'UTC' or 'America/New_York'. If not specified and the input is a timestamp, then it is assumed to be UTC. If it is a python datetime format or QDateTime format, then the datetime is checked to see if there is an associated timezone to use. If not, UTC is used.</p>
    
    <h4>Example usage</h4>
    <ul>
      <li><b>geom_to_wkt( esm_sun_zenith( make_datetime</b>(2023,5,4,17,45,30), 'UTC')) &rarr; 'Point (-68.14671867 -0.15771011)'.</li>
    </ul>
    """
    if len(values) < 1 or len(values) > 2:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    dt = values[0]
    if len(values) == 2:
        tz_name = values[1]
    else:
        tz_name = None
        
    try:
        dt = get_datetime(dt, tz_name)
        utc = dt.astimezone(ZoneInfo('UTC'))
        eph = settings.ephem()
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        sun = eph['sun'] # vector from solar system barycenter to sun
        geocentric_sun = sun - earth # vector from geocenter to sun
        ts = settings.timescale()
        t = ts.utc(utc.year, utc.month, utc.day, utc.hour, utc.minute, utc.second)
        try:
            sun_position = wgs84.geographic_position_of(geocentric_sun.at(t)) # geographic_position_of method requires a geocentric position
        except Exception:
            parent.setEvalErrorString("The ephemeris file does not cover the selected date range. Go to Settings and download and select an ephemeris file that contains your date range.")
            return
        pt = QgsPointXY(sun_position.longitude.degrees, sun_position.latitude.degrees)
        return(QgsGeometry.fromPointXY(pt))
    except Exception:
        parent.setEvalErrorString("Error: datetime, timezone error in calculation moon phase")
        return

@qgsfunction(-1, group=group_name)
def esm_moon_zenith(values, feature, parent):
    """
    Given a date and time, return the EPSG:4326 coordinate point where the moon is directly overhead.

    <h4>Syntax</h4>
    <p><b>esm_moon_zenith</b>( <i>datetime</i>[, tz_name] )</p>

    <h4>Arguments</h4>
    <p><i>datetime</i> &rarr; this can be a native QGIS QDateTime, a python datetime, or a timestamp in ms.</p>
    <p><i>tz_name</i> &rarr; optional timezone IANA formatted string such as 'UTC' or 'America/New_York'. If not specified and the input is a timestamp, then it is assumed to be UTC. If it is a python datetime format or QDateTime format, then the datetime is checked to see if there is an associated timezone to use. If not, UTC is used.</p>
    
    <h4>Example usage</h4>
    <ul>
      <li><b>geom_to_wkt( esm_moon_zenith( make_datetime</b>(2023,5,4,17,45,30), 'UTC')) &rarr; 'Point (80.94657837 -11.8883969)'.</li>
    </ul>
    """
    if len(values) < 1 or len(values) > 2:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    dt = values[0]
    if len(values) == 2:
        tz_name = values[1]
    else:
        tz_name = None
        
    try:
        dt = get_datetime(dt, tz_name)
        utc = dt.astimezone(ZoneInfo('UTC'))
        eph = settings.ephem()
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        moon = eph['moon'] # vector from solar system barycenter to moon
        geocentric_moon = moon - earth # vector from geocenter to moon
        ts = settings.timescale()
        t = ts.utc(utc.year, utc.month, utc.day, utc.hour, utc.minute, utc.second)
        try:
            moon_position = wgs84.geographic_position_of(geocentric_moon.at(t)) # geographic_position_of method requires a geocentric position
        except Exception:
            parent.setEvalErrorString("The ephemeris file does not cover the selected date range. Go to Settings and download and select an ephemeris file that contains your date range.")
            return
        pt = QgsPointXY(moon_position.longitude.degrees, moon_position.latitude.degrees)
        return(QgsGeometry.fromPointXY(pt))
    except Exception:
        parent.setEvalErrorString("Error: datetime, timezone error in calculation moon phase")
        return

@qgsfunction(-1, group=group_name)
def esm_sun_moon_info(values, feature, parent):
    """
    Given a date and time, latitude and longitude in EPSG:4326, output format type, and optional timezone of the date and time object, it returns a python dictionary or JSON string of solar and lunar information. If you want to avoing all confusion, use UTC as the datetime timezone.

    <h4>Syntax</h4>
    <p><b>esm_sun_moon_info</b>( <i>datetime, latitude, longitude[, output_type, tz_name]</i> )</p>

    <h4>Arguments</h4>
    <p><i>datetime</i> &rarr; this can be a native QGIS QDateTime, a python datetime, or a timestamp in ms.</p>
    <p><i>latitude</i> &rarr; latitude of reference point in EPSG:4326.</p>
    <p><i>longitude</i> &rarr; longitude of reference point in EPSG:4326.</p>
    <p><i>output_type</i> &rarr; output type with 'dict' returning a python dictionary and 'json' returning a json formatted string. The default is 'dict'.</p>
    <p><i>tz_name</i> &rarr; optional timezone IANA formatted string such as 'UTC' or 'America/New_York'. If not specified and the input is a timestamp, then it is assumed to be UTC. If it is a python datetime format or QDateTime format, then the datetime is checked to see if there is an associated timezone to use. If not, UTC is used.</p>
    
    <h4>Example usage</h4>
    <ul>
      <li><b>esm_sun_moon_info( make_datetime</b>(2023,5,4,17,45,00), 38.66113944, -90.06202624, 'dict', 'America/Chicago') &rarr; { 'astronomical_twilight': '2023-05-04T01:58:08Z',...,'sunset': '2023-05-04T00:54:08Z' }.</li>
    </ul>
    """
    if len(values) < 3 or len(values) > 5:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
        
    try:
        dt = values[0]
        lat = float(values[1])
        lon = float(values[2])
        if len(values) >= 4:
            output_type = values[3]
        else:
            output_type = 'dict'
        if len(values) == 5:
            tz_name = values[4]
        else:
            tz_name = None
        dt = get_datetime(dt, tz_name)

        # Convert the date, time and timezone to UTC
        utc = dt.astimezone(ZoneInfo('UTC'))
        ts = settings.timescale()

        # Return all dates and times in terms of UTC
        cur_time = ts.from_datetime(utc)
        loc = wgs84.latlon(lat, lon)
        info = {}

        # Load  ephemeris
        eph = settings.ephem()
        earth = eph['earth']
        sun = eph['sun']
        moon = eph['moon']
                
        # Get sun azimuth and altitude
        observer = earth + loc
        astrometric = observer.at(cur_time).observe(sun)
        alt, az, d = astrometric.apparent().altaz()
        info['sun_azimuth'] = float(az.degrees)
        info['sun_elevation'] = float(alt.degrees)
    
        # Get moon azimuth and altitude
        astrometric = observer.at(cur_time).observe(moon)
        alt, az, d = astrometric.apparent().altaz()
        info['moon_azimuth'] = float(az.degrees)
        info['moon_elevation'] = float(alt.degrees)

        # Get solar noon
        midnight = utc.replace(hour=0, minute=0, second=0, microsecond=0)
        next_midnight = midnight + timedelta(days=1)
        t0 = ts.from_datetime(midnight) # Starting time to search for events
        t1 = ts.from_datetime(next_midnight) # Ending time to search for events
        
        f = almanac.meridian_transits(eph, sun, loc)
        times, events = almanac.find_discrete(t0, t1, f)
        if times:
            # Select transits instead of antitransits.
            times = times[events == 1]
            t = times[0]
            info['solar_noon'] = t.utc_iso()
        
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
                    info['sunrise'] = t.utc_iso()
                elif e == 3: # Dawn
                    info['dawn'] = t.utc_iso()
            else:
                if e == 3: # Civil twilight starts
                    day_end = t
                    has_end = True
                    info['sunset'] = t.utc_iso()
                    info['civil_twilight'] = t.utc_iso()
                elif e == 2: # Nautical twilight starts
                    info['nautical_twilight'] = t.utc_iso()
                elif e == 1: # Astronomical twilight starts
                    info['astronomical_twilight'] = t.utc_iso()
                elif e == 0: # Night starts
                    info['night'] = t.utc_iso()
            previous_e = e

        # Calculate the phase of the moon
        t = ts.from_datetime(utc)
        phase = almanac.moon_phase(eph, t)
        info['moon_phase'] = float(phase.degrees)
        
        if output_type == 'dict':
            return(info)
        else:
            return(json.dumps(info, indent = 1))
    except Exception:
        parent.setEvalErrorString("Error: datetime, timezone error in calculation moon phase")
        return

@qgsfunction(args='auto', group=group_name)
def esm_local_datetime(feature, parent):
    """
    Returns the current date and time as a python datetime object with the local computer's timezone settings.

    <h4>Syntax</h4>
    <p><b>esm_local_datetime</b>( )</p>

    <h4>Arguments</h4>
    <p>None</p>
    <h4>Example usage</h4>
    <ul>
      <li><b>esm_local_datetime</b>() &rarr; returns a local python datetime with timezone set</li>
    </ul>
    """
    try:
        dt = datetime.utcnow()
        dt = dt.replace(tzinfo=ZoneInfo('UTC'))
        tz_name = dt.astimezone().tzname()
        dt = get_datetime(dt, tz_name)  # This will try to standardize the timezone
        return(dt)
    except Exception:
        parent.setEvalErrorString("Error: Was not able to get the local time")
        return

@qgsfunction(args='auto', group=group_name)
def esm_local_qdatetime(feature, parent):
    """
    Returns the current date and time as a standard QGIS QDateTime object with the local computer's timezone settings.

    <h4>Syntax</h4>
    <p><b>esm_local_qdatetime</b>( )</p>

    <h4>Arguments</h4>
    <p>None</p>
    <h4>Example usage</h4>
    <ul>
      <li><b>esm_local_qdatetime</b>() &rarr; returns local QGIS supported QDateTime object.</li>
    </ul>
    """
    try:
        dt = QDateTime.currentDateTime()
        return(dt)
    except Exception:
        parent.setEvalErrorString("Error: Was not able to get the local time")
        return
