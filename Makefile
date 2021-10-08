PLUGINNAME = earthsunmoon
PLUGINS = C:/Users/cjhamil/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = earthsunmoon.py __init__.py provider.py sunposition.py moonposition.py daynight.py planetpositions.py utils.py infoDialog.py captureCoordinate.py wintz.py dms.py
EXTRAS = metadata.txt

deploy: 
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vrf icons $(PLUGINS)
	cp -vrf doc $(PLUGINS)
	cp -vrf ui $(PLUGINS)
	cp -vf helphead.html index.html
	python -m markdown -x extra readme.md >> index.html
	echo '</body>' >> index.html
	cp -vf index.html $(PLUGINS)/index.html
