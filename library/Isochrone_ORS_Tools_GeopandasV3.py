"""
/***************************************************************************
    Isochrone_ORS_Tools_GeopandasV3.py will produce an isochrone geojson for each point of a point layer 
    using the ORS Tools API. The isochrones will be created for each time interval declared 
    in the 'interval_minutes' variable, from the ORS API services.
    It will then merge the isochrones together and create a new geojson
    which represents the time range unit of this isochrone. 

    interval_minutes: list of time intervals in minutes
    api_ors_key: string representing the API key for the ORS Tools services
    input_coordinates: a list of a list of coordinates (X,Y) of each point needed to get an isochrone, 
                             -------------------
        start                : 2025-01-29
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import polygon
from shapely.ops import voronoi_diagram
from shapely.wkt import loads
from .utilsLibrary import decorators

class Isochrone_API_ORS:
    def __init__(self,input_layer:gpd.GeoDataFrame, api_ors_key:str, interval_minutes:list, processing_mode:int=0, smoothing:int=0, location_type:str='destination',transportation:str='driving-car', voronoi_extend_layer=None):
        """
        The function initializes an object with a selected vector layer, a list of interval minutes, and
        an API key for OpenRouteService.
        
        * input_layer (gpd.GeoDataFrame): GeoDataFrame representing a layer of points that will be used to calculate isochrones
        * interval_minutes (list[int]): A list that contains the intervals in minutes that you want to use to calculate isochrones
        * api_ors_key (str):  A string that represents the API key for the OpenRouteService (ORS) API.
        * smoothing (int): integer used for the smoothing factor in the isochrone API request (0 - 100) 
        * location_type (str): string used for the smoothing factor in the isochrone API request ('start' or 'destination')
        * processingMode (int): Processing mode chosen by the user that decided the output type coming from the Isochrone_API_IGN.main().
        * voronoi_extend_layer (str | tuple): Selected input for the clipping of the voronoi's cells if the voronoi processing mode has been selected.
        """
        self.input_layer = input_layer.to_crs(epsg=4326) if input_layer.crs!='epsg:4326' else input_layer
        self.api_ors_key = str(api_ors_key)
        self.interval_minutes = self.time_range_minutes_to_seconds(interval_minutes)
        self.processing_mode=processing_mode
        self.smoothing = smoothing
        self.location_type = location_type
        self.transportation = transportation
        self.voronoi_extend_layer = voronoi_extend_layer
        try:
            self.result = self.main().to_json()
        except Exception as err:
            raise RuntimeError(f"An error occurred while generating the result: {err}")

    @staticmethod
    @decorators.retryRequest(min_wait=1, wait_multiplier=2, max_retries=3)
    def request_ORS_isochrone_api(input_coordinates: list[list[float,float]], interval_seconds: list[int],api_ors_key: str,smoothing:int=0, location_type:str='destination', transportation:str='driving-car', ) -> dict:
        """
        The function `request_ORS_isochrone_api` prepares the body parameters for the isochrone API request from ORS Tools services.
        It then sends a POST request to the ORS Tools isochrone API and returns the response from the API as a QgsVectorLayer.
        The number of points requested cannot exceed 5 points, so the function verifies if the list of points > 5 or not.
        If it is the case, then I will request the points by dividing the list of points into sublists of 5 points.

        inputs:
        * input_coordinates: list of lists representing the coordinates X,Y (espg:4326) of each point in the layer (cannot be over 5 sublists)
        * interval_seconds: list of time intervals in seconds
        * smoothing: integer representing the smoothing factor for the isochrone (0 - 100) 
        a value closer to 100 will result in a more generalised shape.
        * location_type: string representing the location type for the isochrone API request ('start' or 'destination')

        return: 
        * call.json: variable the JSON response data from the ORS Tools isochrone API request
        """
        try:
            api_headers  = {
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                'Authorization': api_ors_key,
                'Content-Type': 'application/json; charset=utf-8'
                }

            api_body = {
                'locations':input_coordinates,
                'range':interval_seconds,
                'location_type':location_type,
                'range_type':"time",
                'attributes':["area","reachfactor"],
                'smoothing':smoothing,
            }
            call=requests.post('https://api.openrouteservice.org/v2/isochrones/{}'.format(transportation),json=api_body,headers=api_headers)
            call.raise_for_status()
            return call.json()
        except Exception as e:
            if call.status_code == 403: # Not authorized, invalid API key
                raise ValueError("Invalid API key provided.")
            else:
                raise e

    @staticmethod
    def verif_list_int(interval_minutes: list):
        """
        The function `verif_list_int` checks if all elements in the list `interval_minutes` are integers.
        Returns True if all elements in the `interval_minutes` list are of type `int`
        """
        return all(isinstance(i, int) for i in interval_minutes)

    @staticmethod
    def  verif_list_float(input_coordinates: list):
        """
        The function `verif_list_int` checks if all the lists in the list `input_coordinates` contain 2 float elements.
        Returns True if all conditons are met.
        """
        return all(
            [all(isinstance(i[0], float) for i in input_coordinates),
             all(isinstance(i[1], float) for i in input_coordinates), 
             all(len(i)==2 for i in input_coordinates)])

    @staticmethod    
    def time_range_minutes_to_seconds(interval_minutes: list) -> list:
        """
        The function `time_range_minutes_to_seconds` converts the time intervals in minutes to seconds in new self variables.

        interval_seconds: list of time intervals in seconds
        """
        return [i*60 for i in interval_minutes]

    @staticmethod
    def split_coordinates_into_sublists(list_to_split: list) -> list:
        """
        This Python function splits a list of coordinates into sublists of 5 elements each if the original
        list has more than 5 elements.

        returns:
        split= a list of the different sublists that also contains lists -> list[sublist[lists]]
        """
        return [list_to_split[i:i+5] for i in range(0,len(list_to_split),5)]

    @staticmethod
    def get_points_coordinates(gdf: gpd.GeoDataFrame, geometry_column: str) -> list:
        """
        The function `get_points_coordinates` retrieves the coordinates of the points in a gdf layer.
        and returns a list of lists representing the coordinates (X,Y) of each point in the layer.
        """
        return [[f.x,f.y] for f in gdf['{}'.format(geometry_column)]]

    @staticmethod
    def api_output_to_gdf(json) -> gpd.GeoDataFrame:
        features = json['features']
        gdf = gpd.GeoDataFrame.from_features(features)
        return gdf.set_crs(epsg=4326, inplace=True)
    
    @staticmethod
    def post_api_processing(list_gdf:list, interval_seconds:list) -> gpd.GeoDataFrame:
        """geojson2gdf runs a bunch of processing on the isochrones output from the ORS API services.
        It dissolves the isochrones per time value and then calculates the difference between each layer 
        (layer x+1 - layer x).

        Args:
            list_gdf (list): list of GeoDataFrames (gdf) representing the isochrones output (maximum 5 points) 
            from the ORS API for time intervals
            interval_minutes (list): list of the time intervals used to calculate the isochrones in seconds

        Returns:
            A GeoDataFrame representing the merged isochrones after the difference of each layers.
            The column 'value' is updated to be presented in minutes.
            The column 'center' is dropped to be replaced with 'Xcentroid' and 'Ycentroid' columns.
        """
        dissolved_gdf=[list_gdf[list_gdf['value'] == y].dissolve() for y in interval_seconds] #dissolve the layer per time value
        difference = []
        difference.append(dissolved_gdf[0])  #Append the first layer without processing
        for u in range(len(interval_seconds) - 1): #Loop to get the difference between each layer
            output = gpd.overlay(dissolved_gdf[u + 1], dissolved_gdf[u], how='difference')
            difference.append(output)
        gdf = pd.concat(difference)
        gdf.drop(columns=['center','area','group_index'], inplace=True)
        gdf[['value','Xcentroid','Ycentroid']] = gdf.apply(lambda row: pd.Series([row['value']/60, row['geometry'].centroid.x,row['geometry'].centroid.y]), axis=1)
        return gdf
    
    @staticmethod
    def post_api_voronoi_processing(list_gdf:list, interval_seconds:list, point_layer:gpd.GeoDataFrame, voronoi_extend_layer:polygon.Polygon=None) -> gpd.GeoDataFrame:
        """Same as post_api_dissolve_processing but it clips the output with the voronoï polygons of the input points."""
        try:
            dissolved_gdf=[list_gdf[list_gdf['value'] == y].dissolve() for y in interval_seconds] #dissolve the layer per time value
            difference = []
            difference.append(dissolved_gdf[0])  #Append the first layer without processing
            for u in range(len(interval_seconds) - 1): #Loop to get the difference between each layer
                output = gpd.overlay(dissolved_gdf[u + 1], dissolved_gdf[u], how='difference')
                difference.append(output)
            gdf = pd.concat(difference)
            gdf.drop(columns=['center','area','group_index'], inplace=True)
            gdf[['value','Xcentroid','Ycentroid']] = gdf.apply(lambda row: pd.Series([row['value']/60, row['geometry'].centroid.x,row['geometry'].centroid.y]), axis=1)
            gdf.to_crs(epsg=4326, inplace=True) #Need a projected CRS to work, right now I'm using web mercator for a global usage but I'm not sure which one to use!
            gdf.set_geometry('geometry', inplace=True)
            point_layer.to_crs("EPSG:4326",inplace=True)
            voronoi_polygon = gpd.GeoDataFrame(
                geometry=[geom for geom in list(voronoi_diagram(point_layer.unary_union, envelope=loads(str(voronoi_extend_layer)) if voronoi_extend_layer else None).geoms)], #union_all() if geopandas >= 1.0.0
                crs="EPSG:4326"
                )
            voronoi_polygon['id_voronoi'] = range(len(voronoi_polygon))
            voronoi_polygon_cliped=gpd.overlay(voronoi_polygon,  gpd.GeoDataFrame(geometry=[voronoi_extend_layer], crs="EPSG:4326"), how='intersection') if voronoi_extend_layer else voronoi_polygon
            gdf_voronoi = gpd.overlay(gdf, voronoi_polygon_cliped, how='intersection')
            gdf_voronoi.to_crs(4326,inplace=True)
            return gdf_voronoi
        except Exception as err:
            raise err

    def main(self) -> gpd.GeoDataFrame:
        """
        The function `main` is the main function that runs the entire isochrone creation process.
        It calls the necessary functions in the correct order to generate isochrones from a selected point layer.
        """
        outputJson=[]
        try:
            for y in self.split_coordinates_into_sublists(self.get_points_coordinates(self.input_layer,'geometry')):
                outputJson.append(self.request_ORS_isochrone_api(y,self.interval_minutes,self.api_ors_key,self.smoothing,self.location_type,self.transportation))
            if self.processing_mode==0:
                return self.post_api_processing(pd.concat([self.api_output_to_gdf(y) for y in outputJson]),self.interval_minutes)
            elif self.processing_mode==1:
                return pd.concat([self.api_output_to_gdf(y) for y in outputJson])
            else:
                return self.post_api_voronoi_processing(gpd.GeoDataFrame(pd.concat([self.api_output_to_gdf(y) for y in outputJson])),self.interval_minutes, self.input_layer,self.voronoi_extend_layer)
        except Exception as err:
            raise err
