"""
/***************************************************************************
    This module contains the class to create the dialog UI for the 
    Request_API_SIRENE.py script.
    It contains a class 'ui_mg_isochrone' for the management of the UI 
    and data preparation. And another class 'ui_run_isochrone' to run the 
    script through the UI. 
                             -------------------
        start                : 2025-08-20
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
from .utils import load_ui, prepVector, usefullVariable
from ..library import siretInPolygonFilteredByCoordinates, siretInPolygonFilteredByAddresses,apiSireneUtils

from qgis.PyQt import QtWidgets
from qgis.core import QgsProject, QgsMapLayerType, QgsWkbTypes
from qgis.core import QgsVectorLayer

class ui_mg_request_sirene(QtWidgets.QDialog, load_ui('Request_API_SIRENE.ui').FORM_CLASS):
    """ui_mg_isochrone contains all the functions specifically designed to manage the UI
    and the data created from the UI to be used in the Isochrone_ORS_Tools_GeopandasV3.py script.

    Args:
        QtWidgets: QDialog class that forms the base class of our dialog window.
        load_ui : function that loads the .ui file and returns the class and the form.
    """
    def __init__(self,parent=None):
        """__init__ initializes the dialog window and connects the buttons to the functions.
        Hides the OK and delete buttons if the QTableWidget is empty."""
        super(ui_mg_request_sirene, self).__init__(parent)
        self.setupUi(self)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.tableWidget.rowCount() > 0)
        self.pushButton_Ajouter_table.clicked.connect(self.addRowQTableWidget)
        self.pushButton_Effacer_ligne_table.clicked.connect(self.removeRwoQTableWidget)
        self.pushButton_Effacer_ligne_table.setEnabled(self.tableWidget.rowCount() > 0)
        self.list_layers = [] #List of layers id selected by the user, its purpose is a bit excessive but it is to avoid confusion in QGIS if several layers share the same name.

    def closeEvent(self, event):
        """closeEvent is used to reset the widgets to their default settings.
        It is called when the user closes the window.
        """
        self.tableWidget.setRowCount(0)
        self.pushButton_Ajouter_table.clicked.disconnect()
        self.pushButton_Effacer_ligne_table.disconnect()
        self.lineEdit_field.clear()
        self.lineEdit_field.setPlaceholderText("Ex: activitePrincipaleUniteLegale...")
        self.lineEdit_api_key.clear()
        self.lineEdit_api_key.setPlaceholderText("Add your API key")
        self.lineEdit_activity.clear()
        self.lineEdit_activity.setPlaceholderText("Ex: 47, 10.13B, 38.3...")
        super().closeEvent(event)

    def addRowQTableWidget(self): 
        """addRowQTableWidget adds a row to  the QTableWidget 
        with the parameters selected by the user. And add the layer id to self.list_layers.
        Enables the OK and delete buttons if the QTableWidget is not empty.

        It checks if the user has enter parameters in the QlineEdit.
        If not, the missing or wrong input will be highlighted in red
        """
        if self.comboBox_layer_QGIS.currentText()=="": 
            pass
        else:
            if self.lineEdit_api_key.text()=="":
                self.lineEdit_api_key.setStyleSheet("""
                    QLineEdit {
                        color: red; /* Text color */
                        border: 1px solid red; /* Hollow red border */
                        border-radius: 2px; 
                        background-color: white; /* Optional: ensure background is not red */
                    }""")
                pass
            else:
                self.lineEdit_api_key.setStyleSheet("""QLineEdit { }""")
                parameters=[
                    self.comboBox_layer_QGIS.currentText(),
                    self.lineEdit_api_key.text(),
                    self.comboBox_processing.currentText(),
                    self.lineEdit_field.text(),
                    self.lineEdit_activity.text()]
                self.list_layers.append(self.comboBox_layer_QGIS.itemData(self.comboBox_layer_QGIS.currentIndex()))
                self.comboBox_layer_QGIS.setCurrentIndex(-1) #On retourne à la sélection vid
                numRows = self.tableWidget.rowCount()
                self.tableWidget.insertRow(numRows) # Create a empty row at bottom of table
                for i in range(len(parameters)): #populate the row
                    self.tableWidget.setItem(numRows, i, QtWidgets.QTableWidgetItem(str(parameters[i])))
                self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.tableWidget.rowCount() > 0)
                self.pushButton_Effacer_ligne_table.setEnabled(self.tableWidget.rowCount() > 0)

    def removeRwoQTableWidget(self):
        """removeRwoQTableWidget removes the selected row from the QTableWidget and self.list_layers.
        Enables the OK and delete buttons if the QTableWidget is not empty."""
        row = self.tableWidget.currentRow()
        try:
            del(self.list_layers[row])
        except IndexError:
            return
        self.tableWidget.removeRow(row)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.tableWidget.rowCount() > 0)
        self.pushButton_Effacer_ligne_table.setEnabled(self.tableWidget.rowCount() > 0)

    def getQTableWidgetData(self,column_number:int=5):
        """getQTableWidgetData returns the data from the QTableWidget"""
        data = []
        for row in range(self.tableWidget.rowCount()):
            data.append([self.tableWidget.item(row, col).text() for col in range(self.tableWidget.columnCount())])
        return [data[i:i+column_number] for i in range(0,len(data),column_number)][0]

    def field_combo_box_selected(self):
        selected_item = self.comboBox_filed.currentText()
        current_text = self.lineEdit_field.text()
        
        if current_text:
            self.lineEdit_field.setText(f"{current_text}, {selected_item}")
        else:
            self.lineEdit_field.setText(selected_item)

    def activty_combo_box_selected(self):
        selected_item = self.comboBox_activity.currentText()
        current_text = self.lineEdit_activity.text()
        if current_text:
            self.lineEdit_activity.setText(f"{current_text}, {selected_item}")
        else:
            self.lineEdit_activity.setText(selected_item)
    
    def prepLayer(self, index:int):
        """function return the selected layer as a gpd.GeoDataFrame and the layer name"""
        layer_selected=QgsProject.instance().mapLayer(self.list_layers[index])
        return prepVector.layer_to_geodataframe(layer_selected), layer_selected.name()
    
    @staticmethod
    def add_extra_fields(field,extra_field):
        """Add the other fields that the user chosen to add to the request from the UI"""
        for new_field in set([u for u in extra_field.replace(" ", ",").split(',') if u!='']):
            field+=','+new_field
        return field
        

    @staticmethod
    def add_activity_filter(activity):
        """Add the activities that the user chosen to add to the request as filter"""
        list_possible_NAF = [clean_activity for clean_activity in set([u for u in activity.replace(" ", ",").split(',') if u!=''])]
        return [code for code in list_possible_NAF if code.replace('.','',1).isdigit()]

class ui_run_request_sirene():
    """ui_run_isochrone is used to run Isochrones_ORS_Tools_GeopandasV3's UI.
    And use the data selected from the UI to calculate isochrones and display them in QGIS.
    """
    def __init__(self):
        self.dlg = ui_mg_request_sirene()
        self.fields ='siren,dateCreationUniteLegale,siret,dateCreationEtablissement,trancheEffectifsEtablissement,enseigne1Etablissement,codeCommuneEtablissement,numeroVoieEtablissement,typeVoieEtablissement,libelleVoieEtablissement,codePostalEtablissement,libelleCommuneEtablissement,activitePrincipaleEtablissement,etatAdministratifEtablissement,coordonneeLambertAbscisseEtablissement,coordonneeLambertOrdonneeEtablissement'
        self.activity = []
    def run(self): 
        self.dlg.comboBox_layer_QGIS.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.dlg.comboBox_layer_QGIS.addItem(layer.name(), layer.id())
        self.dlg.comboBox_filed.addItems(usefullVariable.all_API_SIREN_fields)
        self.dlg.comboBox_activity.addItems(usefullVariable.nomenclature_NAFV2)
        self.dlg.comboBox_filed.currentIndexChanged.connect(self.dlg.field_combo_box_selected)
        self.dlg.comboBox_activity.currentIndexChanged.connect(self.dlg.activty_combo_box_selected)
        ui = self.dlg.exec()

        if ui == QtWidgets.QDialog.Accepted:
            try:
                for index,data in enumerate(self.dlg.getQTableWidgetData()):
                    layer_selected, layer_name = self.dlg.prepLayer(index)
                    if data[3]:
                        self.fields = self.dlg.add_extra_fields(self.fields,data[3])
                    if data[4]:
                        self.activity = self.dlg.add_activity_filter(data[4])
                    request_parameters={
                    "api_key":data[1].split()[0], 
                    "champs": self.fields,
                    "nombre": 100,
                    "curseur": '*',
                    "date": '2099-01-01'
                    }
                    if data[2]=='Selection from coordinates (Fastest)':
                        request_SIRENE_output = siretInPolygonFilteredByCoordinates(layer_selected, request_parameters, self.activity).establishments_SIRENE_in_polygon_coordinates()
                    elif data[2]=='Selection from address':
                        request_SIRENE_output = siretInPolygonFilteredByAddresses(layer_selected, request_parameters, self.activity).establishments_SIRENE_in_polygon_address()
                    else: 
                        request_coordinates = siretInPolygonFilteredByCoordinates(layer_selected, request_parameters, self.activity).establishments_SIRENE_in_polygon_coordinates()
                        request_addresse = siretInPolygonFilteredByAddresses(layer_selected, request_parameters, self.activity).establishments_SIRENE_in_polygon_address()
                        request_SIRENE_output = apiSireneUtils.mergeRequestTypeOutput(request_coordinates,request_addresse)
                    QgsProject.instance().addMapLayer(QgsVectorLayer(request_SIRENE_output.to_json(), "Siret_located_in_{}".format(layer_name), "ogr"))
            except RuntimeError as e:
                raise e
            except ValueError as e:
                raise e
            except Exception as e:
                raise e
