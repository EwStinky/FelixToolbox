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
            * key (str): The name of the key attribute in the output. If None or 'None', the column will not be created.
            * processingMode (int): Processing mode chosen by the user that decided the output type coming from the Isochrone_API_IGN.main().
            * voronoi_extend_layer (str | tuple): Selected input for the clipping of the voronoi's cells if the voronoi processing mode has been selected.
            * for the other parameters in self.params, see the request_IGN_isochrone_api function
        """
       
        self.input_layer= input_layer
        self.range_value = range_value
        self.attributKey = key
        self.processingMode = processingMode
        self.params=[resource,costType,profile,direction,constraints,geometryFormat,distanceUnit,timeUnit,crs]
        self.voronoi_extend_layer=voronoi_extend_layer
        try:
            self.output = self.main().to_json()
        except RuntimeError as e:
            raise RuntimeError("An error occurred while processing the isochrone API request: {}".format(e))

    @staticmethod
    @decorators.retryRequest(min_wait=1, wait_multiplier=2, max_retries=3)
    def request_IGN_isochrone_api(point:str , costValue:int,valueKey:str=None, resource:str='bdtopo-valhalla', costType:str="time", profile:str='car', direction:str='arrival', constraints:str=None, geometryFormat:str='geojson', distanceUnit:str='meter', timeUnit:str='minute', crs:str='EPSG:4326') -> gpd.GeoDataFrame:
        """
        The function `request_IGN_isochrone_api` prepares the body parameters for the isochrone API request from IGN service.
        It then sends a GET request to the IGN isochrone API and returns the response from the API as a geojson.

        Args:
            point (str): Coordinates of a point position: 'lon,lat'. This is the point from which calculations are made. It must be in EPSG:4326 format.
            costValue (int): Cost value used for calculation. You can, for example, specify a distance or a time, depending on the chosen optimization. 
                             The unit will also depend on the distanceUnit and timeUnit parameters.
            valueKey (str): The value of the key attribute in the output. If None or 'None', the column will not be created.
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
        
        base_dict = {'geometry': shape(call.json()['geometry']), **{k: v for k, v in call.json().items() if k != 'geometry'}}

        if valueKey is not None and valueKey != 'None':
            base_dict['valueKey'] = valueKey

        gdf = gpd.GeoDataFrame([base_dict], geometry='geometry', crs='EPSG:4326')
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
    def post_api_voronoi_processing(input_gdf:gpd.GeoDataFrame, range_value:list, point_layer:gpd.GeoDataFrame, voronoi_extend_layer:polygon.Polygon=None) -> gpd.GeoDataFrame:
        """
        Process input geodataframe by creating Voronoi polygons from points and computing differences between cost value rings.
        
        This function creates Voronoi diagrams from point locations, intersects them with input isochrones,
        filters to keep only relevant zones, and computes ring differences for each Voronoi zone.
        
        Args:
            input_gdf (gpd.GeoDataFrame): Input geodataframe containing isochrone geometries with 'costValue' and 'point' attributes
            range_value (list): List of cost values to process
            point_layer (gpd.GeoDataFrame): Points used to generate Voronoi polygons
            voronoi_extend_layer (polygon.Polygon, optional): Boundary polygon to clip Voronoi diagram. Defaults to None.
        
        Returns:
            gpd.GeoDataFrame: Processed geodataframe with ring geometries, centroids, and associated attributes
        """
        try:
            # Create Voronoi polygons
            point_layer.to_crs("EPSG:4326", inplace=True)
            voronoi_polygon = gpd.GeoDataFrame(
                geometry=[geom for geom in list(voronoi_diagram(
                    point_layer.unary_union, 
                    envelope=loads(str(voronoi_extend_layer)) if voronoi_extend_layer else None
                ).geoms)],
                crs="EPSG:4326"
            )
            voronoi_polygon['id_voronoi'] = range(len(voronoi_polygon))
            voronoi_polygon_cliped = gpd.overlay(
                voronoi_polygon, 
                gpd.GeoDataFrame(geometry=[voronoi_extend_layer], crs="EPSG:4326"), 
                how='intersection'
            ) if voronoi_extend_layer else voronoi_polygon
            
            # Intersect input geodataframe with Voronoi polygons
            input_gdf.to_crs(epsg=4326, inplace=True)
            gdf_voronoi = gpd.overlay(input_gdf, voronoi_polygon_cliped, how='intersection')
            
            def point_in_geometry(row):
                """Check if the point attribute is contained within the geometry."""
                try:
                    [x, y] = row['point'].split(',')
                    pt = Point(float(x), float(y))
                    return row['geometry'].contains(pt)
                except:
                    return False
        
            # Filter clipped isochrones with Voronoi polygons to keep only occurrences that intersect the starting point   
            gdf_voronoi = gdf_voronoi[gdf_voronoi.apply(point_in_geometry, axis=1)] 
            
            # If only one isochrone value, no need for differences
            print(len(range_value))
            if len(range_value) == 1:
                gdf = gdf_voronoi.copy()
            # Otherwise, process differences by groups of isochrones that share the same Voronoi polygon id, 
            # starting from the largest costValue down to the smallest     
            else:
                difference = []
                # Group by id_voronoi
                for voronoi_id, group in gdf_voronoi.groupby('id_voronoi'):
                    group_sorted = group.sort_values('costValue', ascending=False).reset_index(drop=True)
                    # Loop through group occurrences (from largest to smallest)
                    for idx in range(len(group_sorted)):
                        current_row = group_sorted.iloc[idx]
                        current_geom = gpd.GeoDataFrame([current_row], crs=gdf_voronoi.crs)
                        # If this is the last one (= smallest costValue)
                        if idx == len(group_sorted) - 1:
                            difference.append(current_geom)
                        else:
                            next_row = group_sorted.iloc[idx + 1]
                            next_geom = gpd.GeoDataFrame([next_row], crs=gdf_voronoi.crs)
                            result = gpd.overlay(current_geom, next_geom, how='difference')
                            difference.append(result)
                    
                gdf = pd.concat(difference, ignore_index=True)
            
            # Calculate centroid coordinates for each geometry    
            gdf[['value', 'Xcentroid', 'Ycentroid']] = gdf.apply(
                lambda row: pd.Series([
                    row['costValue'], 
                    row['geometry'].centroid.x, 
                    row['geometry'].centroid.y
                ]), 
                axis=1
            )
            
            return gdf
            
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
            count_api=0
            attribute_values = self.input_layer[self.attributKey] if self.attributKey is not None else [None] * len(self.input_layer['geometry'])
            for f, i in zip(self.input_layer['geometry'], attribute_values):
                coordinates = '{},{}'.format(f.x, f.y)
                for value in self.range_value:
                    if count_api == 5:
                        time.sleep(1)
                        count_api = 1
                    else:
                        count_api += 1
                    
                    output = self.request_IGN_isochrone_api(coordinates, value,i, *self.params)
                    output['X_input_point'], output['Y_input_point'] = coordinates.split(',')
                    list_gdf.append(output)
            if self.processingMode == 0: 
                return self.post_api_dissolve_processing(gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True)), self.range_value)
            elif self.processingMode == 1:
                return gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True))
            else:
                return self.post_api_voronoi_processing(gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True)), self.range_value, self.input_layer, self.voronoi_extend_layer)
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