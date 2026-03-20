"""
/***************************************************************************
    Itinerary_IGN_API.py will create an itinerary between departure points
    and arrival points by using the IGN's /itineraire API.
                             -------------------
        start                : 2026-03-17
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
import geopandas as gpd
import pandas as pd
from typing import List
import requests
from shapely.geometry import shape
from .utilsLibrary import decorators,usefullTools
from .Isochrone_IGN_API import Isochrone_API_IGN

class ItineraireIGN:
    def __init__(self, start:gpd.GeoDataFrame, processingMode:int, end:gpd.GeoDataFrame=None, primaryKey:str=None, maximalTime:int=0, orderColumn:str=None, groupByColumn:str=None, resource:str='bdtopo-osrm', intermediates:List[str]=None, profile:str='car', optimization:str='fastest', constraints:List[str]=None, geometryFormat:str='geojson', distanceUnit:str='meter', timeUnit:str='minute', crs:str='EPSG:4326', waysAttributes:List[str]=None,getSteps:str='false',getBbox:str='false') -> gpd.GeoDataFrame:
        """Init the class, see request_IGN_itineraire_api() and oneByOneItinerary() doc for the rest of the parameters.

        Args:
            processingMode (int): Integer that signifies which processing mode to use for the output. '0': calculate itineraries for every arrival from every departure points ; '1': same as 1 but the potential arrivals are filtered by a selected maximum driving time from each departure points ; '2': Only one layer is selected and the itinerary is created using each points of the layer, the order and the divinding of itineraries is selected by the user.
            start (gpd.GeoDataFrame): A GeoDataFrame containing the departure points for the itinerary.
            end (gpd.GeoDataFrame, optional): A GeoDataFrame containing the arrival points for the itinerary. Optional because if processingMode = 2 then no arrival layer is needed.
            primaryKey (str, optional): Field name of the 'start' selected layer which the values it contains will be used as primary key in the output, if None, no key is added. Defaults to None.
            maximalTime (int, optional): Maximal time in minutes chosen to reach any points from 'end' layer from each individual 'start' point. It is used to limit the amount of itineraries to create from the current 'start' point in process. When set to 0, it creates an itinerary for every 'end' points. Defaults to 0.
        """
        self.processingMode=processingMode
        self.start=start
        self.end=end
        self.primaryKey = primaryKey
        if primaryKey != None:
            self.listPrimaryKey=start[primaryKey].tolist()
        else:
            self.listPrimaryKey=None
        self.maximalTime=maximalTime
        self.orderColumn=orderColumn
        self.groupByColumn=groupByColumn
        self.params={
            'resource':resource,
            'intermediates':intermediates,
            'profile':profile,
            'optimization':optimization,
            'constraints': constraints,
            'geometryFormat':geometryFormat,
            'getSteps':getSteps,
            'getBbox':getBbox,
            'waysAttributes':waysAttributes,
            'distanceUnit':distanceUnit,
            'timeUnit':timeUnit,
            'crs':crs
        }
        try:
            self.output = self.main()
            if not self.output.empty:
                self.output=self.output.to_json()
        except RuntimeError as e:
            raise RuntimeError("An error occurred while processing the isochrone API request: {}".format(e))

    @staticmethod
    @decorators.retryRequest(min_wait=1, wait_multiplier=2, max_retries=5)
    def request_IGN_itineraire_api(start:str, end:str, resource:str='bdtopo-osrm', intermediates:List[str]=None, profile:str='car', optimization:str='fastest', constraints:List[str]=None, geometryFormat:str='geojson', distanceUnit:str='meter', timeUnit:str='minute', crs:str='EPSG:4326', waysAttributes:List[str]=None,getSteps:str='false',getBbox:str='false') -> gpd.GeoDataFrame:
        """Calculate a route by providing a starting point and a destination. 
        It use IGN's API: https://www.geoportail.gouv.fr/depot/swagger/itineraire.html#/Utilisation/routeItineraire-get

        Args:
            start (str): Coordinates of the departure point for the itinerary, needs to follow the following format: 'X,Y'. Coordinates need to be in WGS84.
            end (str): Coordinates of the arrival point for the itinerary, needs to follow the following format: 'X,Y'. Coordinates need to be in WGS84.
            resource (str, optional): Resource used for calculation. Possible values are: bdtopo-valhalla, bdtopo-pgr, bdtopo-osrm, pgr_sgl_r100_all, graph_pgr_D013. Defaults to 'bdtopo-osrm'.
            intermediates (List[str], optional): Intermediate points. They must be expressed in the default CRS of the resource. Defaults to None.
            profile (str, optional): Displacement mode used for calculation. Available values are: car, pedestrian. Defaults to 'car'.
            optimization (str, optional): Calculation method used to determine the route. Available values are: fastest, shortest. Defaults to 'fastest'.
            constraints (List[str], optional): Constraints used for calculation, this is a JSON object.. Defaults to None.
            geometryFormat (str, optional): Geometry format in the response. Can be in GeoJSON or Encoded Polyline format.. Defaults to 'geojson'.
            distanceUnit (str, optional): Unit of returned distances. Possible values are: meter, kilometer. Defaults to 'meter'.
            timeUnit (str, optional): Unit of returned times. Possible values are: second, minute, hour, standard. Defaults to 'minute'.
            crs (str, optional): Coordinate reference system used for calculation. Defaults to 'EPSG:4326'.
            waysAttributes (List[str], optional): Attributes of the sections to be displayed in the response. Defaults to None.
            getSteps (str, optional): Presence of steps in the response. Defaults to 'false'.
            getBbox (str, optional): Presence of the route's Bbox in the response.. Defaults to 'false'.

        Returns:
            gpd.GeoDataFrame: A geodata
        """
        api_headers  = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Content-Type': 'application/json; charset=utf-8'
            }
        api_body = {
            'start':start,
            'end':end,
            'resource':resource,
            'intermediates':intermediates,
            'profile':profile,
            'optimization':optimization,
            'constraints': constraints,
            'geometryFormat':geometryFormat,
            'getSteps':getSteps,
            'getBbox':getBbox,
            'waysAttributes':waysAttributes,
            'distanceUnit':distanceUnit,
            'timeUnit':timeUnit,
            'crs':crs
        }
        call=requests.get('https://data.geopf.fr/navigation/itineraire',params=api_body,headers=api_headers)
        call.raise_for_status()
        gdf = gpd.GeoDataFrame([{'geometry': shape(call.json()['geometry']), **{k: v for k, v in call.json().items() if k != 'geometry'}}], geometry='geometry', crs='EPSG:4326')
        return gdf
    
    @staticmethod
    def oneByOneItinerary(layer:gpd.GeoDataFrame, orderColumn:str, groupByColumn:str=None, itineraryApiParameters:dict={}) -> gpd.GeoDataFrame:
        """Create itineraries between points that share a common value in a selected field (groupByColumn).
        The order of the itinerary is defined by sorting the value of the selected field (orderColumn).
        The idea is to create an itinerary from one layer without having to precise the departure or arrival,
        instead of each point is used as a departure and/or as an arrival, following the order established 
        after sorting the value of orderColumn.
        If groupByColumn = None, then one unique itinerary will be created among the points.

        Args:
            layer (gpd.GeoDataFrame): A GeoDataFrame containing the points used to established itineraries from.
            orderColumn (str): Name of the column from 'layer' that will be used to sort the values and established 
                the order of use of each point within the itinerary.
            groupByColumn (str, optional): Name of the column from 'layer' that will be used to group the points 
                sharing the same values. Defaults to None.
            itineraryApiParameters (dict, optional): Dictionary containing all the optionals parameters allowed in
                ItineraireIGN.request_IGN_itineraire_api(). Defaults to an empty dict

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the itineraries, divided by group from groupByColumn's value 
                or not. Contains the orderColumn's value of the departure and arrival point for each section of the itinerary.
        """
        layer.sort_values(by='{}'.format(orderColumn),inplace=True)
        if groupByColumn is not None:
            list_gdf = [x for _, x in layer.groupby(layer[groupByColumn])]
        else:
            list_gdf = [layer]
        list_itinerary=[]
        for gdf in list_gdf:
            if gdf.crs!="EPSG:4326":
                gdf.to_crs("EPSG:4326",inplace=True)
            for itinerary in range(len(gdf)-1):
                itinerary_output=ItineraireIGN.request_IGN_itineraire_api(
                    "{},{}".format(gdf.iloc[itinerary]['geometry'].x,gdf.iloc[itinerary]['geometry'].y),
                    "{},{}".format(gdf.iloc[itinerary+1]['geometry'].x,gdf.iloc[itinerary+1]['geometry'].y),
                    **itineraryApiParameters
                    )
                itinerary_output['departure_{}'.format(orderColumn)]=gdf.iloc[itinerary][orderColumn]
                itinerary_output['arrival_{}'.format(orderColumn)]=gdf.iloc[itinerary+1][orderColumn]
                if groupByColumn is not None:
                    itinerary_output[groupByColumn]=gdf.iloc[itinerary][groupByColumn]
                list_itinerary.append(itinerary_output)
        return gpd.GeoDataFrame(pd.concat(list_itinerary, ignore_index=True))

    def main(self):
        """
        If processingMode = 0:
        Create an itinerary for each departure points (self.start) towards each arrival points (self.end).

        If processingMode = 1:
        self.maximalTime is used to filter the amount of arrival points used to create an itinerary from the current departure point.
        It generates an isochrone representing in space the surface corresponding of a driving car can reach for the time value in minutes chosen by the user.
        The arrivals points are then selected for the itinerary if they intersect the isochrone. 
        If maximalTime>0 but no arrival points are intersected, no itinerary is created and the current departure point is skipped.
        If maximalTime=0 it create an itinerary for each end point (no isochrone created, similar to processingMode = 1).
        The main goal is to limit the number of itineraries created when the number of departure/arrival is too high.
        One limit of the use of isochrones as filter is that sometimes the shape of the isochrone does not overlap one or several end points when they realistically should (isochrone having a small position error on where is located the road for example).

        If processingMode = 2: 
        Create a itineraries between points within one selected layer, following an order based on the sorting value of a selected column (self.orderColumn) of the input geodataframe.
        Several itineraries can be created if the user chose to group the differents points according to their values of a selected column. This results into several
        itineraries between the points sharing the same values of self.groupByColumn. The order is still being decided by self.orderColumn
        Returns:
            gpd.GeoDataFrame: A geodataframe containing all the itinaries of each departure point towards the ends points
        """
        if self.processingMode!=2:
            list_gdf=[]
            list_intersected_end_points=None
            start_gdf=self.start.to_crs(epsg=4326) if self.start.crs!="EPSG:4326" else self.start
            end_gdf=self.end.to_crs(epsg=4326) if self.end.crs!="EPSG:4326" else self.end
            if any([self.processingMode==0, self.maximalTime==0]):
                listCoordsEnd = usefullTools.extractPointCoordinatesGdf(self.end)
            for index,departure in enumerate(usefullTools.extractPointCoordinatesGdf(start_gdf)):
                if departure==None: #Case when the geometry is empty or not a point.
                    pass
                if all([isinstance(self.maximalTime, int),self.maximalTime!=0,self.processingMode==1]):
                    intersecred_end_points=gpd.sjoin(end_gdf,Isochrone_API_IGN.request_IGN_isochrone_api(departure,self.maximalTime),how='inner',predicate="intersects")
                    if len(intersecred_end_points.index)==0:
                        pass
                    list_intersected_end_points=usefullTools.extractPointCoordinatesGdf(intersecred_end_points)
                list_arrival=listCoordsEnd if any([self.processingMode==0, self.maximalTime==0]) else list_intersected_end_points
                for arrival in list_arrival:
                    gdf_itineraire = self.request_IGN_itineraire_api(departure,arrival, **self.params)
                    if self.primaryKey!=None:
                        gdf_itineraire['{}'.format(self.primaryKey)] = self.listPrimaryKey[index]
                    list_gdf.append(gdf_itineraire)
            if len(list_gdf)==0:
                return gpd.GeoDataFrame()
            return gpd.GeoDataFrame(pd.concat(list_gdf, ignore_index=True))
        else:
            return ItineraireIGN.oneByOneItinerary(self.start, self.orderColumn, self.groupByColumn, self.params)