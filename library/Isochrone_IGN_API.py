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
        start                : 2025-05-15
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import shape, polygon
from shapely.ops import voronoi_diagram
from shapely.wkt import loads
import time
from .utilsLibrary import decorators

class Isochrone_API_IGN:
    def __init__(self, input_layer:gpd.GeoDataFrame, range_value:list[int], processingMode:int=0, resource:str='bdtopo-valhalla', costType:str="time", profile:str='car', direction:str='arrival', constraints:str=None, geometryFormat:str='geojson', distanceUnit:str='meter', timeUnit:str='minute', crs:str='EPSG:4326', voronoi_extend_layer=None,key:str=None):
        """Initializes the Isochrone_API_IGN_V2 class the input layer and the range value.
        Every other parameters are set to their default value but can be changed, they are regrouped in a list to be used in 
        the request_IGN_isochrone_api function.

        Args:
            * input_layer (gpd.GeoDataFrame): a GeoDataFrame object representing the location of the points from which the isochrones will be calculated.
            * range_value (list[int]): a list of integers representing the time/distance values for which the isochrones will be calculated.
            * key (str): The name of the key attribute that will be used as key value in the output. If None or 'None', the column will be filled with None.
            * processingMode (int): Processing mode chosen by the user that decided the output type coming from the Isochrone_API_IGN.main().
            * voronoi_extend_layer (str | tuple): Selected input for the clipping of the voronoi's cells if the voronoi processing mode has been selected.
            * for the other parameters in self.params, see the request_IGN_isochrone_api function
        """
       
        self.input_layer= input_layer
        self.range_value = range_value
        self.attributKey = key
        self.processingMode = processingMode
        self.params={
            'resource':resource,
            'costType':costType,
            'profile':profile,
            'direction':direction,
            'constraints':constraints,
            'geometryFormat':geometryFormat,
            'distanceUnit':distanceUnit,
            'timeUnit':timeUnit,
            'crs':crs}
        self.voronoi_extend_layer=voronoi_extend_layer
        try:
            self.output = self.main().to_json()
        except RuntimeError as e:
            raise RuntimeError("An error occurred while processing the isochrone API request: {}".format(e))

    @staticmethod
    @decorators.retryRequest(min_wait=1, wait_multiplier=2, max_retries=3)
    def request_IGN_isochrone_api(point:str , costValue:int, resource:str='bdtopo-valhalla', costType:str="time", profile:str='car', direction:str='arrival', constraints:str=None, geometryFormat:str='geojson', distanceUnit:str='meter', timeUnit:str='minute', crs:str='EPSG:4326') -> gpd.GeoDataFrame:
        """
        The function `request_IGN_isochrone_api` prepares the body parameters for the isochrone API request from IGN service.
        It then sends a GET request to the IGN isochrone API and returns the response from the API as a geojson.

        Args:
            point (str): Coordinates of a point position: 'lon,lat'. This is the point from which calculations are made. It must be in EPSG:4326 format.
            costValue (int): Cost value used for calculation. You can, for example, specify a distance or a time, depending on the chosen optimization. 
                             The unit will also depend on the distanceUnit and timeUnit parameters.
            resource (str): Resource used for calculation. Possible values are: bdtopo-valhalla, bdtopo-pgr, pgr_sgl_r100_all, graph_pgr_D013. 
            costType (str): Type of cost used for calculation. The unit will also depend on the distanceUnit and timeUnit parameters. 
                            Possible values are: time, distance
            profile (str): Displacement mode used for calculation. Available values are: car, pedestrian
            direction (str): This defines the direction of travel. Possible values are: arrival, departure. 
                             Either define a starting point and obtain potential arrival points.  Or define an arrival point and obtain the potential departure points.  
            constraints (array[str]): Constraints used for calculation, this is a JSON object. The available parameters are present in the GetCapabilities.
                                      I'm not so sure but it seems that only one constraint can be used at a time, at least based on my tests.
            geometryFormat (str): Geometry format in the response. Can be in GeoJSON or Encoded Polyline format.
            distanceUnit (str): Unit of returned distances. Possible values are: meter, kilometer
            timeUnit (str): Unit of returned times. Possible values are: second, minute, hour, standard
            crs (str): Coordinate reference system used for calculation. The default value is EPSG:4326. The available parameters are present in the GetCapabilities.

        return: 
            gdf (gpd.GeoDataFrame): A GeoDataFrame representing the isochrone output from the IGN API output (json). 
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
        
        gdf = gpd.GeoDataFrame([{'geometry': shape(call.json()['geometry']), **{k: v for k, v in call.json().items() if k != 'geometry'}}], geometry='geometry', crs='EPSG:4326')
        return gdf
    
    @staticmethod
    def post_api_dissolve_processing(input_gdf:gpd.GeoDataFrame, range_value:list) -> gpd.GeoDataFrame:
        """post_api_processing runs a bunch of processing on the isochrones output from the ORS API services.
        It dissolves the isochrones per time value and then calculates the difference between each layer 
        (layer x+1 - layer x).

        Args:
            input_gdf (gpd.GeoDataFrame): GeoDataFrames containing isochrones from the API request.
            range_value: list[int]: a list of integers representing the time/distance values for which the isochrones will be calculated

        Returns:
            A GeoDataFrame representing the merged isochrones after the difference of each layers.
            Three new columns are added to the gdf to represent the value used for each isochrone, the X and Y coordinates of the centroid of the isochrone. 
        """
        dissolved_gdf=[input_gdf[input_gdf['costValue'] == y].dissolve() for y in range_value] #dissovle the layer per time value
        difference = []
        difference.append(dissolved_gdf[0])  #Append the first layer without processing
        for u in range(len(range_value) - 1): #Loop to get the difference between each layer
            output = gpd.overlay(dissolved_gdf[u + 1], dissolved_gdf[u], how='difference')
            difference.append(output)
        gdf = pd.concat(difference)
        #gdf.drop(columns=['center','area','group_index'], inplace=True)
        gdf[['value','Xcentroid','Ycentroid']] = gdf.apply(lambda row: pd.Series([row['costValue'], row['geometry'].centroid.x,row['geometry'].centroid.y]), axis=1)
        return gdf
    
    @staticmethod
    def post_api_voronoi_processing(input_gdf:gpd.GeoDataFrame, range_value:list, point_layer:gpd.GeoDataFrame, voronoi_extend_layer:polygon.Polygon=None, key_attribute:str=None) -> gpd.GeoDataFrame:
        """
        Same as post_api_dissolve_processing but it clips the output with the voronoï polygons of the input points.

        Args:
            input_gdf (gpd.GeoDataFrame): GeoDataFrames containing isochrones from the API request.
            range_value: list[int]: a list of integers representing the time/distance values for which the isochrones will be calculated
            point_layer (gpd.GeoDataFrame): GeoDataFrame representing the input point layer used to calculate the isochrones.
            voronoi_extend_layer (polygon.Polygon, optional): Polygon used to clip the voronoi's cells. If None, no clipping is applied. Defaults to None.
            key_attribute (str, optional): Name of the point_layer attribute to use as a key value in the output. If None, None values are assigned to the keyValue column.

        Returns:
            gdf_voronoi | gdf_voronoi_with_key (gpd.GeoDataFrame): A GeoDataFrame representing the merged isochrones after the difference of each layers and clipped with the voronoi's cells.
            If key_attribute is provided, the value 'keyValue' will be corresponding to the value of the attribute for the point from the isochrone has been calculated.
        """
        try:
            dissolved_gdf=[input_gdf[input_gdf['costValue'] == y].dissolve() for y in range_value] 
            difference = []
            difference.append(dissolved_gdf[0])  
            for u in range(len(range_value) - 1): 
                output = gpd.overlay(dissolved_gdf[u + 1], dissolved_gdf[u], how='difference')
                difference.append(output)
            gdf = pd.concat(difference)
            #gdf[['value','Xcentroid','Ycentroid']] = gdf.apply(lambda row: pd.Series([row['costValue'], row['geometry'].centroid.x,row['geometry'].centroid.y]), axis=1)
            gdf.to_crs(epsg=4326, inplace=True)
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
            gdf_voronoi.drop(columns=['X_input_point','Y_input_point'], inplace=True)

            if key_attribute:
                gdf2concat=[]
                gdf_voronoi['keyValue'] = None
                for index, row in point_layer.iterrows():
                    gdf_voronoi.loc[gdf_voronoi[gdf_voronoi.intersects(row['geometry'])].index, 'keyValue'] = row[key_attribute]
                for gdf2modif in [gdf_voronoi[gdf_voronoi['id_voronoi']==id_voronoi] for id_voronoi in gdf_voronoi['id_voronoi'].unique().tolist()]:
                    value2apply = gdf2modif['keyValue'].dropna().tolist()[0]
                    gdf2modif['keyValue'] = value2apply
                    gdf2concat.append(gdf2modif)
                gdf_voronoi_with_key = gpd.GeoDataFrame(pd.concat(gdf2concat, ignore_index=True))
                return gdf_voronoi_with_key
            else:
                gdf_voronoi['keyValue'] = None
                return gdf_voronoi
        except Exception as err:
            raise err

    def main(self) -> gpd.GeoDataFrame:
        """
        The function `main` is the main function of the class. It retrieves the coordinates of the points in the input layer,
        then it loops through each point and calls the `request_IGN_isochrone_api` function to get the isochrones for each point.
        It then merges all the isochrones together and creates a new GeoDataFrame representing the time/distance range unit of this time/distance value.
        the function respects the usage policy of the IGN API by waiting 1 second after every 5 requests.
        """
        try:
            list_gdf = []
            count_api=1
            for index, row in self.input_layer.iterrows():
                coordinates = '{},{}'.format(row['geometry'].x,row['geometry'].y)
                for value in self.range_value:
                    count_api+=1
                    if count_api%6==0:
                        time.sleep(1)
                    count_api=1
                    output = self.request_IGN_isochrone_api(coordinates, value, **self.params)
                    output['X_input_point'], output['Y_input_point'] = coordinates.split(',')
                    output['keyValue'] = row['{}'.format(self.attributKey)] if self.attributKey is not None else None
                    list_gdf.append(output)
            if self.processingMode == 0: 
                return self.post_api_dissolve_processing(gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True)), self.range_value)
            elif self.processingMode == 1:
                return gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True))
            else:
                return self.post_api_voronoi_processing(gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True)), self.range_value, self.input_layer, self.voronoi_extend_layer, self.attributKey)
        except Exception as err:
            raise err
