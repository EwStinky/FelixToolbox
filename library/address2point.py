"""
/***************************************************************************
    address2point.py is a script that takes an address as input (string) 
    and returns a geometry point in the form of a GeoDataFrame object.
    The GeoDataFrame contains the attributes returned by the API selected.
                             -------------------
        begin                : 2025-03-26
        email                : felix.gardot@gmail.com
        github               : https://github.com/EwStinky
 ***************************************************************************/
"""
import geopandas as gpd
import requests

class AddressSearch:
    """
    AddressSearch is a class that uses APIs from BAN or Nominatim to produce a 
    GeoDataFrame from an address string used as input

    /!\ The usage policies of the APIs are:
        - Nominatim: maximum 1 request / second 
        - BAN: maximum 50 requests / second / ip
    Please respect these specifications
    """

    def __init__(self, api:str, parameters=[]):
        try:
            if api=='BAN':
                self.result = AddressSearch.search_address_API_BAN(*parameters)
            elif api=='Nominatim':
                self.result = AddressSearch.search_address_nominatim_API(*parameters)
            else:
                raise ValueError("Invalid API choice. Choose 'BAN' or 'Nominatim'.")
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError("HTTP error occurred: {}".format(http_err))
        except requests.exceptions.ConnectionError as conn_err:
            raise RuntimeError("Connection error occurred: {}".format(conn_err))
        except requests.exceptions.Timeout as timeout_err:
            raise RuntimeError("Timeout error occurred: {}".format(timeout_err))    
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError("Request error occurred: {}".format(req_err))    
        except ValueError as err:
            raise ValueError(err) 
        except Exception as err:
            raise RuntimeError("An error occurred: {}".format(err))

    @staticmethod
    def search_address_API_BAN( q: str, limit: int = 5, autocomplete: int = 0, citycode: int = None, postcode: int = None, type_search: str =None, lat: float = None, lon: float = None) -> gpd.GeoDataFrame:
        """Search for an address located in France, using the API Adresse from data.gouv.fr
        https://adresse.data.gouv.fr/outils/api-doc/adresse

        Args:
            - q (str): a string corresponding to the adress to research .
            - limit (int, optional): Maximum number of results.
            - autocomplete (int, optional): Activate/deactivate autocomplete.
            - citycode (int, optional): City code to filter the results.
            - postcode (int, optional): Postal code to filter the results.
            - type_search (str, optional): Type of the result. Can be 'housenumber', 'street', 'locality', 'municipality'.
            - lat (float, optional): Latitude to filter the results.
            - lon (float, optional): Longitude to filter the results.

        Returns: a GeoDataFrame object containing the results of the API request. 
        """
        url='http://api-adresse.data.gouv.fr/search/'
        payload = {
            'q': q,
            'limit': limit,
            'autocomplete': autocomplete,
            'citycode': citycode,
            'postcode': postcode,
            'type:': type_search,
            'lat': lat,
            'lon': lon
        }
        call = requests.get(url, params=payload)
        call.raise_for_status()
        return gpd.GeoDataFrame.from_features(call.json()["features"]).set_crs("EPSG:4326")

    @staticmethod
    def search_address_nominatim_API(q:str ,limit:int =10, addressdetails:int =1, extratags:int =1, namedetails:int =1, dedupe:int =1, countrycodes: list =None, layer: list=None, featureType:str =None, exclude_place_ids:list =None, viewbox:str =None, bounded:int =0) -> gpd.GeoDataFrame:
        """Search for an address using the Nominatim API
        https://nominatim.org/release-docs/develop/api/Search/

        Args:
            - q (str): a string corresponding to the address to research (amenity-street-city-county-state-country-postal code)
            - limit (int, optional): Limit the maximum number of returned results. Defaults to 10.
            - addressdetails (int, optional): include a breakdown of the address into elements. Defaults to 1.
            - extratags (int, optional): include any additional information in the result that is available in the database. Defaults to 1.
            - namedetails (int, optional): include a full list of names for the result. Defaults to 1.
            - accept_language (str, optional): Preferred language order for showing search results. Defaults to 'en'.
            - countrycodes (list of str, optional): restrict results to a specific country. Defaults to None. Comma-separated list of country codes
            - layer (list of str, optional): restrict results to a specific layer. Defaults to None. Comma-separated list of: 'address', 'poi', 'railway', 'natural', 'manmade'
            - featureType (str, optional): restrict results to a specific feature type. Defaults to None. One of: 'country', 'state', 'city', 'settlement'
            - exclude_place_ids (list of str, optional): exclude results with specific place IDs. Defaults to None. Comma-separated list of place ids
            - viewbox (str, optional): restrict results to a specific bounding box. Defaults to None. <x1>,<y1>,<x2>,<y2> 
            - bounded (int, optional): when 1, turns the 'viewbox' parameter into a filter parameter, excluding any results outside the viewbox.. Defaults to 0.
            - dedupe (int, optional): remove duplicate results. Defaults to 1.

        Returns: a GeoDataFrame object containing the results of the API request. 
        """
        payload = { 
            'q': q,
            'limit': limit,
            'format': 'geojson',
            'addressdetails': addressdetails,
            'extratags': extratags,
            'namedetails': namedetails,
            'accept-language': 'en',
            'polygon_geojson': 1,
            'countrycodes':countrycodes,
            'layer':layer,
            'featureType':featureType,
            'exclude_place_ids':exclude_place_ids,
            'viewbox':viewbox,
            'bounded':bounded,
            'dedupe':dedupe
        }
        url= 'https://nominatim.openstreetmap.org/search'
        headers = {'User-Agent': 'FelixToolbox/1.0'}

        call = requests.get(url, headers=headers, params=payload)
        call.raise_for_status()
        return gpd.GeoDataFrame.from_features(call.json()["features"]).set_crs("EPSG:4326")