"""
/***************************************************************************
    This module contains the class to create the dialog UI for the 
    Isochrone_ORS_Tools_GeopandasV3.py script.
    It contains a class 'ui_mg_isochrone' for the management of the UI 
    and data preparation. And another class 'ui_run_isochrone' to run the 
    script through the UI. 
                             -------------------
        start                : 2025-03-17
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
from .utils import load_ui, prepVector, UI_tools
from ..library import Isochrone_API_ORS

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
        self.comboBox_processing_mode.currentIndexChanged.connect(self.update_voronoi_parameters)
        self.list_layers = [] #List of layers id selected by the user, its purpose is a bit excessive but it is to avoid confusion in QGIS if several layers share the same name.
        self.gridLayout_input.addWidget(self.create_voronoi_parameters(), 2, 2)
        self.voronoi_subWidget.hide()        

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
                    self.lineEdit_api_key.text(),
                    self.comboBox_processing_mode.currentText(),
                    {
                    'transportation':self.comboBox_transportation_mode.currentText(),
                    'interval_minutes':[int(x) for x in self.lineEdit_time_interval.text().split(",")],
                    'smoothing': self.spinBox_smoothing_factor.value(),
                    'location_type':self.comboBox_location_type.currentText(),
                    'voronoi_extend_layer':self.voronoi_comboBoxLayer.itemData(self.voronoi_comboBoxLayer.currentIndex()) if self.voronoi_comboBoxLayer.isVisible() else self.voronoi_comboBoxClipType.currentText() if self.voronoi_subWidget.isVisible() else None
                    }]
                self.list_layers.append(self.comboBox_layer_QGIS.itemData(self.comboBox_layer_QGIS.currentIndex()))
                self.comboBox_layer_QGIS.setCurrentIndex(-1) 
                self.comboBox_processing_mode.setCurrentIndex(-1)
                self.voronoi_comboBoxClipType.setCurrentIndex(-1)
                self.voronoi_comboBoxLayer.setCurrentIndex(-1)
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

    def getQTableWidgetData(self,column_number:int=4):
        """getQTableWidgetData returns the data from the QTableWidget"""
        data = []
        for row in range(self.tableWidget.rowCount()):
            data.append([self.tableWidget.item(row, col).text() for col in range(self.tableWidget.columnCount())])
        return [data[i:i+column_number] for i in range(0,len(data),column_number)][0]
    
    def create_voronoi_parameters(self):
        """Creates a QtWidget containing the Voronoi processing mode parameters."""
        self.voronoi_subWidget = QtWidgets.QWidget()
        self.voronoi_subLayout = QtWidgets.QGridLayout()
        self.voronoi_subWidget.setLayout(self.voronoi_subLayout)
        self.voronoi_combobox_label=QtWidgets.QLabel("Clip the Voronoï's cells:")
        self.voronoi_combobox_Polygon_label=QtWidgets.QLabel("Select a polygon layer to clip the cells from")
        self.voronoi_subLayout.addWidget(self.voronoi_combobox_label, 0, 0)
        self.voronoi_subLayout.addWidget(self.voronoi_combobox_Polygon_label, 0, 1)
        self.voronoi_comboBoxClipType = QtWidgets.QComboBox()
        self.voronoi_comboBoxLayer = QtWidgets.QComboBox()
        self.voronoi_subLayout.addWidget(self.voronoi_comboBoxClipType, 1, 0)
        self.voronoi_subLayout.addWidget(self.voronoi_comboBoxLayer, 1, 1)
        self.voronoi_comboBoxLayer.hide()
        self.voronoi_combobox_Polygon_label.hide()
        self.voronoi_comboBoxClipType.currentIndexChanged.connect(self.update_voronoi_clip_layer_parameters)
        return self.voronoi_subWidget

    def update_voronoi_parameters(self, index):
        """Update the QGridLayout to show or hide the Voronoi processing mode parameters."""
        if index == 2:
            self.voronoi_subWidget.show()
        else:
            self.voronoi_subWidget.hide()

    def update_voronoi_clip_layer_parameters(self, index):
        """Update the QGridLayout to show or hide the Voronoi processing mode parameters."""
        if index == 3:
            self.voronoi_comboBoxLayer.show()
            self.voronoi_combobox_Polygon_label.show()
        else:
            self.voronoi_comboBoxLayer.hide()
            self.voronoi_combobox_Polygon_label.hide()

class ui_run_isochrone():
    """ui_run_isochrone is used to run Isochrones_ORS_Tools_GeopandasV3's UI.
    And use the data selected from the UI to calculate isochrones and display them in QGIS.
    """
    def __init__(self):
        self.dlg = ui_mg_isochrone()
        self.dlg.voronoi_clip_options={'None':"None",'Bounding box':"layer.unary_union.envelope",'Convex hull':"layer.unary_union.convex_hull"}
    
    def run(self): 
        self.dlg.comboBox_layer_QGIS.clear()
        self.dlg.lineEdit_api_key.setText(UI_tools.read_API_key('ORS_API_KEY'))
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PointGeometry:
                self.dlg.comboBox_layer_QGIS.addItem(layer.name(), layer.id())
        self.dlg.voronoi_comboBoxClipType.clear()
        self.dlg.voronoi_comboBoxClipType.addItems(['None','Bounding box','Convex hull', 'From a Polygon'])
        self.dlg.voronoi_comboBoxLayer.clear()
        for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                        self.dlg.voronoi_comboBoxLayer.addItem(layer.name(), layer.id())
        ui = self.dlg.exec()

        if ui == QtWidgets.QDialog.Accepted:
            try:
                for index,data in enumerate(self.dlg.getQTableWidgetData()):
                    layer_selected=QgsProject.instance().mapLayer(self.dlg.list_layers[index])
                    layer=prepVector.layer_to_geodataframe(layer_selected)
                    layer.to_crs('EPSG:4326', inplace =True)
                    parameters=eval(data[3])
                    parameters['smoothing'] = int(parameters['smoothing'])
                    parameters['interval_minutes'] = list(map(int,parameters['interval_minutes']))
                    if parameters['voronoi_extend_layer']:
                        if parameters['voronoi_extend_layer'] in self.dlg.voronoi_clip_options.keys():
                            parameters['voronoi_extend_layer']=eval(self.dlg.voronoi_clip_options[parameters['voronoi_extend_layer']])
                        else:
                            parameters['voronoi_extend_layer']=prepVector.layer_to_geodataframe(QgsProject.instance().mapLayer(parameters['voronoi_extend_layer'])).to_crs("EPSG:4326")
                            parameters['voronoi_extend_layer']=parameters['voronoi_extend_layer'].unary_union #union_all() if geopandas >= 1.0.0
                    processingMode = 0 if data[2] == 'Merge isochrones by cost type' else 1 if data[2] == 'Separate each isochron' else 2
                    isochrone_output=Isochrone_API_ORS(layer,data[1],processing_mode=processingMode, **parameters)
                    QgsProject.instance().addMapLayer(QgsVectorLayer(isochrone_output.result, "Isochrone_ORS_{}".format(layer_selected.name()), "ogr"))
            except RuntimeError as e:
                raise e
            except ValueError as e:
                raise e
            except Exception as e:
                raise e
