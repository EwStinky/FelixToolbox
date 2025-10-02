"""
/***************************************************************************
    This module contains the class to create the dialog UI for a 
    API keys storage.
                             -------------------
        start                : 2025-09-28
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
from .utils import load_ui, UI_tools
from ..library import Isochrone_API_ORS, apiSireneRequest
from qgis.PyQt import QtWidgets
from qgis.core import QgsSettings

class ui_mg_api_key(QtWidgets.QDialog, load_ui('API_keys_storage.ui').FORM_CLASS):
    """ui_mg_api_key contains all the functions specifically designed to manage the UI
    and the data created from the UI.

    Args:
        QtWidgets: QDialog class that forms the base class of our dialog window.
        load_ui : function that loads the .ui file and returns the class and the form.
    """
    def __init__(self,parent=None):
        """__init__ initializes the dialog window and connects the buttons to the functions.
        Hides the OK and delete buttons if the QTableWidget is empty."""
        super(ui_mg_api_key, self).__init__(parent)
        self.setupUi(self)
        self.lineEdit_SIRENE_key.setText(UI_tools.read_API_key('SIRENE_API_KEY'))
        self.lineEdit_ORS_key.setText(UI_tools.read_API_key('ORS_API_KEY'))
        self.pushButton_test_keys.clicked.connect(self.test_api_keys)

    @staticmethod
    def store_api_key(key_name:str, key_value:str):
        """Store the API key in a QgsSettings used for this plugin only."""
        QgsSettings().setValue(f'FelixToolbox/{key_name}', key_value)
    
    def test_api_keys(self):
        """Test if the API keys provided in the QLineEdit are valid."""
        try:
            test_ors = Isochrone_API_ORS.request_ORS_isochrone_api([[8.681495,49.41461]], [1], self.lineEdit_ORS_key.text())
        except Exception as e:
            test_ors = False
        try: 
            test_sirene = apiSireneRequest(api_key=self.lineEdit_SIRENE_key.text(), nombre=0).get_request_api_SIRENE()
        except Exception as e:
            test_sirene = False
        if test_ors and test_sirene:
            QtWidgets.QMessageBox.information(self, "Success", "Both API keys are valid.")
        else:
            QtWidgets.QMessageBox.warning(self, "Warning", f"SIRENE API key: {'Valid' if test_sirene else 'Invalid'} - ORS API key: {'Valid' if test_ors else 'Invalid'}")

class ui_run_api_key():
    """ui_run_api_key is used to run the dialog window and execute the functions"""
    def __init__(self):
        self.dlg = ui_mg_api_key()
    def run(self):
        ui=self.dlg.exec()
        if ui == QtWidgets.QDialog.Accepted:
            try:
                self.dlg.store_api_key('SIRENE_API_KEY', self.dlg.lineEdit_SIRENE_key.text())
                self.dlg.store_api_key('ORS_API_KEY', self.dlg.lineEdit_ORS_key.text())
            except Exception as e:
                raise e
