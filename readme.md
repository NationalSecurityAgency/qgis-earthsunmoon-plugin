# Earth, Sun, Moon, and Planets Plugin

This plugin uses the highly accurate Skyfield library to show where the sun, moon, and planets are located at their zenith from earth's perspective for a particular date and time. An additional algorithm calculates lunar and solar data for a particular location on earth given a date and time. When installed, this plugin can be found in the QGIS menu under ***Plugins->Earth, sun, moon &amp; planets***. The planetary location alogorims are as follows:

* <img src="icons/sun_icon.svg" alt="Sun position directly overhead"> ***Sun position directly overhead*** - This shows the location of the sun where it is directly overhead for a particular date and time.
* <img src="icons/moon.png" width=24 height=24 alt="Moon position directly overhead"> ***Moon position directly overhead*** - This shows the location of the moon where it is directly overhead for a particular date and time.
* <img src="icons/venus.png" width=24 height=24 alt="Planetary positions directly overhead"> ***Planetary positions directly overhead*** - This shows the location of the planets where they are directly overhead for a particular date and time.

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

