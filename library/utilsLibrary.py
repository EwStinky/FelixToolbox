import time
import functools
import requests
import geopandas as gpd
from shapely.geometry import LineString
from requests.exceptions import RequestException

class decorators:
  @staticmethod
  def retryRequest(min_wait:float=1.0,wait_multiplier:float=2.0,max_retries:int=3,exceptions=(RequestException)): #Can also add personalised exceptions or others
      """
      Decorator made to retry a request after an amount of time decided by the
      user if the function using the decorator raises a requests exception.
  
      Args:
          min_wait (float): Minimum wait time in seconds between retries.
          wait_multiplier (float): Multiplier for wait time on each retry.
          max_retries (int): Maximum number of retries before giving up.
          exceptions (tuple): Exceptions to catch and retry on. 
          
      """
      def decorator(func):
          @functools.wraps(func)
          def wrapper(*args, **kwargs):
              wait_time = min_wait
              last_exception = None
              for attempt in range(max_retries + 1):
                  try:
                      return func(*args, **kwargs)
                  except exceptions as e:
                      last_exception = e
                      if attempt < max_retries:
                          time.sleep(wait_time)
                          wait_time *= wait_multiplier
                      else:
                          raise
          return wrapper
      return decorator

class requestOtherApi:
    """Other functions to requests some API potentially needed for some tools"""
    @staticmethod
    @decorators.retryRequest(min_wait=4,wait_multiplier=2,max_retries=5,exceptions=(RequestException))
    def get_osm_road_within_bbox(xmin:float, ymin:float, xmax:float, ymax:float)-> gpd.GeoDataFrame: 
        """ Function to retrieve roads network (highways) from OpenStreetMap using the Overpass API.
        It keeps only the roads that are located within the bouding box defined by the user.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing the roads within the bounding box.
        """
        query = f"""[out:json][timeout:25]; (way["highway"]({ymin},{xmin},{ymax},{xmax});); out body;>;out skel qt;"""
        
        url = "http://overpass-api.de/api/interpreter"
        
        try:
            call = requests.post(url, data=query)
            call.raise_for_status()
            data = call.json()

            nodes = {} #Dict that stores the coordinates of each node based on their ID
            ways = [] #list that stores the ways (streets) found in the query containing their nodes's ID and tags
            for el in data["elements"]:
                if el["type"] == "node":
                    nodes[el["id"]] = (el["lon"], el["lat"])
                elif el["type"] == "way":
                    ways.append(el)
            rows = []
            for way in ways:
                coords = [nodes[node_id] for node_id in way["nodes"] if node_id in nodes]
                if len(coords) >= 2:
                    geometry = LineString(coords)
                    props = way.get("tags", {})
                    props["osm_id"] = way["id"]
                    props["geometry"] = geometry
                    rows.append(props)
            return gpd.GeoDataFrame(rows, crs="EPSG:4326")
        except requests.exceptions.HTTPError as e:
            raise e
    
    @staticmethod
    @decorators.retryRequest(min_wait=1,wait_multiplier=2,max_retries=5,exceptions=(RequestException))
    def get_request_api_carto_commune(lon=None, lat=None, geom=None, _limit=None, _start=None) -> requests.Response:
        """
        Send a GET request to the IGN API Carto to retrieve administrative commune boundaries.

        Args:
            lon (float, optional): Longitude coordinate.
            lat (float, optional): Latitude coordinate.
            geom (str, optional): GeoJSON geometry as a string.
            _limit (int, optional): Limit the number of results.
            _start (int, optional): Start index for pagination.

        Returns:
            requests.Response: The response object from the API call.
        """
        url = "https://apicarto.ign.fr/api/limites-administratives/commune"
        body = {
            "lon": lon,
            "lat": lat,
            "geom": geom,
            "_limit": _limit,
            "_start": _start,
        }
        try:
            call = requests.get(url, params=body)
            call.raise_for_status()
            return call
        except Exception as e:
            raise e
        
class usefullTools:
    """Usefull tools to use in the library scripts"""
    def compare_versions(v1:str, v2:str) -> int:
        """Compare two package_name.__version__ , and return 1 if v1 > v2, -1 if v1 < v2, and 0 if they are equal."""
        v1_parts = list(map(int, v1.split('.')))
        v2_parts = list(map(int, v2.split('.')))
        max_length = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_length - len(v1_parts))
        v2_parts += [0] * (max_length - len(v2_parts))
        for a, b in zip(v1_parts, v2_parts):
            if a > b:
                return 1
            elif a < b:
                return -1
        return 0





