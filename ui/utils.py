"""
/***************************************************************************
    This module containes the class and functions usefull the UI management.
    So far it is made for Qt UIs.
                             -------------------
        begin                : 2025-02-19
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky
 ***************************************************************************/
"""
import os
import geopandas as gpd
import pandas as pd

from qgis.PyQt import uic
from qgis.core import QgsVectorLayer

class load_ui():
    """
    This class is used to load a UI file so that PyQt 
    can populate your plugin with the elements from Qt Designer
    """
    def __init__(self, file):
        self.FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), file))

class prepVector():
    """
    This class contains function that help for the preparation
    of vector layers for future processing.
    """
    @staticmethod
    def layer_to_geodataframe(layer: QgsVectorLayer) -> gpd.GeoDataFrame:
        """Transform a QgsVectorLayer to a gdp.Geodataframe
        copying its attributes and geometries.

        Args:
            layer (QgsVectorLayer): class object from qgis.core
        Returns:
            gdp.Geodataframe: a GeoDataFrame object with the same 
            attributes, geometry and crs as the input layer
        """
        try:
            return gpd.read_file(layer.source())
        except:
            features = layer.getFeatures()
            geometries = []
            attributes = []
            for feature in features:
                geometries.append(feature.geometry().asWkt())
                attributes.append(feature.attributes())
            column_names = [field.name() for field in layer.fields()]
            gdf = gpd.GeoDataFrame(attributes, columns=column_names)
            gdf['geometry'] = geometries
            gdf['geometry'] = gpd.GeoSeries.from_wkt(gdf['geometry'])
            return gdf.set_crs(layer.crs().authid())

    @staticmethod
    def separate_gdf_by_geometry(gdf) -> list:
        """separate_gdf_by_geometry separates a GeoDataFrame object
        into multiple GeoDataFrame based on the different geometries
        present in the input GeodataFrame.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame object that may 
            contain multiple type of geometry.

        Returns:
            output_list: list of gpd.GeoDataFrame objects, each containing
            a unique type of geometry.
        """
        geometry_dict = {}
        output_list = []
        for index, row in gdf.iterrows():
            if row['geometry'].geom_type not in geometry_dict:
                geometry_dict[row['geometry'].geom_type] = gpd.GeoDataFrame(columns=gdf.columns, crs=gdf.crs)
            geometry_dict[row['geometry'].geom_type] = pd.concat(
                [geometry_dict[row['geometry'].geom_type], row.to_frame().T],
                ignore_index=True
            )
        for y in range(len(geometry_dict)):
            output_list.append(geometry_dict[list(geometry_dict.keys())[y]])
        return output_list