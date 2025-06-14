"""
/***************************************************************************
    This module contains the class to create the dialog UI for the 
    Isochrone_ORS_Tools_GeopandasV3.py script.
    It contains a class 'ui_mg_isochrone' for the management of the UI 
    and data preparation. And another class 'ui_run_isochrone' to run the 
    script through the UI. 
                             -------------------
        begin                : 2025-03-17
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky
 ***************************************************************************/
"""
from .utils import load_ui, prepVector
from ..library import Isochrone_ORS_V3_QGIS

from qgis.PyQt import QtWidgets
from qgis.core import QgsProject, QgsMapLayerType, QgsWkbTypes
from qgis.core import QgsVectorLayer

class ui_mg_isochrone(QtWidgets.QDialog, load_ui('Isochrone_ORS_Tools_API.ui').FORM_CLASS):
    """ui_mg_isochrone contains all the functions specifically designed to manage the UI
    and the data created from the UI to be used in the Isochrone_ORS_Tools_GeopandasV3.py script.

    Args:
        QtWidgets: QDialog class that forms the base class of our dialog window.
        load_ui : function that loads the .ui file and returns the class and the form.
    """
    def __init__(self,parent=None):
        """__init__ initializes the dialog window and connects the buttons to the functions.
        Hides the OK and delete buttons if the QTableWidget is empty."""
        super(ui_mg_isochrone, self).__init__(parent)
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
        self.spinBox_smoothing_factor.setValue(0)
        self.lineEdit_time_interval.clear()
        self.lineEdit_time_interval.setPlaceholderText("5, 10 ,15, 20 ...")
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
                try:
                    self.lineEdit_api_key.setStyleSheet("""QLineEdit { }""")
                    self.lineEdit_time_interval.setStyleSheet("""QLineEdit { }""")
                    CostValue=list(map(int,self.lineEdit_time_interval.text().split(',')))
                except Exception:
                    self.lineEdit_time_interval.setStyleSheet("""
                        QLineEdit {
                            color: red; /* Text color */
                            border: 1px solid red; /* Hollow red border */
                            border-radius: 2px; 
                            background-color: white; /* Optional: ensure background is not red */
                        }""")
                    return
                parameters=[
                    self.comboBox_layer_QGIS.currentText(),
                    self.comboBox_transportation_mode.currentText(),
                    self.lineEdit_time_interval.text(),
                    self.spinBox_smoothing_factor.value(),
                    self.comboBox_location_type.currentText(),
                    self.lineEdit_api_key.text()]
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

    def getQTableWidgetData(self,column_number:int=6):
        """getQTableWidgetData returns the data from the QTableWidget"""
        data = []
        for row in range(self.tableWidget.rowCount()):
            data.append([self.tableWidget.item(row, col).text() for col in range(self.tableWidget.columnCount())])
        return [data[i:i+column_number] for i in range(0,len(data),column_number)][0]

    def prepData(self, data: list, index:int):
        """prepData transforms the data from the QTableWidget and self.list_layers
        into a format that can be used by Isochrone_ORS_Tools_GeopandasV3.py"""
        layer_selected=QgsProject.instance().mapLayer(self.list_layers[index])
        layer=prepVector.layer_to_geodataframe(layer_selected)
        layer_name=layer_selected.name()
        transportation=data[1]
        interval_minute=[int(x) for x in data[2].split(",")]
        smoothing_factor=int(data[3])
        location_type=data[4]
        api_key=data[5]
        return layer,interval_minute,api_key,smoothing_factor,location_type,transportation,layer_name

class ui_run_isochrone():
    """ui_run_isochrone is used to run Isochrones_ORS_Tools_GeopandasV3's UI.
    And use the data selected from the UI to calculate isochrones and display them in QGIS.
    """
    def __init__(self):
        self.dlg = ui_mg_isochrone()
    
    def run(self): 
        self.dlg.comboBox_layer_QGIS.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PointGeometry:
                self.dlg.comboBox_layer_QGIS.addItem(layer.name(), layer.id())
        ui = self.dlg.exec()

        if ui == QtWidgets.QDialog.Accepted:
            try:
                if self.dlg.tableWidget.rowCount()==0:
                    QtWidgets.QMessageBox.warning(self.dlg, "Warning", "Please add at least one input.")
                    return
                else:
                    for index,data in enumerate(self.dlg.getQTableWidgetData()):
                        parameters=list(self.dlg.prepData(data,index))
                        isochrone_output=Isochrone_ORS_V3_QGIS(*parameters[:-1])
                        QgsProject.instance().addMapLayer(QgsVectorLayer(isochrone_output.result, "Isochrone_{}".format(parameters[-1]), "ogr"))
            except RuntimeError as e:
                raise e
            except ValueError as e:
                raise e
            except Exception as e:
                raise e
