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
from PyQt5.QtCore import Qt
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
        self.pushButton_selectAll_fields.clicked.connect(lambda: self.setCheckStateAllItems(self.listWidget_field,Qt.Checked))
        self.pushButton_deselectAll_fields.clicked.connect(lambda: self.setCheckStateAllItems(self.listWidget_field,Qt.Unchecked))
        self.lineEdit_searchNAF.textChanged.connect(self.searchNAFbyKeyword)
        self.list_layers = [] #List of layers id selected by the user, its purpose is a bit excessive but it is to avoid confusion in QGIS if several layers share the same name.

    def closeEvent(self, event):
        """closeEvent is used to reset the widgets to their default settings.
        It is called when the user closes the window.
        """
        self.tableWidget.setRowCount(0)
        self.pushButton_Ajouter_table.clicked.disconnect()
        self.pushButton_Effacer_ligne_table.disconnect()
        self.lineEdit_api_key.clear()
        self.lineEdit_api_key.setPlaceholderText("Add your API key")
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
                    ','.join(self.retrieveCheckedItems(self.listWidget_field)),
                    ','.join([value.split()[0] for value in self.retrieveCheckedItems(self.listWidget_NAF)]),]
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
    
    @staticmethod
    def fillListWidget(ListWidget, elements:list, status:Qt.CheckState=Qt.Unchecked):
        """Fill a QListWidget with the elements of a list and make them checkable"""
        for index, value in enumerate(elements):
            item=QtWidgets.QListWidgetItem(str(value))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(status)
            ListWidget.addItem(item)

    @staticmethod
    def retrieveCheckedItems(ListWidget):
        """Retrieve the checked items from a QListWidget and return them as a list"""
        checked_items = []
        for index in range(ListWidget.count()):
            item = ListWidget.item(index)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.text())
        return checked_items
    
    @staticmethod
    def setCheckStateAllItems(ListWidget,checkState:Qt.CheckState):
        """Set the check state of all items that are enable in a QListWidget"""
        for index in range(ListWidget.count()):
            if ListWidget.item(index).flags() & Qt.ItemIsEnabled: 
                item = ListWidget.item(index)
                item.setCheckState(checkState)
    
    def searchNAFbyKeyword(self, text:str):
        """show the differents items in selfistWidget_NAF that contains the keywords entered in lineEdit_searchNAF"""
        filter_text = self.lineEdit_searchNAF.text().lower()
        for i in range(self.listWidget_NAF.count()):
            item = self.listWidget_NAF.item(i)
            item_text = item.text().lower()
            self.listWidget_NAF.setRowHidden(i, filter_text not in item_text)

    def prepLayer(self, index:int):
        """function return the selected layer as a gpd.GeoDataFrame and the layer name"""
        layer_selected=QgsProject.instance().mapLayer(self.list_layers[index])
        return prepVector.layer_to_geodataframe(layer_selected), layer_selected.name()
    
class ui_run_request_sirene():
    """ui_run_isochrone is used to run Isochrones_ORS_Tools_GeopandasV3's UI.
    And use the data selected from the UI to calculate isochrones and display them in QGIS.
    """
    def __init__(self):
        self.dlg = ui_mg_request_sirene()
    def run(self): 
        self.dlg.comboBox_layer_QGIS.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.dlg.comboBox_layer_QGIS.addItem(layer.name(), layer.id())
        self.dlg.fillListWidget(self.dlg.listWidget_field,usefullVariable.all_API_SIREN_fields)
        for i in range(12): #Pre-check the needed fields
            item2check=self.dlg.listWidget_field.item(i)
            item2check.setCheckState(Qt.Checked)  
            item2check.setFlags(item2check.flags() & ~Qt.ItemIsEnabled)  
        self.dlg.fillListWidget(self.dlg.listWidget_NAF,usefullVariable.nomenclature_NAFV2)
        ui = self.dlg.exec()

        if ui == QtWidgets.QDialog.Accepted:
            try:
                for index,data in enumerate(self.dlg.getQTableWidgetData()):
                    layer_selected, layer_name = self.dlg.prepLayer(index)
                    activity = data[4].split(',') if data[4] else []
                    request_parameters={
                    "api_key":data[1].split()[0], 
                    "champs": data[3],
                    "nombre": 100,
                    "curseur": '*',
                    "date": '2099-01-01'
                    }
                    if data[2]=='Selection from coordinates (Fastest)':
                        request_SIRENE_output = siretInPolygonFilteredByCoordinates(layer_selected, request_parameters, activity).establishments_SIRENE_in_polygon_coordinates()
                    elif data[2]=='Selection from address':
                        request_SIRENE_output = siretInPolygonFilteredByAddresses(layer_selected, request_parameters, activity).establishments_SIRENE_in_polygon_address()
                    else: 
                        request_coordinates = siretInPolygonFilteredByCoordinates(layer_selected, request_parameters, activity).establishments_SIRENE_in_polygon_coordinates()
                        request_addresse = siretInPolygonFilteredByAddresses(layer_selected, request_parameters, activity).establishments_SIRENE_in_polygon_address()
                        request_SIRENE_output = apiSireneUtils.mergeRequestTypeOutput(request_coordinates,request_addresse)
                    QgsProject.instance().addMapLayer(QgsVectorLayer(request_SIRENE_output.to_json(), "Siret_located_in_{}".format(layer_name), "ogr"))
            except Exception as e:
                raise e
