
def classFactory(iface):
    if iface:
        from .earthsunmoon import EarthSunMoon
        return EarthSunMoon(iface)
    else:
        # This is used when the plugin is loaded from the command line command qgis_process
        from .earthsunmoonprocessing import EarthSunMoon
        return EarthSunMoon(iface)
