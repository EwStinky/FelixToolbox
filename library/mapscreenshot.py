"""
/***************************************************************************
    mapscreenshot.py - FelixToolBox QGIS plugins - map screenshot tool
                             -------------------
        begin                : 05/03/2025
        email                : felix.gardot@gmail.com
	    copyright            : (c) 2025 by Félix GARDOT
        github               : https://!github.com/EwStinky
 ***************************************************************************/
"""
from PyQt5.QtWidgets import QMessageBox, QLineEdit, QInputDialog, QDialog
from PyQt5.QtGui import QColor,QFont
from PyQt5.QtCore import QDate
from qgis.core import QgsProject,QgsApplication,QgsLegendStyle,QgsLayoutItemShape,QgsLayoutMeasurement,QgsPrintLayout,QgsLayoutItemPicture,QgsLayoutItemMap,QgsMapSettings,QgsLayoutItemLegend,QgsLayoutItemScaleBar,QgsLayoutItemLabel,QgsLayoutExporter,QgsRectangle,QgsUnitTypes,QgsLayoutPoint,QgsLayoutSize,QgsLayerTree,QgsProcessingUtils,QgsLayoutNorthArrowHandler
from qgis.utils import iface

class mapscreenshot():
    @staticmethod
    def get_text_values(initial_texts, parent=None, title="", label=""):
        """get_text_values is a function that creates a dialog box with
        QlineEdit widgets for each string in the initial_texts lists.
        it returns a list of the text entered in each QLineEdit add by the user.

        Args:
            initial_texts (str): list of strings to be displayed in the QLineEdits.
            parent (optional): Defaults to None.
            title (str, optional): title of the dialog box. Defaults to "".
            label (str, optional): label of the dialog box. Defaults to "".

        Returns:
            _type_: list of strings containing the text entered by the user
            in each QlineEdit widgets.
        """
        dialog = QInputDialog()
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.show() 
        dialog.findChild(QLineEdit).hide()
        editors = []
        for i, text in enumerate(initial_texts, start=1): #generate and add a QLineEdit for each text in the list
            editor = QLineEdit(text=text)
            dialog.layout().insertWidget(i, editor)
            editors.append(editor)

        ret = dialog.exec_()
        if ret == QDialog.Accepted:
            return ret, [editor.text() for editor in editors]
        else:
            return ret, None


    def run():
        try:
            verif, input_name=mapscreenshot.get_text_values(
                ["Title of the map", "Source",], 
                title="Title & source of the map", 
                label ="Please enter the title and the source of the map                        "
                )
            
            if verif == QDialog.Accepted:
                project = QgsProject.instance()
                manager = project.layoutManager()
                layoutName = 'layout_mapscreenshot'
                layouts_list = manager.printLayouts()
                # remove any duplicate layouts
                for layout in layouts_list:
                    if layout.name() == layoutName:
                        manager.removeLayout(layout)
                layout = QgsPrintLayout(project)
                layout.initializeDefaults()
                layout.setName(layoutName)
                manager.addLayout(layout)

                # Create a shape (rectangle) for the border
                border = QgsLayoutItemShape(layout)
                border.setShapeType(QgsLayoutItemShape.Rectangle)
                border.setFrameEnabled(True)
                border.setFrameStrokeWidth(QgsLayoutMeasurement(1, QgsUnitTypes.LayoutMillimeters))
                border.setFrameStrokeColor(QColor(150, 150, 150))
                border.attemptResize(QgsLayoutSize(layout.pageCollection().pages()[0].pageSize().width()-4, layout.pageCollection().pages()[0].pageSize().height()-4, QgsUnitTypes.LayoutMillimeters))
                border.attemptMove(QgsLayoutPoint(2, 2, QgsUnitTypes.LayoutMillimeters))
                layout.addLayoutItem(border)

                # create map item in the layout
                map = QgsLayoutItemMap(layout)
                map.setRect(20, 20, 20, 20)

                # set the map extent
                ms = QgsMapSettings()
                list_layer = [layer for layer in QgsProject.instance().mapLayers().values() if project.layerTreeRoot().findLayer(layer.id()).isVisible()]
                ms.setLayers(list_layer)
                rect = QgsRectangle(iface.mapCanvas().extent()) #prend l'étendue spatiale de la map instance
                rect.scale(1.0)
                ms.setExtent(rect)
                map.setExtent(rect)
                map.setBackgroundColor(QColor(255, 255, 255, 0))
                layout.addLayoutItem(map)
                map.attemptMove(QgsLayoutPoint(5, 20, QgsUnitTypes.LayoutMillimeters))
                map.attemptResize(QgsLayoutSize(220, 178, QgsUnitTypes.LayoutMillimeters))

                #legend
                legend = QgsLayoutItemLegend(layout)
                legend.setTitle("") #add your legend title here
                layerTree = QgsLayerTree()
                for layer in list_layer:
                    layerTree.addLayer(layer)
                legend.model().setRootGroup(layerTree)
                legend.setStyleFont(QgsLegendStyle.Title, QFont("Arial", 12))
                legend.setStyleFont(QgsLegendStyle.Subgroup, QFont("Arial", 11))
                legend.setStyleFont(QgsLegendStyle.SymbolLabel, QFont("Arial", 10))
                layout.addLayoutItem(legend)
                legend.attemptMove(QgsLayoutPoint(225, 15, QgsUnitTypes.LayoutMillimeters))

                #scalebar
                scalebar = QgsLayoutItemScaleBar(layout)
                scalebar.setLinkedMap(map)
                scalebar.setStyle('Line Ticks Up')
                scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
                scalebar.setNumberOfSegments(5)
                scalebar.setNumberOfSegmentsLeft(0)
                scalebar.setUnitsPerSegment(1)
                scalebar.setLabelBarSpace(2)
                scalebar.setUnitLabel('km')
                scalebar.setFont(QFont('Arial', 7))
                scalebar.update()
                layout.addLayoutItem(scalebar)
                scalebar.attemptMove(QgsLayoutPoint(5, 198, QgsUnitTypes.LayoutMillimeters))

                # North Arrow
                north = QgsLayoutItemPicture(layout)
                north.setPicturePath(QgsApplication.svgPaths()[0] + "/arrows/NorthArrow_04.svg")
                layout.addLayoutItem(north)
                north.attemptResize(QgsLayoutSize(10, 10, QgsUnitTypes.LayoutMillimeters))
                north.attemptMove(QgsLayoutPoint(10, 24, QgsUnitTypes.LayoutMillimeters))
 
                #title
                title = QgsLayoutItemLabel(layout)
                title.setText("{}".format(str(input_name[0])))
                title.setFont(QFont('Arial', 25))
                title.adjustSizeToText()
                title.setFont(QFont('Arial', 24))
                layout.addLayoutItem(title)
                title.attemptMove(QgsLayoutPoint(10, 5, QgsUnitTypes.LayoutMillimeters))

                # Create and set the source label with name and date
                source_label = QgsLayoutItemLabel(layout)
                source_label.setText("{} - {}".format(input_name[1],QDate.currentDate().toString('dd/MM/yyyy')))
                source_label.setFont(QFont("Arial", 11))
                source_label.adjustSizeToText()
                source_label.setFont(QFont("Arial", 10))
                layout.addLayoutItem(source_label)
                source_label.attemptMove(QgsLayoutPoint(10, 15, QgsUnitTypes.LayoutMillimeters))

                layout = manager.layoutByName(layoutName)
    
                # Export the layout to a PDF file
                pdf_path=QgsProcessingUtils.generateTempFilename('Map_Screenshot_Output.pdf')
                pdf_exporter = QgsLayoutExporter(layout)
                pdf_exporter.exportToPdf(pdf_path, QgsLayoutExporter.PdfExportSettings())
                QMessageBox.information(None, 'Path of the output file: ', '{}'.format(pdf_path))

                #remove the Layout of the project
                manager.removeLayout(layout)
            else:
                raise Exception('Error: operation canceled')
        except Exception as e:
            QMessageBox.critical(None, 'Error', 'An error occured : {}'.format(str(e)))
