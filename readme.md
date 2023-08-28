# Earth, Sun, Moon, and Planets Plugin

This plugin uses the highly accurate Skyfield library to show where the sun, moon, and planets are located at their zenith from earth's perspective for a particular date and time. An additional algorithm calculates lunar and solar data for a particular location on earth given a date and time. The ***Day/Night terminator*** algorithm plots the day/night terminator line and polygon layers associate with sunrise/set, civil twilight, nautical twilight, and astronomical twilight. When installed, this plugin can be found in the QGIS menu under ***Plugins->Earth, sun, moon &amp; planets***. 

<div style="text-align:center"><img src="doc/menu.jpg" alt="Plugin menu"></div>

## Installation
Other than for the ***Day/Night terminator*** algorithm, this plugin requires two additional libraries not provided by QGIS. These can be installed by opening up your OSGeo4W Shell and typing the command "**pip install timezonefinder skyfield**" or whatever method you use to install Python libraries.

You do not need to be a system administrator to be able to install these libraries.

## Tools Overview

These are the tools provided by the Earth, Sun, Moon, and Planets Plugin:

* <img src="icons/daynight.png" width=24 height=24 alt="Sun position directly overhead"> ***Day/Night terminator*** - This algorithm creates vector layers for the day/night terminator line, polygon layers associate with sunrise/set, civil twilight, nautical twilight and astronomical twilight, and the position of the sun directly overhead. Unlike the other algorithms below this does not depend on the Skyfield library. It uses spherical geometery like the web based maps that you find on-line.
* <img src="icons/sun_icon.svg" alt="Sun position directly overhead"> ***Sun position directly overhead*** - This shows the location of the sun where it is directly overhead for a particular date and time.
* <img src="icons/moon.png" width=24 height=24 alt="Moon position directly overhead"> ***Moon position directly overhead*** - This shows the location of the moon where it is directly overhead for a particular date and time.
* <img src="icons/venus.png" width=24 height=24 alt="Planetary positions directly overhead"> ***Planetary positions directly overhead*** - This shows the location of the planets where they are directly overhead for a particular date and time.
* <img src="icons/ephem.svg" alt="Ephemeris information"> ***Ephemeris information*** - This provides information about the selected ephemeris file. This plugin includes limited ephemeris data for the dates 1990-2040. For dates outside this range other ephemeris files can be downloaded from the <a href="https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/">JPL Ephemeris page</a>. These can be installed from the ***Settings*** menu.
* <img src="doc/settings.png" width=24 height=24 alt="Settings"> ***Settings*** - Plugin settings.

As an example this is the dialog for the algorithm to calculate the sun directly overhead.

<div style="text-align:center"><img src="doc/sunalg.jpg" alt="Sun position directly overhead"></div>

The moon and planets are the same. This shows what this algorithm produces when this algorithm is run.

<div style="text-align:center"><img src="doc/sunmoonmap.jpg" alt="Sun moon map"></div>

This shows the locations of the sun, moon, and planets.

<div style="text-align:center"><img src="doc/sunmoonplanets.jpg" alt="Sun moon planets"></div>

The attributes table contains the name of the object, its coordinate where it is directly overhead, and the date and time both in computer time and UTC. This is the attribute table with all three combined together.

<div style="text-align:center"><img src="doc/attributes.jpg" alt="Attributes"></div>

## <img src="icons/info.svg" alt="Solar/lunar information"> Solar/lunar information

The user can click on the <img src="icons/coordCapture.svg" alt="coordinate capture"> coordinate capture icon and click on the map. This dialog is then populated with the following details. The timezone is automatically selected based on the coordinate.

<div style="text-align:center"><img src="doc/info.jpg" alt="Info"></div>

The ***Now*** icon <img src="icons/CurrentTime.png" width=24 height=24 alt="Now"> will set the date and time to the current computer time. The ***Use UTC*** check box displays the date and times in UTC; otherwise, they are displayed using the selected time zone as follows.

<div style="text-align:center"><img src="doc/info2.jpg" alt="Info"></div>

## <img src="icons/ephem.svg" alt="Ephemeris information"> Ephemeris Information
This tool displays information about the selected ephemeris file being used. Here is the limited extract file ***de440s_1990_2040.bsp*** that comes with the plugin.

<div style="text-align:center"><img src="doc/ephemeris_info.jpg" alt="Ephemeris Information"></div>

## <img src="doc/settings.png" width=24 height=24 alt="Settings"> Settings

This shows the settings dialog window. 

<div style="text-align:center"><img src="doc/settings_dialog.jpg" alt="Settings Dialog"></div>

It allows the user to select the ephemeris file used in the calculations. Click on the drop down box to select the ephemeris file to use. When first installed the plugin only includes a single limited ephemeris data extract between the years 1990 and 2040 so there will only be one option. A full ephemeris file exceeds the allowed QGIS plugin size. For dates outside this range other ephemeris files can be downloaded from the <a href="https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/">JPL Ephemeris page</a>. Once one of these are downloaded, click on the "**...**" button and select the downloaded **.bsp** then click on the ***Install Ephemeris File*** button and it will be copied over to the plugin's data directory. It will also select the file automatically in the ephemeris drop down list. Click on ***OK*** to accept these settings.

These are some of the popular ephemeris series that you will find on the JPL Ephemeris page.

<table><tr><th>Issued</th><th>Short</th><th>Medium</th><th>Long</th></tr>
<tr><td>1997</td><td></td>
<td>de405.bsp<br/>
1600 to 2200<br/>
63 MB</td>
<td>de406.bsp<br/>
−3000 to 3000<br/>
287 MB</td>
</tr>
<tr><td>2008</td>
<td>de421.bsp<br/>
1900 to 2050<br/>
17 MB</td>
<td></td>
<td>de422.bsp<br/>
−3000 to 3000<br/>
623 MB</td>
</tr>
<tr><td>2013</td>
<td>de430_1850-2150.bsp<br/>
1850 to 2150<br/>
31 MB</td>
<td>de430t.bsp<br/>
1550 to 2650<br/>
128 MB</td>
<td>de431t.bsp<br/>
–13200 to 17191<br/>
3.5 GB</td>
</tr>
<tr><td>2020</td>
<td>de440s.bsp<br/>
1849 to 2150<br/>
32 MB</td>
<td>de440.bsp<br/>
1550 to 2650<br/>
114 MB</td>
<td>de441.bsp<br/>
−13200 to 17191<br/>
3.1 GB</td>
</tr>
</table>