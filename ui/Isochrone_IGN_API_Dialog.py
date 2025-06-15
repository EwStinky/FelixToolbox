"""
/***************************************************************************
    This module contains the class to create the dialog UI for the 
    Isochrone_IGN_API.py script.
    It contains a class 'ui_mg_isochrone_ign' for the management of the UI 
    and data preparation. And another class 'ui_run_isochrone_ign' to run the 
    script through the UI. 
                             -------------------
        begin                : 2025-05-20
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky
 ***************************************************************************/
"""
from .utils import load_ui, prepVector
from ..library import Isochrone_API_IGN

from qgis.PyQt import QtWidgets
from qgis.core import QgsProject, QgsMapLayerType, QgsWkbTypes
from qgis.core import QgsVectorLayer

class ui_mg_isochrone_ign(QtWidgets.QDialog, load_ui('Isochrone_IGN_API.ui').FORM_CLASS):
    """ui_mg_isochrone_ign contains all the functions specifically designed to manage the UI
    and the data created from the UI to be used in the Isochrone_ORS_Tools_GeopandasV3.py script.

    Args:
        QtWidgets: QDialog class that forms the base class of our dialog window.
        load_ui : function that loads the .ui file and returns the class and the form.
    """
    def __init__(self,parent=None):
        """__init__ initializes the dialog window and connects the buttons to the functions.
        Hides the OK and delete buttons if the QTableWidget is empty."""
        super(ui_mg_isochrone_ign, self).__init__(parent)
        self.setupUi(self)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.tableWidget.rowCount() > 0)
        self.pushButton_Ajouter_table.clicked.connect(self.addRowQTableWidget)
        self.pushButton_Effacer_ligne_table.clicked.connect(self.removeRwoQTableWidget)
        self.pushButton_Effacer_ligne_table.setEnabled(self.tableWidget.rowCount() > 0)
        self.comboBox_CostType.currentTextChanged.connect(self.update_unit_combobox)
        self.list_layers = [] #List of layers id selected by the user, its purpose is a bit excessive but it is to avoid confusion in QGIS if several layers share the same name.

    def closeEvent(self, event):
        """closeEvent is used to reset the widgets to their default settings.
        It is called when the user closes the window.
        """
        self.tableWidget.setRowCount(0)
        self.pushButton_Ajouter_table.clicked.disconnect()
        self.pushButton_Effacer_ligne_table.disconnect()
        self.lineEdit_CostValue.clear()
        self.lineEdit_CostValue.setPlaceholderText("5, 10 ,15, 20 ...")
        self.lineEdit_constraint.clear()
        self.lineEdit_constraint.setPlaceholderText('Ex: {"constraintType":"banned","key":"wayType","operator":"=","value":"autoroute"}')
        super().closeEvent(event)

    def addRowQTableWidget(self): 
        """addRowQTableWidget adds a row to  the QTableWidget 
        with the parameters selected by the user. And add the layer id to self.list_layers.
        Enables the OK and delete buttons if the QTableWidget is not empty.

        It checks if the user has enter parameters in the QlineEdit.
        If not, the missing or wrong input will be highlighted in red
        """
        if self.comboBox_layer_QGIS.currentText()=="": #Check if the user has selected a layer
            pass

        else:
            try:
                self.lineEdit_CostValue.setStyleSheet("""QLineEdit { }""")
                CostValue=list(map(int,self.lineEdit_CostValue.text().split(',')))
            except Exception:
                self.lineEdit_CostValue.setStyleSheet("""
                    QLineEdit {
                        color: red; /* Text color */
                        border: 1px solid red; /* Hollow red border */
                        border-radius: 2px; 
                        background-color: white; /* Optional: ensure background is not red */
                    }""")
                return
            parameters=[
                self.comboBox_layer_QGIS.currentText(),
                self.lineEdit_CostValue.text(),
                {
                    'costType':self.comboBox_CostType.currentText(),
                    'resource':self.comboBox_resource.currentText(),
                    'profile':self.comboBox_profile.currentText(),
                    'direction':self.comboBox_location_type.currentText(),
                    'constraints': self.lineEdit_constraint.text(),
                    'distanceUnit':[i if i=='kilometer' else 'meter' for i in [self.comboBox_Unit.currentText()]][0],
                    'timeUnit':[i if i in ('second', 'minute', 'hour', 'standard') else 'minute' for i in [self.comboBox_Unit.currentText()]][0],
                    }
                ]
            self.list_layers.append(self.comboBox_layer_QGIS.itemData(self.comboBox_layer_QGIS.currentIndex()))
            self.comboBox_layer_QGIS.setCurrentIndex(-1) #back to default
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

    def update_unit_combobox(self):
        """update and populate comboBox_Unit based on the selected cost type (comboBox_CostType)"""
        self.comboBox_Unit.clear()
        if self.comboBox_CostType.currentText() == 'time':
            self.comboBox_Unit.addItems(['minute','second', 'hour', 'standard'])
        else:
            self.comboBox_Unit.addItems(['meter', 'kilometer'])

    def getQTableWidgetData(self,columnNumber=3) -> list[list]:
        """getQTableWidgetData returns data from the QTableWidget in a list of lists.
        each list contains the parameters for each row of the QTableWidget.
        
        Returns: A list of list[str,str,str(dict)] containing the parameters of each row.
        """
        data = []
        for row in range(self.tableWidget.rowCount()):
            data.append([self.tableWidget.item(row, col).text() for col in range(self.tableWidget.columnCount())])
        return [data[i:i+columnNumber] for i in range(0,len(data),columnNumber)][0]


class ui_run_isochrone_ign():
    """ui_run_isochrone_ign is used to run Isochrones_IGN_API's UI.
    And use the data selected from the UI to calculate isochrones and display them in QGIS.
    The crs of the layer used for the isochrones is set to EPSG:4326, same thing for the API output.
    """
    def __init__(self):
        self.dlg = ui_mg_isochrone_ign()
    
    def run(self): 
        self.dlg.comboBox_layer_QGIS.clear()
        for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PointGeometry:
                        self.dlg.comboBox_layer_QGIS.addItem(layer.name(), layer.id())

        ui=self.dlg.exec()

        if ui == QtWidgets.QDialog.Accepted:
            try:
                for index,data in enumerate(self.dlg.getQTableWidgetData()):
                    layer_selected=QgsProject.instance().mapLayer(self.dlg.list_layers[index])
                    layer=prepVector.layer_to_geodataframe(layer_selected)
                    layer.to_crs('EPSG:4326', inplace=True)
                    isochrone=Isochrone_API_IGN(layer,list(map(int,data[1].split(','))),**eval(data[2]))
                    QgsProject.instance().addMapLayer(QgsVectorLayer(isochrone.output, "Isochrone_{}".format(layer_selected.name()), "ogr"))
            except RuntimeError as e:
                raise e
            except ValueError as e:
                raise e
            except Exception as e:
                raise e