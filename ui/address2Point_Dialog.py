"""
/***************************************************************************
    This module contains the class to create the dialog UI for the 
    address2point.py script. It contains a class 'ui_mg_addresse2point' 
    for the management of the UI and data preparation. 
    And another class 'ui_run_address2point' to run the script through the UI. 
                             -------------------
        begin                : 2025-03-17
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky
 ***************************************************************************/
"""
from .utils import load_ui, prepVector
from ..library import AddressSearch
import time
import csv
import pandas as pd
import geopandas as gpd

from qgis.PyQt import QtWidgets
from qgis.core import QgsProject, QgsMapLayerType, QgsWkbTypes
from qgis.core import QgsVectorLayer

class ui_mg_address2point(QtWidgets.QDialog, load_ui('Address2Point.ui').FORM_CLASS):
    """ui_mg_address2point contains all the functions specifically designed to manage the UI
    and the data created from the UI to be used in the address2point.py script.

    Args:
        QtWidgets: QDialog class that forms the base class of our dialog window.
        load_ui : function that loads the .ui file and returns the class and the form.
    """
    def __init__(self,parent=None):
        """__init__ initializes the dialog window and connects the buttons to the functions."""
        super(ui_mg_address2point, self).__init__(parent)
        self.setupUi(self)
        self.pushButton_Ajouter_table_Tab1.clicked.connect(self.addRowQTableWidget)
        self.pushButton_Effacer_ligne_table_Tab1.clicked.connect(self.removeRwoQTableWidget)
        self.pushButton_csv_file_load_Tab2.clicked.connect(self.load_csv)

    #Individual geocoding Tab
    def addRowQTableWidget(self): 
        """addRowQTableWidget adds a row to  the QTableWidget 
        with the parameters selected by the user.

        It checks if the user has enter parameters in the QlineEdit.
        If not, the missing or wrong input will be highlighted in red
        """
        #Nominatim API
        if self.stackedWidget_Tab1.currentIndex()==0: 
            if self.lineEdit_AddressInput_Nominatim_Tab1.text() == '':
                try:
                    CostValue=list(map(int,self.lineEdit_AddressInput_Nominatim_Tab1.text().split(',')))
                except Exception:
                    self.lineEdit_AddressInput_Nominatim_Tab1.setStyleSheet("""
                        QLineEdit {
                            color: red; /* Text color */
                            border: 1px solid red; /* Hollow red border */
                            border-radius: 2px; 
                            background-color: white; /* Optional: ensure background is not red */
                        }""")
                    return
            else:
                self.lineEdit_AddressInput_Nominatim_Tab1.setStyleSheet("""QLineEdit { }""")
                parameters=[
                    self.lineEdit_AddressInput_Nominatim_Tab1.text(),
                    'Nominatim',
                    {
                        'limit': self.spinBox_Limit_Nominatim_Tab1.value(),
                        'addressdetails': 1 if self.checkBox_AddressDetail_Nominatim_Tab1.isChecked() else 0,
                        'extratags': 1 if self.checkBox_ExtraTag_Nominatim_Tab1.isChecked() else 0,
                        'namedetails': 1 if self.checkBox_ExtraName_Nominatim_Tab1.isChecked() else 0 ,
                        'dedupe': 1 if self.checkBox_dedupe_Nominatim_Tab1.isChecked() else 0,
                        'countrycodes': self.lineEdit_countrycodes_Nominatim_Tab1.text() if self.lineEdit_countrycodes_Nominatim_Tab1.text() != '' else None,
                        'layer': self.lineEdit_layer_Nominatim_Tab1.text() if self.lineEdit_layer_Nominatim_Tab1.text() !='' else None,
                        'featureType': self.comboBox_featureType_Tab1_Nominatim.currentText() if self.comboBox_featureType_Tab1_Nominatim.currentText() !='' else None,
                        'viewbox': self.lineEdit_viewBox_Nominatim_Tab1.text() if self.lineEdit_viewBox_Nominatim_Tab1.text() != '' else None
                    }]
                numRows = self.tableWidget_Tab1.rowCount()
                self.tableWidget_Tab1.insertRow(numRows) # Create a empty row at bottom of table
                for i in range(len(parameters)): #populate the row
                    self.tableWidget_Tab1.setItem(numRows, i, QtWidgets.QTableWidgetItem(str(parameters[i])))

        #BAN API
        elif self.stackedWidget_Tab1.currentIndex()==1: 
            if self.lineEdit_AddressInput_BAN_Tab1.text() == '':
                try:
                    CostValue=list(map(int,self.lineEdit_AddressInput_BAN_Tab1.text().split(',')))
                except Exception:
                    self.lineEdit_AddressInput_BAN_Tab1.setStyleSheet("""
                        QLineEdit {
                            color: red; /* Text color */
                            border: 1px solid red; /* Hollow red border */
                            border-radius: 2px; 
                            background-color: white; /* Optional: ensure background is not red */
                        }""")
                    return
            else:
                self.lineEdit_AddressInput_BAN_Tab1.setStyleSheet("""QLineEdit { }""")
                parameters=[
                    self.lineEdit_AddressInput_BAN_Tab1.text(),
                    'BAN',
                    {
                        'limit': self.spinBox_Limit_BAN_Tab1.value(),
                        'autocomplete': 1 if self.checkBox_Autocomplete_BAN_Tab1.isChecked() else 0,
                        'citycode': self.lineEdit_cityCodes_BAN_Tab1.text() if self.lineEdit_cityCodes_BAN_Tab1.text() != '' else None,
                        'postcode': self.lineEdit_postCode_BAN_Tab1.text() if self.lineEdit_postCode_BAN_Tab1.text() != '' else None,
                        'type': self.comboBox_locationType_Tab1_BAN.currentText() if self.comboBox_locationType_Tab1_BAN.currentText() != '' else None,
                        'lat': [float(x) for x in self.lineEdit_coords_BAN_Tab1.text().split(",")][0] if self.lineEdit_coords_BAN_Tab1.text() != '' else None,
                        'lon': [float(x) for x in self.lineEdit_coords_BAN_Tab1.text().split(",")][1] if self.lineEdit_coords_BAN_Tab1.text() != '' else None
                    }]
                numRows = self.tableWidget_Tab1.rowCount()
                self.tableWidget_Tab1.insertRow(numRows)
                for i in range(len(parameters)):
                    self.tableWidget_Tab1.setItem(numRows, i, QtWidgets.QTableWidgetItem(str(parameters[i])))
        else:
            raise ValueError("Invalid API choice.")        

    def removeRwoQTableWidget(self):
        """removeRwoQTableWidget removes the selected row from the QTableWidget."""
        row = self.tableWidget_Tab1.currentRow()
        self.tableWidget_Tab1.removeRow(row)

    def getQTableWidgetData(self,columnNumber=3) -> list[list]:
        """getQTableWidgetData returns data from the QTableWidget in a list of lists.
        each list contains the parameters for each row of the QTableWidget.
        
        Returns: A list of list[str,str,str(dict)] containing the parameters of each row.
        """
        data = []
        for row in range(self.tableWidget_Tab1.rowCount()):
            data.append([self.tableWidget_Tab1.item(row, col).text() for col in range(self.tableWidget_Tab1.columnCount())])
        return [data[i:i+columnNumber] for i in range(0,len(data),columnNumber)][0]
    
    @staticmethod
    def processAPI_Tab1(data: list) -> list:
        """processAPI_Tab1 will use address2point.py functions to geocode individually each row of the QTableWidget.
        Each row is transformed into a specific format list[API, address, other parameters..] 
        and then passed to the AddressSearch class. AddressSearch uses these parameters to geocode the address.
        The result will be stored in a list of GeoDataFrame objects that will be merged into 
        a single GeoDataFrame, that will be separated into several gdf according to the geometry type of each row
        (Mostly point, but can be polygon with Nominatim).

        It will respect the usage policies of the APIs used:
            - Nominatim: maximum 1 request / second
            - BAN: maximum 50 requests / second / ip (count_BAN)

        Args:
            data (list[str,str,str(dict)]) : list returned by getQTableWidgetData() or by the CSV file

        Raises (probably from AddressSearch):
            ValueError: If the API choice is invalid
            RuntimeError : If an error occurs during the API request
            Exception: If an unexpected error occurs

        Returns: A list of gpd.GeoDataFrame objects, each gdf represents a type of geometry which 
        may contain the results of several API requests. (I)
        """
        try:
            output_list=[]
            count_BAN=0
            for index,row in enumerate(data):
                input=[row[1],row[0],*list(eval(row[2]).values())]
                if input[0]=='BAN': #Apply usage policies of the API
                    count_BAN+=1
                    if count_BAN>50:
                        time.sleep(1)
                        count_BAN=0
                        output_api=AddressSearch(input[0], input[1:]).result
                        output_api['INDEX']= index
                        output_api['API']= 'BAN'
                        output_api['ADDRESS']= input[1]
                        output_list.append(output_api)
                    else:
                        output_api=AddressSearch(input[0], input[1:]).result
                        output_api['INDEX']= index
                        output_api['API']= 'BAN'
                        output_api['ADDRESS']= input[1]
                        output_list.append(output_api)
                else:
                    time.sleep(1.2)
                    output_api=AddressSearch(input[0], input[1:]).result
                    output_api['INDEX']= index
                    output_api['API']= 'Nominatim'
                    output_api['ADDRESS']= input[1]
                    output_list.append(output_api)
            return prepVector.separate_gdf_by_geometry(gpd.GeoDataFrame(pd.concat(output_list, ignore_index=True)))
        except RuntimeError as e:
            raise e
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    #CSV geocoding Tab
    def load_csv(self):
        """loads a CSV file and populates the QTableWidget of the UI with the data.
        it then populate the comboBox with the header of the CSV file to select the address column.
        """
        file_path = self.mQgsFileWidget_Tab2.filePath()
        if file_path:
            with open(file_path, mode='r', encoding='{}'.format(self.comboBox_2_csv_encoding_Tab2.currentText()), newline='') as file:
                data = list(csv.reader(file, delimiter='{}'.format(self.lineEdit_csv_delimiter_Tab2.text())))
                if not data:
                    return

                self.tableWidget_Tab2.setRowCount(len(data) - 1)  # Subtract 1 for the header row
                self.tableWidget_Tab2.setColumnCount(len(data[0]))
                for row_index, row_data in enumerate(data[1:]):  # Skip the header row
                    for col_index, cell_data in enumerate(row_data):
                        self.tableWidget_Tab2.setItem(row_index, col_index, QtWidgets.QTableWidgetItem(cell_data))
                self.tableWidget_Tab2.setHorizontalHeaderLabels(data[0])

                self.comboBox_address_column_Tab2.clear()
                self.comboBox_address_column_Tab2.addItems(data[0])

    def getAddressColumn(self):
        """getAddressColumn returns the index (int) of the address column
        select by the user in the comboBox_address_column_Tab2
        """
        for i in range(self.tableWidget_Tab2.columnCount()):
            if self.tableWidget_Tab2.horizontalHeaderItem(i).text() == '{}'.format(self.comboBox_address_column_Tab2.currentText()):
                return i
        
    def processAPI_Tab2(self):
        """processApi_Tab2 will use address2point.py functions to geocode individually each row of the QTableWidget.
        Each row is passed to the AddressSearch class with the API selected by the user. 

        It will respect the usage policies of the APIs used:
            - Nominatim: maximum 1 request / second
            - BAN: maximum 50 requests / second / ip (count_BAN)

        Raises (probably from AddressSearch):
            ValueError: If the API choice is invalid
            RuntimeError : If an error occurs during the API request
            Exception: If an unexpected error occurs

        Yields:
            gpd.GeoDataFrame: the output of the AddressSearch class, 
            with the input address added to the gdf.
        """
        try:
            if self.comboBox_API_selection_Tab2.currentText() == 'BAN (adresse.data.gouv.fr)':
                count_BAN=0
                for row in range(self.tableWidget_Tab2.rowCount()):
                    item = self.tableWidget_Tab2.item(row, self.getAddressColumn())
                    if item is not None:
                        count_BAN+=1
                        if count_BAN > 50:
                            time.sleep(1)
                            count_BAN=0
                            output=AddressSearch('BAN', [item.text(), 1]).result
                            output['ADDRESS']= item.text()
                            yield output
                        else:
                            output=AddressSearch('BAN', [item.text(), 1]).result
                            output['ADDRESS']= item.text()
                            yield output
            else: 
                for row in range(self.tableWidget_Tab2.rowCount()):
                    item = self.tableWidget_Tab2.item(row, self.getAddressColumn())
                    if item is not None:
                        time.sleep(1.2)
                        output=AddressSearch('Nominatim', [item.text(), 1]).result
                        output['ADDRESS']= item.text()
                        yield output
        except RuntimeError as e:
            raise e
        except ValueError as e:
            raise e
        except Exception as e:
            raise e

class ui_run_address2point():
    """ui_mg_address2point is used to run address2point's UI.
    Use the data and API selected from the UI to geocode addresses and display them in QGIS.
    It also respects the usage policies of the APIs used:
        - Nominatim: maximum 1 request / second 
        - BAN: maximum 50 requests / second / ip
    """
    def __init__(self):
        self.dlg = ui_mg_address2point()
    
    def run(self): 
        """Run the UI and geocode the addresses selected by the user
        and display them within QGIS

        Args:
            count_BAN (int): Counter for the number of requests sent to the BAN API.

        Raises (probably from processAPI):
            ValueError: If the API choice is invalid or if the input is not valid
            RuntimeError: If an error occurs during the API request
            Exception: If an unexpected error occurs
        """
        self.dlg.show()
        if self.dlg.exec_():
            try:
                if self.dlg.tabWidget.currentIndex()==0: #Individual geocoding
                    if self.dlg.tableWidget_Tab1.rowCount()==0:
                        QtWidgets.QMessageBox.warning(self.dlg, "Warning", "Please add at least one address.")
                        return
                    else:
                        data=self.dlg.getQTableWidgetData()
                        output=ui_mg_address2point.processAPI_Tab1(data)
                        for gdf in output:
                            layer_name = '{}_{}'.format(self.dlg.lineEdit_Output_Name.text(),gdf.geom_type.unique()[0])
                            layer = QgsVectorLayer(gdf.to_json(), layer_name, 'ogr')
                            QgsProject.instance().addMapLayer(layer)

                elif self.dlg.tabWidget.currentIndex()==1: #CSV file geocoding
                    if self.dlg.tableWidget_Tab2.rowCount()==0:
                        QtWidgets.QMessageBox.warning(self.dlg, "Warning", "Please load your CSV file.")
                        return
                    else:
                        output=prepVector.separate_gdf_by_geometry(pd.concat(list(self.dlg.processAPI_Tab2()), ignore_index=True))
                        for gdf in output:
                            layer_name = '{}_{}'.format(self.dlg.lineEdit_Output_Name.text(),gdf.geom_type.unique()[0])
                            layer = QgsVectorLayer(gdf.to_json(), layer_name, 'ogr')
                            QgsProject.instance().addMapLayer(layer)
                else:
                    raise ValueError("Invalid tab index.")
            except RuntimeError as e:
                raise e
            except ValueError as e:
                raise e
            except Exception as e:
                raise e