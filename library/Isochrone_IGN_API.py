"""
/***************************************************************************
    Isochrone_IGN_API.py will produces an isochrone geojson for each points of a point layer 
    using the IGN API. One isochrone will be created for each value declared 
    in the 'range_value' variable.
    It will then merge the isochrones together and create a new geojson
    which represents the time/distance range unit of this time/distance value. 

    inteval_minutes: list of time intervals in minutes
    api_ors_key: string representing the API key for the ORS Tools services
    input_coordinates: a list of a list of coordinates (X,Y) of each point need to get an isochrone, 
                             -------------------
        begin                : 2025-05-15
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky
 ***************************************************************************/
"""
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import shape
import time

class Isochrone_API_IGN:
    def __init__(self, input_layer, range_value:list[int], resource='bdtopo-valhalla', costType="time", profile='car', direction='arrival', constraints=None, geometryFormat='geojson', distanceUnit='meter', timeUnit='minute', crs='EPSG:4326'):
        """Initializes the Isochrone_API_IGN_V2 class the input layer and the range value.
        Every other parameters are set to their default value but can be changed, they are regrouped in a list to be used in 
        the request_IGN_isochrone_api function.

        Args:
            input_layer: GeoDataFrame: a GeoDataFrame object representing the location of the points from which the isochrones will be calculated
            range_value: list[int]: a list of integers representing the time/distance values for which the isochrones will be calculated
            for the other parameters, see the request_IGN_isochrone_api function
        """
        self.input_layer= input_layer
        self.range_value = range_value
        self.params=[resource,costType,profile,direction,constraints,geometryFormat,distanceUnit,timeUnit,crs]
        try:
            self.output = self.main().to_json()
        except RuntimeError as e:
            raise RuntimeError("An error occurred while processing the isochrone API request: {}".format(e))

    @staticmethod
    def get_points_coordinates(gdf,geometry_column: str):
        """
        The function `get_points_coordinates` retrieves the coordinates of the points in a gdf layer.
        and returns a list of string representing the coordinates (X,Y) of each point in the layer.
        """
        return ['{},{}'.format(f.x,f.y) for f in gdf['{}'.format(geometry_column)]]

    @staticmethod
    def request_IGN_isochrone_api(point:str , costValue:int, resource='bdtopo-valhalla', costType="time", profile='car', direction='arrival', constraints=None, geometryFormat='geojson', distanceUnit='meter', timeUnit='minute', crs='EPSG:4326') -> dict:
        """
        The function `request_IGN_isochrone_api` prepares the body parameters for the isochrone API request from IGN service.
        It then sends a GET request to the IGN isochrone API and returns the response from the API as a geojson.

        inputs:
        * point: str: Coordinates of a point position. This is the point from which calculations are made. It must be in EPSG:4326 format.
        * costValue: int: Cost value used for calculation. You can, for example, specify a distance or a time, depending on the chosen optimization. 
        The unit will also depend on the distanceUnit and timeUnit parameters.
        * resource: str: Resource used for calculation. Possible values are: bdtopo-valhalla, bdtopo-pgr, pgr_sgl_r100_all, graph_pgr_D013. 
        * costType: str: Type of cost used for calculation. The unit will also depend on the distanceUnit and timeUnit parameters. 
        Possible values are: time, distance
        * profile: str: Displacement mode used for calculation. Available values are: car, pedestrian
        * direction: str: This defines the direction of travel. Possible values are: arrival, departure. 
        Either define a starting point and obtain potential arrival points.  Or define an arrival point and obtain the potential departure points.  
        * constraints: array[str]: Constraints used for calculation, this is a JSON object. The available parameters are present in the GetCapabilities.
        I'm not so sure but it seems that only one constraint can be used at a time, at least based on my tests.
        * geometryFormat: str: Geometry format in the response. Can be in GeoJSON or Encoded Polyline format.
        * distanceUnit: str: Unit of returned distances. Possible values are: meter, kilometer
        * timeUnit: str: Unit of returned times. Possible values are: second, minute, hour, standard
        * crs: str: Coordinate reference system used for calculation. The default value is EPSG:4326. The available parameters are present in the GetCapabilities.

        return: 
        * gdf: GeoDataFrame: A GeoDataFrame representing the isochrone output from the IGN API output (json). 
        """
        api_headers  = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Content-Type': 'application/json; charset=utf-8'
            }

        api_body = {
            'point':point,
            'resource':resource,
            'costValue':costValue,
            'costType':costType,
            'profile':profile,
            'direction':direction,
            'constraints': constraints,
            'geometryFormat':geometryFormat,
            'distanceUnit':distanceUnit,
            'timeUnit':timeUnit,
            'crs':crs
        }
        call=requests.get('https://data.geopf.fr/navigation/isochrone',params=api_body,headers=api_headers)
        call.raise_for_status()
        
        gdf = gpd.GeoDataFrame(
            [{'geometry': shape(call.json()['geometry']), **{k: v for k, v in call.json().items() if k != 'geometry'}}],
            geometry='geometry',
            crs='EPSG:4326'
        )
        return gdf
    
    @staticmethod
    def post_api_processing(list_gdf:list, range_value:list):
        """post_api_processing runs a bunch of processing on the isochrones output from the ORS API services.
        It dissolves the isochrones per time value and then calculates the difference between each layer 
        (layer x+1 - layer x).

        Args:
            list_gdf (list): list of GeoDataFrames (gdf) representing the isochrones output (maximum 5 points) 
            from the IGN API for time/distance intervals
            range_value: list[int]: a list of integers representing the time/distance values for which the isochrones will be calculated

        Returns:
            A GeoDataFrame representing the merged isochrones after the difference of each layers.
            Three new columns are added to the gdf to represent the value used for each isochrone, the X and Y coordinates of the centroid of the isochrone. 
        """
        dissolved_gdf=[list_gdf[list_gdf['costValue'] == y].dissolve() for y in range_value] #dissovle the layer per time value
        difference = []
        difference.append(dissolved_gdf[0])  #Append the first layer without processing
        for u in range(len(range_value) - 1): #Loop to get the difference between each layer
            output = gpd.overlay(dissolved_gdf[u + 1], dissolved_gdf[u], how='difference')
            difference.append(output)
        gdf = pd.concat(difference)
        #gdf.drop(columns=['center','area','group_index'], inplace=True)
        gdf[['value','Xcentroid','Ycentroid']] = gdf.apply(lambda row: pd.Series([row['costValue'], row['geometry'].centroid.x,row['geometry'].centroid.y]), axis=1)
        return gdf
    
    def main(self):
        """
        The function `main` is the main function of the class. It retrieves the coordinates of the points in the input layer,
        then it loops through each point and calls the `request_IGN_isochrone_api` function to get the isochrones for each point.
        It then merges all the isochrones together and creates a new GeoDataFrame representing the time/distance range unit of this time/distance value.
        the function respects the usage policy of the IGN API by waiting 1 second after every 5 requests.
        """
        try:
            list_coordinates = self.get_points_coordinates(self.input_layer, 'geometry')
            list_gdf = []
            count_api=0
            for coordinates in list_coordinates:
                for value in self.range_value:
                    if count_api == 5:
                        time.sleep(1)
                        count_api=1
                        list_gdf.append(self.request_IGN_isochrone_api(coordinates, value, *self.params))
                    else:
                        count_api+=1
                        list_gdf.append(self.request_IGN_isochrone_api(coordinates, value, *self.params))        
            return self.post_api_processing(gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True)), self.range_value)
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError("HTTP error occurred: {}".format(http_err))
        except requests.exceptions.ConnectionError as conn_err:
            raise RuntimeError("Connection error occurred: {}".format(conn_err))
        except requests.exceptions.Timeout as timeout_err:
            raise RuntimeError("Timeout error occurred: {}".format(timeout_err))    
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError("Request error occurred: {}".format(req_err))    
        except ValueError as json_err:
            raise ValueError("JSON error occurred: {}".format(json_err)) 
        except Exception as err:
            raise RuntimeError("An error occurred: {}".format(err)) 

if __name__ == "__main__":
    #example usage for QGIS

    from qgis.PyQt import uic
    from qgis.core import QgsVectorLayer
    from PyQt5.QtWidgets import QInputDialog
    from qgis.core import QgsProject

    def layerSelectQGIS():
        """
        The function `layerSelectQGIS` allows the user to select a layer from the current QGIS project.
        
        :return: returns the selected layer from the QGIS project based on user input. -> QgsVectorLayer
        """
        layer,test=QInputDialog.getItem(None,'Select your layer','Layer selected:',[layer.name() for layer in QgsProject.instance().mapLayers().values()],0)
        return QgsProject.instance().mapLayersByName(layer)[0]

    def layer_to_geodataframe(layer: QgsVectorLayer) -> gpd.GeoDataFrame:
        """Transform a QgsVectorLayer to a gdp.Geodataframe
        copying its attributes and geometries.

        Args:
            layer (QgsVectorLayer): class object from qgis.core
        Returns:
            gdp.Geodataframe: a GeoDataFrame object with the same 
            attributes, geometry and crs as the input layer
        """
        if layer.isValid() and layer.dataProvider().name() == 'ogr':
            return gpd.read_file(layer.source())
        else:
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
        
    layer=layerSelectQGIS()
    gdf=layer_to_geodataframe(layer)
    gdf.to_crs('EPSG:4326', inplace=True)
    isochrone = Isochrone_API_IGN(gdf, [10], profile='pedestrian', resource ='bdtopo-pgr',constraints=['{"constraintType":"banned","key":"wayType","operator":"=","value":"autoroute"}']).output
    QgsProject.instance().addMapLayer(QgsVectorLayer(isochrone, "Isochrone_test", "ogr"))