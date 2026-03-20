"""
/***************************************************************************
    This module contains the class to create the dialog UI for the 
    Itinerary_IGN_API.py script.
    It contains a class 'ui_mg_itinerary_ign' for the management of the UI 
    and data preparation. And another class 'ui_run_itinerary_ign' to run the 
    script through the UI. 
                             -------------------
        start                : 2026-03-18
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
from .utils import load_ui, prepVector
from ..library import ItineraireIGN
from qgis.PyQt import QtWidgets
from qgis.core import QgsProject, QgsMapLayerType, QgsWkbTypes
from qgis.core import QgsVectorLayer

class ui_mg_itinerary_ign(QtWidgets.QDialog, load_ui('Itinerary_IGN_API.ui').FORM_CLASS):
    """ui_mg_itinerary_ign contains all the functions specifically designed to manage the UI
    and the data created from the UI to be used in the Itinerary_IGN_API.py script.

    Args:
        QtWidgets: QDialog class that forms the base class of our dialog window.
        load_ui : function that loads the .ui file and returns the class and the form.
    """
    def __init__(self,parent=None):
        """__init__ initializes the dialog window and connects the buttons to the functions.
        Hides the OK and delete buttons if the QTableWidget is empty."""
        super(ui_mg_itinerary_ign, self).__init__(parent)
        self.setupUi(self)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.tableWidget.rowCount() > 0)
        self.pushButton_Ajouter_table.clicked.connect(self.addRowQTableWidget)
        self.pushButton_Effacer_ligne_table.clicked.connect(self.removeRwoQTableWidget)
        self.pushButton_Effacer_ligne_table.setEnabled(self.tableWidget.rowCount() > 0)
        self.comboBox_processingMode.currentIndexChanged.connect(self.update_processing_mode_parameters)
        self.list_layers = [] 
        self.comboBox_departure.currentIndexChanged.connect(self.refreshKeyLayer)
        # Hide some parameters because processing mode is 0 at start
        self.spinBox_MaximumTime.hide()
        self.label_MaximumTime.hide()
        self.comboBox_orderColumn.hide()
        self.label_orderColumn.hide()
        self.comboBox_groupByColumn.hide()
        self.label_groupByColumn.hide()
        
    def closeEvent(self, event):
        """closeEvent is used to reset the widgets to their default settings.
        It is called when the user closes the window.
        """
        self.tableWidget.setRowCount(0)
        self.pushButton_Ajouter_table.clicked.disconnect()
        self.pushButton_Effacer_ligne_table.disconnect()
        self.lineEdit_intermediates.clear()
        self.lineEdit_constraint.clear()
        self.lineEdit_constraint.setPlaceholderText('Ex: {"constraintType":"banned","key":"wayType","operator":"=","value":"autoroute"}')
        super().closeEvent(event)

    def addRowQTableWidget(self): 
        """addRowQTableWidget adds a row to  the QTableWidget 
        with the parameters selected by the user. And add the layer id to self.list_layers.
        Enables the OK and delete buttons if the QTableWidget is not empty.

        It checks if the user has enter parameters in the QlineEdit or QComboBox.
        If not, the missing or wrong input will be highlighted in red
        """
        if self.comboBox_processingMode.currentIndex()<2:
            self.comboBox_departure.setStyleSheet("""QComboBox { }""")
            if self.comboBox_departure.currentText()=="": #Check if the user has selected a layer
                self.comboBox_departure.setStyleSheet("""
                    QComboBox {
                        color: red; /* Text color */
                        border: 1px solid red; /* Hollow red border */
                        border-radius: 2px; 
                        background-color: white; /* Optional: ensure background is not red */
                    }""")
                return
            self.comboBox_arrival.setStyleSheet("""QComboBox { }""")
            if self.comboBox_arrival.currentText()=="":
                self.comboBox_arrival.setStyleSheet("""
                    QComboBox {
                        color: red; /* Text color */
                        border: 1px solid red; /* Hollow red border */
                        border-radius: 2px; 
                        background-color: white; /* Optional: ensure background is not red */
                    }""")
                return
        if self.comboBox_processingMode.currentIndex()==2:
            self.comboBox_orderColumn.setStyleSheet("""QComboBox { }""")
            if self.comboBox_orderColumn.currentText()=="":
                self.comboBox_orderColumn.setStyleSheet("""
                    QComboBox {
                        color: red; /* Text color */
                        border: 1px solid red; /* Hollow red border */
                        border-radius: 2px; 
                        background-color: white; /* Optional: ensure background is not red */
                    }""")
                return

        parameters=[
            self.comboBox_departure.currentText(),
            self.comboBox_arrival.currentText() if self.comboBox_arrival.isVisible() else None,
            self.comboBox_processingMode.currentIndex(),
            {
                'primaryKey':self.comboBox_key.currentText() if self.comboBox_key.currentText()!='None' else None,
                'resource':self.comboBox_resource.currentText(),
                'optimization':self.comboBox_Optimization.currentText(),
                'profile':self.comboBox_profile.currentText(),
                'distanceUnit':self.comboBox_DistanceUnit.currentText(),
                'timeUnit':self.comboBox_TimeUnit.currentText(),
                'intermediates':self.lineEdit_intermediates.text(),
                'constraints': self.lineEdit_constraint.text(),
                'maximalTime':self.spinBox_MaximumTime.value() if self.spinBox_MaximumTime.isVisible() else None,
                'orderColumn':self.comboBox_orderColumn.currentText() if self.comboBox_orderColumn.isVisible() else None,
                'groupByColumn': self.comboBox_groupByColumn.currentText() if all([self.comboBox_groupByColumn.isVisible(),self.comboBox_groupByColumn.currentText()!='None']) else None
                }
            ]
        self.list_layers.append(
            [self.comboBox_departure.itemData(self.comboBox_departure.currentIndex()),
                self.comboBox_arrival.itemData(self.comboBox_arrival.currentIndex()) if self.comboBox_arrival.isVisible() else None]
        )
        self.comboBox_departure.setCurrentIndex(-1) #back to default
        self.comboBox_arrival.setCurrentIndex(-1)
        self.comboBox_processingMode.setCurrentIndex(0)
        self.comboBox_orderColumn.setCurrentIndex(-1)
        self.comboBox_key.setCurrentIndex(-1)
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

    def getQTableWidgetData(self,columnNumber=4) -> list[list]:
        """getQTableWidgetData returns data from the QTableWidget in a list of lists.
        each list contains the parameters for each row of the QTableWidget.
        
        Returns: A list of list[str,str,str(dict)] containing the parameters of each row.
        """
        data = []
        for row in range(self.tableWidget.rowCount()):
            data.append([self.tableWidget.item(row, col).text() for col in range(self.tableWidget.columnCount())])
        return [data[i:i+columnNumber] for i in range(0,len(data),columnNumber)][0]

    def update_processing_mode_parameters(self, index):
        """Update the QGridLayout to show or hide the Voronoi processing mode parameters.
        Also show or hide the key comboBox and label based on the processing mode selected."""
        if index == 1:
            self.spinBox_MaximumTime.show()
            self.label_MaximumTime.show()
        else:
            self.spinBox_MaximumTime.hide()
            self.label_MaximumTime.hide()
            
        if index == 2:
            self.comboBox_orderColumn.show()
            self.label_orderColumn.show()
            self.comboBox_groupByColumn.show()
            self.label_groupByColumn.show()
            self.comboBox_arrival.hide()
            self.label_arrival.hide()
            self.comboBox_key.hide()
            self.comboBox_key_label.hide()

        else:
            self.comboBox_orderColumn.hide()
            self.label_orderColumn.hide()
            self.comboBox_groupByColumn.hide()
            self.label_groupByColumn.hide()
            self.label_arrival.show()
            self.comboBox_arrival.show()
            self.comboBox_key.show()
            self.comboBox_key_label.show()
            
    def refreshKeyLayer(self):
        """Refresh some specific comboBoxes depending with the attributes of the layer selected in self.comboBox_departure."""
        self.comboBox_key.clear()
        self.comboBox_orderColumn.clear()
        self.comboBox_groupByColumn.clear()
        if self.comboBox_departure.currentText()=="":
            pass
        else:
            layer=QgsProject.instance().mapLayer(self.comboBox_departure.itemData(self.comboBox_departure.currentIndex()))
            if layer is not None:
                fields = layer.fields()
                field_names = [field.name() for field in fields]
                self.comboBox_key.addItem("None") #Add an empty item at the top of the list
                self.comboBox_key.addItems(field_names)
                self.comboBox_orderColumn.addItems(field_names)
                self.comboBox_groupByColumn.addItem("None") 
                self.comboBox_groupByColumn.addItems(field_names)
        
class ui_run_itinerary_ign():
    """ui_run_itinerary_ign is used to run Itinerary_IGN_API's UI.
    And use the data selected from the UI to calculate itineraries and display them in QGIS.
    The crs of the layer used for the itinerary is set to EPSG:4326, same thing for the API output.
    """
    def __init__(self):
        self.dlg = ui_mg_itinerary_ign()

    def run(self): 
        self.dlg.comboBox_departure.clear()
        for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PointGeometry:
                        self.dlg.comboBox_departure.addItem(layer.name(), layer.id())
        self.dlg.comboBox_arrival.clear()
        for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PointGeometry:
                        self.dlg.comboBox_arrival.addItem(layer.name(), layer.id())

        ui=self.dlg.exec()
        if ui == QtWidgets.QDialog.Accepted:
            try:
                for index,data in enumerate(self.dlg.getQTableWidgetData()):
                    departure_layer=QgsProject.instance().mapLayer(self.dlg.list_layers[index][0])
                    departure_gdf=prepVector.layer_to_geodataframe(departure_layer)
                    departure_gdf=departure_gdf.to_crs('EPSG:4326') if departure_gdf.crs!='EPSG:4326' else departure_gdf
                    parameters=eval(data[3])
                    if data[2] != 'Sequential point routing from a single layer':
                        arrival_gdf=prepVector.layer_to_geodataframe(QgsProject.instance().mapLayer(self.dlg.list_layers[index][1]))
                        parameters['end'] = arrival_gdf.to_crs('EPSG:4326') if arrival_gdf.crs !='EPSG:4326' else arrival_gdf
                    itinerary=ItineraireIGN(departure_gdf,int(data[2]),**parameters)
                    QgsProject.instance().addMapLayer(QgsVectorLayer(itinerary.output, "Itinerary_IGN_{}".format(departure_layer.name()), "ogr"))
            except Exception as e:
                raise e