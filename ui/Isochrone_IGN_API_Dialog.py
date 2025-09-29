"""
/***************************************************************************
    This module contains the class to create the dialog UI for the 
    Isochrone_IGN_API.py script.
    It contains a class 'ui_mg_isochrone_ign' for the management of the UI 
    and data preparation. And another class 'ui_run_isochrone_ign' to run the 
    script through the UI. 
                             -------------------
        start                : 2025-05-20
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
from .utils import load_ui, prepVector
from ..library import Isochrone_API_IGN



from qgis.PyQt import QtWidgets
from qgis.core import QgsProject, QgsMapLayerType, QgsWkbTypes
from qgis.core import QgsVectorLayer

class ui_mg_isochrone_ign(QtWidgets.QDialog, load_ui('Isochrone_IGN_API.ui').FORM_CLASS):
    """ui_mg_isochrone_ign contains all the functions specifically designed to manage the UI
    and the data created from the UI to be used in the Isochrone_IGN_API.py script.

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
        self.comboBox_processingMode.currentIndexChanged.connect(self.update_processing_mode_parameters)
        self.list_layers = [] #List of layers id selected by the user, its purpose is a bit excessive but it is to avoid confusion in QGIS if several layers share the same name.
        self.gridLayout_input.addWidget(self.create_voronoi_parameters(), 2, 1)
        self.voronoi_subWidget.hide()
        self.comboBox_layer_QGIS.currentIndexChanged.connect(self.refreshKeyLayer)
        # Hide the key comboBox and label by default because the default processing mode is 0 (Merge isochrones by cost type)
        self.comboBox_key.hide()
        self.comboBox_key_label.hide()
        
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
                self.comboBox_processingMode.currentText(),
                {
                    'costType':self.comboBox_CostType.currentText(),
                    'resource':self.comboBox_resource.currentText(),
                    'profile':self.comboBox_profile.currentText(),
                    'direction':self.comboBox_location_type.currentText(),
                    'constraints': self.lineEdit_constraint.text(),
                    'distanceUnit':[i if i=='kilometer' else 'meter' for i in [self.comboBox_Unit.currentText()]][0],
                    'timeUnit':[i if i in ('second', 'minute', 'hour', 'standard') else 'minute' for i in [self.comboBox_Unit.currentText()]][0],
                    'voronoi_extend_layer':self.voronoi_comboBoxLayer.itemData(self.voronoi_comboBoxLayer.currentIndex()) if self.voronoi_comboBoxLayer.isVisible() else self.voronoi_comboBoxClipType.currentText() if self.voronoi_subWidget.isVisible() else None,
                    'key': self.comboBox_key.currentText() if self.comboBox_key.currentText() != "None" else None
                    }
                ]
            self.list_layers.append(self.comboBox_layer_QGIS.itemData(self.comboBox_layer_QGIS.currentIndex()))
            self.comboBox_layer_QGIS.setCurrentIndex(-1) #back to default
            self.comboBox_processingMode.setCurrentIndex(-1)
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

    def getQTableWidgetData(self,columnNumber=4) -> list[list]:
        """getQTableWidgetData returns data from the QTableWidget in a list of lists.
        each list contains the parameters for each row of the QTableWidget.
        
        Returns: A list of list[str,str,str(dict)] containing the parameters of each row.
        """
        data = []
        for row in range(self.tableWidget.rowCount()):
            data.append([self.tableWidget.item(row, col).text() for col in range(self.tableWidget.columnCount())])
        return [data[i:i+columnNumber] for i in range(0,len(data),columnNumber)][0]

    def update_unit_combobox(self):
        """update and populate comboBox_Unit based on the selected cost type (comboBox_CostType)"""
        self.comboBox_Unit.clear()
        if self.comboBox_CostType.currentText() == 'time':
            self.comboBox_Unit.addItems(['minute','second', 'hour', 'standard'])
        else:
            self.comboBox_Unit.addItems(['meter', 'kilometer'])

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

    def update_processing_mode_parameters(self, index):
        """Update the QGridLayout to show or hide the Voronoi processing mode parameters.
        Also show or hide the key comboBox and label based on the processing mode selected."""
        if index == 2:
            self.voronoi_subWidget.show()
        else:
            self.voronoi_subWidget.hide()
            
        if index == 2 or index == 1:
            self.comboBox_key.show()
            self.comboBox_key_label.show()
        else:
            self.comboBox_key.hide()
            self.comboBox_key_label.hide()

    def update_voronoi_clip_layer_parameters(self, index):
        """Update the QGridLayout to show or hide the Voronoi processing mode parameters."""
        if index == 3:
            self.voronoi_comboBoxLayer.show()
            self.voronoi_combobox_Polygon_label.show()
        else:
            self.voronoi_comboBoxLayer.hide()
            self.voronoi_combobox_Polygon_label.hide()
            
    def refreshKeyLayer(self):
        """Refresh the key comboBox comboBox_key with the attributes of the layer selected in the comboBox_layer_QGIS comboBox."""
        self.comboBox_key.clear()
        if self.comboBox_layer_QGIS.currentText()=="":
            pass
        else:
            layer=QgsProject.instance().mapLayer(self.comboBox_layer_QGIS.itemData(self.comboBox_layer_QGIS.currentIndex()))
            if layer is not None:
                fields = layer.fields()
                field_names = [field.name() for field in fields]
                self.comboBox_key.addItem("None") #Add an empty item at the top of the list
                self.comboBox_key.addItems(field_names)
        
        
    
class ui_run_isochrone_ign():
    """ui_run_isochrone_ign is used to run Isochrones_IGN_API's UI.
    And use the data selected from the UI to calculate isochrones and display them in QGIS.
    The crs of the layer used for the isochrones is set to EPSG:4326, same thing for the API output.
    """
    def __init__(self):
        self.dlg = ui_mg_isochrone_ign()
        self.dlg.voronoi_clip_options={'None':"None",'Bounding box':"layer.unary_union.envelope",'Convex hull':"layer.unary_union.convex_hull"}
    
    def run(self): 
        self.dlg.comboBox_layer_QGIS.clear()
        for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PointGeometry:
                        self.dlg.comboBox_layer_QGIS.addItem(layer.name(), layer.id())
        self.dlg.voronoi_comboBoxClipType.clear()
        self.dlg.voronoi_comboBoxClipType.addItems(['None','Bounding box','Convex hull', 'From a Polygon'])
        self.dlg.voronoi_comboBoxLayer.clear()
        for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                        self.dlg.voronoi_comboBoxLayer.addItem(layer.name(), layer.id())

        ui=self.dlg.exec()
        if ui == QtWidgets.QDialog.Accepted:
            try:
                for index,data in enumerate(self.dlg.getQTableWidgetData()):
                    layer_selected=QgsProject.instance().mapLayer(self.dlg.list_layers[index])
                    layer=prepVector.layer_to_geodataframe(layer_selected)
                    layer.to_crs('EPSG:4326', inplace=True)
                    parameters=eval(data[3])
                    if parameters['voronoi_extend_layer']:
                        if parameters['voronoi_extend_layer'] in self.dlg.voronoi_clip_options.keys():
                            parameters['voronoi_extend_layer']=eval(self.dlg.voronoi_clip_options[parameters['voronoi_extend_layer']])
                        else:
                            parameters['voronoi_extend_layer']=prepVector.layer_to_geodataframe(QgsProject.instance().mapLayer(parameters['voronoi_extend_layer'])).to_crs("EPSG:4326")
                            parameters['voronoi_extend_layer']=parameters['voronoi_extend_layer'].unary_union #union_all() if geopandas >= 1.0.0
                    processingMode = 0 if data[2] == 'Merge isochrones by cost type' else 1 if data[2] == 'Separate each isochron' else 2
                    isochrone=Isochrone_API_IGN(layer,list(map(int,data[1].split(','))),processingMode,**parameters)
                    QgsProject.instance().addMapLayer(QgsVectorLayer(isochrone.output, "Isochrone_IGN_{}".format(layer_selected.name()), "ogr"))
            except Exception as e:
                raise e