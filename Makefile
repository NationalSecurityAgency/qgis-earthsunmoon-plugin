PLUGINNAME = earthsunmoon
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = __init__.py captureCoordinate.py dms.py earthsunmoon.py earthsunmoonprocessing.py ephemInfo.py infoDialog.py moonposition.py planetpositions.py provider.py sunposition.py utils.py wintz.py 
EXTRAS = metadata.txt icon.png

deploy: 
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vrf data $(PLUGINS)
	cp -vrf doc $(PLUGINS)
	cp -vrf icons $(PLUGINS)
	cp -vrf ui $(PLUGINS)
	cp -vf helphead.html index.html
	python -m markdown -x extra readme.md >> index.html
	echo '</body>' >> index.html
	cp -vf index.html $(PLUGINS)/index.html
