import os

from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUiType
from .utils import settings

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/ephemInfo.ui'))


class EphemerisInfo(QDialog, FORM_CLASS):

    def __init__(self, iface, parent):
        super(EphemerisInfo, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()

    def showEvent(self, e):
        self.ephemInfoEdit.setPlainText(settings.ephemInfo())