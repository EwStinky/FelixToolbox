"""
/***************************************************************************
        Methods to interact with the SIRENE API, which provides 
        information about French businesses and establishments.
        The main idea here is to use it to select specific businesses
        located within a specific area chosen by th user.
                             -------------------
        start                : 2025-06-03
        email                : gardot.felix@gmail.com
        github               : https://github.com/EwStinky/FelixToolbox
 ***************************************************************************/
"""
import requests
import json
import pandas as pd
import geopandas as gpd
from requests.exceptions import RequestException
from shapely.geometry import mapping, box
from .utilsLibrary import decorators, requestOtherApi
from .address2point import AddressSearch

class apiSireneRequest:
    """Class to interact with the SIRENE API for retrieving information about French businesses and establishments."""
    def __init__(self,api_key,q=None,date=None,champs=None,masquerValeursNulles='false',facette=None,tri=None,nombre=20,debut=0,curseur='*'):
        """see get_request_api_SIRENE() for more details on the parameters."""
        self.api_key = api_key
        self.parameters = {
            "q": q,
            "date": date,
            "champs": champs,
            "masquerValeursNulles": masquerValeursNulles,
            "facette": facette,
            "tri": tri,
            "nombre": nombre,
            "debut": debut,
            "curseur": curseur
            }

    @decorators.retryRequest(min_wait=4,wait_multiplier=2,max_retries=5,exceptions=(RequestException))
    def get_request_api_SIRENE(self) -> requests.Response:
        """get_document_info will return the output of the request to the SIREN API based on the parameters provided.
        check the documentation for more details on the parameters: https://www.sirene.fr/static-resources/documentation/sommaire_311.html
        Usage policy: 30 requests per minute.

        Args:
            api_key (str): API key for authentication.
            q (str): Contents of multi-criteria query, see documentation for details.
            date (str, optional): Date at which historical data values are to be obtained. Defaults to None.
            champs (str, optional): Comma-separated list of requested fields. Defaults to None.
            masquerValeursNulles (str, optional): Hide (true) or show (false) attributes that have no value. Defaults to 'false'.
            facette (str, optional): Comma-separated list of fields to be counted. Defaults to None.
            tri (str, optional): Fields to be sorted, separated by commas. Defaults to None.
            nombre (int, optional): Number of items requested in answer. Defaults to 20.
            debut (int, optional): Rank of the first element requested in the response. Defaults to 0.
            curseur (str, optional): Parameter used for deep pagination. Defaults to '*'.

        Raises:
            e: HTTPError from the requests library if the request fails. Does not raise if a 404 error occurs (returned if no result found).

        Returns:
            requests.Response object: The response from the API containing the requested data.
        """
        url = "https://api.insee.fr/api-sirene/3.11/siret"
        
        headers = {
            "accept": "application/json;charset=utf-8;qs=1",
            "X-INSEE-Api-Key-Integration": self.api_key
        }
        try:
            call = requests.get(url, params=self.parameters,headers=headers)
            call.raise_for_status()
            return call
        except requests.exceptions.HTTPError as e:
            if call.status_code == 404: # Not Found, no result found
                return None
            else:
                raise e
      
    def get_request_with_cursor(self) -> pd.DataFrame:
        """Execute a request API with a cursor based on the parameters set up by the user.
        the request is executed until every results are gathered from the API.

        Args:
            self.parameters (dict): dictionary containing all the parameters needed for get_request_api_SIRENE()

        Returns:
            pd.DataFrame: pd.DataFrame containing all the siret corresponding to the conditions used for the request.
        """
        try:
            df = pd.DataFrame(columns=self.parameters['champs'].split(','))
            if self.parameters['curseur'] != '*':
                self.parameters['curseur'] = '*'
            output = self.get_request_api_SIRENE()
            if output is None:
                pass
            else:
                if output.json()['header']['total'] > self.parameters['nombre']:
                    while self.parameters['curseur'] != output.json()['header']['curseurSuivant']:
                        for value in [dict for dict in output.json()['etablissements']]:
                            df = pd.concat([df,pd.DataFrame({k:[v] for k,v in apiSireneUtils.find_values_in_json(value,df).items()})], ignore_index=True)
                        self.parameters['curseur'] = output.json()['header']['curseurSuivant']
                        output = self.get_request_api_SIRENE()
                else:
                    for value in [dict for dict in output.json()['etablissements']]:
                        df = pd.concat([df,pd.DataFrame({k:[v] for k,v in apiSireneUtils.find_values_in_json(value,df).items()})], ignore_index=True)
            return df
        except Exception as e:
            raise e

class apiSireneUtils:
    """Usefull functions prepare or manage input and output of API requests"""
    @staticmethod
    def find_values_in_json(input_json:dict, df, result=None) -> dict:
        """ Function to find values in a JSON structure and match them with DataFrame columns.

        Args:
            input_json (dict): json object to search in
            df (pd.DataFrame()): Dataframe containing the columns to match
            result (None, optional): dict used to store the values that are matching. Defaults to None.

        Returns:
            dict: output dictionnary containing the values of the json matching the df's columns
        """
        if result is None:
            result = {}
        dict_keys = df.columns.to_series().to_dict()
        if isinstance(input_json, dict):
            for key, value in input_json.items():
                if key in dict_keys and key not in result:
                    result[key] = value
                apiSireneUtils.find_values_in_json(value, df, result)
        elif isinstance(input_json, list):
            for item in input_json:
                apiSireneUtils.find_values_in_json(item, df, result)
        return result
    
    @staticmethod
    def addFilterActivity(q,activity:list[str]) -> str:
        """Add a filter to the SIRENE API request based on the NAF code of the siret
        It assume for now that 'etatAdministratifEtablissement:A' is already in the request q, meaning that 'period(' is there too!
        Do not add '*' after your NAF code it is automatically added.
        
        Args:
            q (str): string of the request that will be sent to the SIRENE API
            activity (list): list of the codes NAF to add as filter to the API request
        """
        if len(activity)>1:
            for index,value in enumerate(activity):
                if index==0:
                    q=q[:q.find("periode(")+8]+'activitePrincipaleEtablissement:{}*) AND '.format(value)+q[q.find("periode(")+8:]
                elif index+1==len(activity):
                    q=q[:q.find("periode(")+8]+'(activitePrincipaleEtablissement:{}* OR '.format(value)+q[q.find("periode(")+8:]
                else:
                    q=q[:q.find("periode(")+8]+'activitePrincipaleEtablissement:{}* OR '.format(value)+q[q.find("periode(")+8:]
            return q
        else:
            return q[:q.find("periode(")+8]+'activitePrincipaleEtablissement:{}* AND '.format(*activity)+q[q.find("periode(")+8:]
    
    @staticmethod    
    def gdf_bbox_to_geojson(gdf:gpd.GeoDataFrame) -> dict:
        """Convert a GeoDataFrame to a GeoJSON representation of its bounding box."""
        bbox=gpd.GeoDataFrame(crs=gdf.crs, geometry=[gdf.unary_union]).geometry.bounds #.union_all() if geopandas version >= 1.0.0, it's not the case yet for my OSGeo
        return json.dumps(mapping(gpd.GeoDataFrame(crs=gdf.crs, geometry=[box(bbox.minx[0], bbox.miny[0], bbox.maxx[0], bbox.maxy[0])]).geometry[0]))

    @staticmethod
    def gdf_convex_hull_to_geojson(gdf:gpd.GeoDataFrame) -> dict:
        """Convert a GeoDataFrame to a GeoJSON representation of its convex hull."""
        return json.dumps(mapping(gpd.GeoDataFrame(crs=gdf.crs, geometry=[gpd.GeoDataFrame(crs="EPSG:4326", geometry=[gdf.unary_union]).convex_hull[0]]).geometry[0]))

    @staticmethod
    def replace_latin_unique_chars(text):
        """Replace some unique latin accented characters with their English equivalents."""
        latin_to_english = {
            'à': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o', 'œ': 'oe',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c',
            'À': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Î': 'I', 'Ï': 'I',
            'Ô': 'O', 'Ö': 'O', 'Œ': 'OE',
            'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C'
        }
        return text.translate(str.maketrans(latin_to_english))

    @staticmethod
    def mergeRequestTypeOutput(output_coordinates:gpd.GeoDataFrame,output_address:gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Merge the two gdf from establishments_SIRENE_in_polygon_coordinates()
        and establishments_SIRENE_in_polygon_adress() into a single gdf without any duplicate"""
        output_coordinates['source']='selection_by_coordinates'
        output_address['source']='selection_by_address'
        output_selection_by_coordinates_WGS84=output_coordinates.set_geometry('geometry').to_crs(crs=4326)
        output_selection_by_address_WGS84=output_address.set_geometry('geometry').to_crs(crs=4326)
        merge_gdf=pd.concat([output_selection_by_coordinates_WGS84, output_selection_by_address_WGS84], ignore_index=True)
        merge_gdf_no_duplicate = merge_gdf.drop_duplicates(['siret','siren'])
        return merge_gdf_no_duplicate

class siretInPolygonFilteredByCoordinates(apiSireneRequest):
    """Selection from coordinates of the siret located within the polygons uses as gdf.
    It faster than the selection by address but less accurate because not every siret has coordinates"""
    def __init__(self,polygon:gpd.GeoDataFrame,params:dict,activity:list[str]=[]):
        super().__init__(**params)
        self.gdf=polygon
        self.activity=activity

    def etablissements_SIRENE_in_bbox(self,xmin=0,ymin=0,xmax=0,ymax=0) -> pd.DataFrame:
        """ Function to retrieve establishments in a bounding box from the SIRENE API.
        Only establishments with administrative status 'A' (active) are returned.

        Args:
            self.parameters (dict): Parameters for the API request. See get_request_api_SIRENE().
            self.activity (list): NAF code list added to activitePrincipaleEtablissement as a condition to the API request.
            xmin (int, optional): minimum x-coordinate of the bounding box. Defaults to 0. EPSG:2154.
            ymin (int, optional): minimum y-coordinate of the bounding box. Defaults to 0. EPSG:2154.
            xmax (int, optional): maximum x-coordinate of the bounding box. Defaults to 0. EPSG:2154.
            ymax (int, optional): maximum y-coordinate of the bounding box. Defaults to 0. EPSG:2154.

        Returns:
            pd.DataFrame: DataFrame containing the establishments within the bounding box.
        """
        self.parameters['q'] = 'coordonneeLambertAbscisseEtablissement:[{} TO {}] AND coordonneeLambertOrdonneeEtablissement:[{} TO {}] AND periode(etatAdministratifEtablissement:A)'.format(xmin,xmax,ymin,ymax)
        if len(self.activity)>0:
            self.parameters['q']=apiSireneUtils.addFilterActivity(self.parameters['q'],self.activity)
        try:
            df_output=self.get_request_with_cursor()
            return df_output
        except Exception as e:
            raise f"Failed to retrieve data for {xmin},{ymin},{xmax},{ymax} : {e}"
        
    
    def establishments_SIRENE_in_polygon_coordinates(self) -> pd.DataFrame:
        """ Function to retrieve establishments within the polygon defined by the GeoDataFrame's geometry.
        Uses the bounding box of the polygon to query the SIRENE API for establishments, and check if
        the establishments' coordinates intersect with the polygon's geometry.

        Returns:
            output: pd.DataFrame: DataFrame containing the establishments within the polygon used as input.
        """
        self.gdf.to_crs(epsg=2154, inplace=True)
        output = gpd.GeoDataFrame(columns=self.parameters['champs'].split(','))
        try:
            gdf_L93 = self.gdf.to_crs(crs=2154)
            merged_geometry = gdf_L93.unary_union #gdf_L93.union_all() if geopandas version >= 1.0.0, it's not the case for my QGIS version (3.30)
            if hasattr(merged_geometry, 'geoms'):
                unique_gdf = gpd.GeoDataFrame(geometry=list(merged_geometry.geoms), crs="EPSG:2154") #multiple geometries
            else:
                unique_gdf = gpd.GeoDataFrame(geometry=[merged_geometry], crs="EPSG:2154")
            unique_gdf['bounds'] = unique_gdf.geometry.apply(lambda geom: list(geom.bounds))
            unique_gdf[['minx', 'miny', 'maxx', 'maxy']] = unique_gdf['bounds'].apply(pd.Series)

            for index, row in unique_gdf.iterrows():
                output_api_df=self.etablissements_SIRENE_in_bbox(xmin=row['minx'],ymin=row['miny'],xmax=row['maxx'],ymax=row['maxy'])
                output_api_gdf = gpd.GeoDataFrame(
                    output_api_df,
                    geometry=gpd.points_from_xy(output_api_df['coordonneeLambertAbscisseEtablissement'], output_api_df['coordonneeLambertOrdonneeEtablissement'], crs='EPSG:2154'),
                    crs='EPSG:2154')
                clipped_points = output_api_gdf.clip(row['geometry'])
                if not clipped_points.empty:
                    output = pd.concat([output, clipped_points], ignore_index=True)
            output.set_geometry('geometry', inplace=True)
            output.drop_duplicates(['siret','siren'], inplace=True)
            return output 
        except Exception as e:
            raise e
    
class siretInPolygonFilteredByAddresses(apiSireneRequest):
    """Selection from addresses of the siret located within the polygons uses as gdf.
    It is more accurate than selection by coordinates but much slower
    The user can add a liste of code NAF in the 'activity' parameter to use as filter"""
    def __init__(self,polygon:gpd.GeoDataFrame,params:dict,activity:list[str]=[]):
        super().__init__(**params)
        self.gdf=polygon
        self.activity=activity

    def etablissements_SIRENE_in_address(self,TypeStreet:str,NameStreet:str,CityCode:int) -> pd.DataFrame:
        """ Function to retrieve establishments based on street type, name, and city code from the SIRENE API.

        Args:
            self.parameters (dict): Parameters for the API request.
            self.activity (list): NAF code list added to activitePrincipaleEtablissement as a condition to the API request.
            TypeStreet (str): Description of the street type (e.g., "RUE", "AVENUE")
            NameStreet (str): Name of the street (e.g., "DE LA PAIX")
            CityCode (int): INSEE code of the city (e.g., 75056)

        Returns:
            pd.DataFrame: DataFrame containing the SIRENE establishments matching the criteria. And containing the columns specified in params['champs']
        """
        self.parameters['q'] = f'codeCommuneEtablissement:{CityCode} AND typeVoieEtablissement:"{TypeStreet}" AND libelleVoieEtablissement:"{NameStreet}" AND periode(etatAdministratifEtablissement:A)'
        if len(self.activity)>0:
            self.parameters['q']=apiSireneUtils.addFilterActivity(self.parameters['q'],self.activity)
        try:
            df_output=self.get_request_with_cursor()
        except Exception as e:
            raise f"Failed to retrieve data for typeVoieEtablissement:{TypeStreet}, libelleVoieEtablissement:{NameStreet}, codeCommuneEtablissement:{CityCode} : {e}"
        return df_output

    def establishments_SIRENE_in_polygon_address(self) -> gpd.GeoDataFrame:
        """Function to retrieve establishments within the polygon defined by the GeoDataFrame's geometry.
        Uses the addresses located within the polygon to query the SIRENE API for establishments, and check if
        the establishments's addresses are equal to the ones find within the polygon's geometry.
        To achieve this we collect information from differents API: Overpass API for the street network,
        API Carto to find in which city this network is located, SIRENE API to extract sirets from theses
        addresses, and the BAN geocoding API to get the coordinates of the siret's addresses and check if they
        are within the polygon.

        Raises:
            ValueError: No roads found in Overpass API using the bounding box
            e: Could be http error mostly

        Returns:
            gpd.GeoDataFrame: GeoDataFrame that contains all the siret located within the polygon used as inpput
        """
        #setting up the basic parameters needed for the API SIRENE request
        for y in ['numeroVoieEtablissement','indiceRepetitionEtablissement','typeVoieEtablissement','codePostalEtablissement','libelleCommuneEtablissement','coordonneeLambertAbscisseEtablissement','coordonneeLambertOrdonneeEtablissement']:
            if y not in self.parameters['champs'].split(','):
                self.parameters['champs']+=','+str(y)
        output_gdf = gpd.GeoDataFrame()
        output_request_sirene = pd.DataFrame(columns=self.parameters['champs'].split(','))
        road_name = set() 
        intersected_commune = gpd.GeoDataFrame(columns=['geometry','statut','population','date_du_recensement','organisme_recenseur','code_insee_du_canton','code_siren',
        'code_postal','superficie_cadastrale','id','nom_com','nom_com_m','code_epci','insee_com','insee_arr','insee_dep','insee_reg','nom_dep','nom_reg'])

        try:
            gdf_wgs84 = self.gdf.to_crs(crs=4326)
            merged_geometry = gdf_wgs84.unary_union #gdf_wgs84.union_all() if geopandas version >= 1.0.0 
            if hasattr(merged_geometry, 'geoms'):
                unique_gdf = gpd.GeoDataFrame(geometry=list(merged_geometry.geoms), crs="EPSG:4326") #multiple geometries
            else:
                unique_gdf = gpd.GeoDataFrame(geometry=[merged_geometry], crs="EPSG:4326")
            unique_gdf['bounds'] = unique_gdf.geometry.apply(lambda geom: list(geom.bounds))
            unique_gdf[['minx', 'miny', 'maxx', 'maxy']] = unique_gdf['bounds'].apply(pd.Series)
            
            for index, row in unique_gdf.iterrows():
                road_nt_cliped=requestOtherApi.get_osm_road_within_bbox(row['minx'], row['miny'], row['maxx'], row['maxy']).clip(row['geometry'])
                if road_nt_cliped.empty:
                    raise ValueError(f"No roads found in Overpass API using the bounding box for index {index} with coordinates: {row['miny']}, {row['minx']},{row['maxy']}, {row['maxx']}")
                else:
                    #This section intersects the roads from osm with the commune from API Carto to add the commune infos, there are 3 options:
                    if road_nt_cliped.geometry.within(intersected_commune.unary_union).all(): #1. it checks if the roads are already within the communes that were previously requested
                        road_nt_intersected_with_commune=gpd.overlay(road_nt_cliped, intersected_commune, how='intersection')
                    else:
                        try: #2. If not, it tries to get the commune from the API Carto using the convex hull geometrt of the roads, to reduce geometry and thus the URL size.
                            bboxTest = False
                            return_api_carto=requestOtherApi.get_request_api_carto_commune(geom=apiSireneUtils.gdf_convex_hull_to_geojson(road_nt_cliped))
                            intersected_commune = pd.concat([intersected_commune, gpd.GeoDataFrame.from_features(return_api_carto.json()['features'],crs="EPSG:4326")])
                            intersected_commune = intersected_commune.drop_duplicates(subset='insee_com')
                        except requests.exceptions.HTTPError as e:
                            if bboxTest == False: #3. If the convex hull geometry request fails, we retry with the bounding box of the roads this time.
                                bboxTest = True
                                return_api_carto=requestOtherApi.get_request_api_carto_commune(geom=apiSireneUtils.gdf_bbox_to_geojson(road_nt_cliped))
                                intersected_commune = pd.concat([intersected_commune, gpd.GeoDataFrame.from_features(return_api_carto.json()['features'],crs="EPSG:4326")])
                                intersected_commune = intersected_commune.drop_duplicates(subset='insee_com')
                            else:
                                raise e
                        road_nt_intersected_with_commune=gpd.overlay(road_nt_cliped, intersected_commune, how='intersection')
                    road_nt_intersected_with_commune[['TypeRue', 'LibelleRue']] = road_nt_intersected_with_commune['name'].str.split(n=1, expand=True)
                    road_nt_intersected_with_commune['TypeRue'] = road_nt_intersected_with_commune['TypeRue'].apply(lambda x: apiSireneUtils.replace_latin_unique_chars(x.upper()) if isinstance(x, str) else x)
                    road_nt_intersected_with_commune['LibelleRue'] = road_nt_intersected_with_commune['LibelleRue'].apply(lambda x: apiSireneUtils.replace_latin_unique_chars(x.upper()) if isinstance(x, str) else x)
                    road_name.update([(row_rn['TypeRue'], row_rn['LibelleRue'], row_rn['insee_com']) for index_rn, row_rn in road_nt_intersected_with_commune.iterrows() if isinstance(row_rn['name'], str)])
            for address in road_name:
                TypeStreet, NameStreet, CityCode = address
                establishments_in_address = self.etablissements_SIRENE_in_address(TypeStreet=TypeStreet,NameStreet=NameStreet,CityCode=CityCode)
                if not establishments_in_address.empty:
                    output_request_sirene = pd.concat([output_request_sirene, establishments_in_address], ignore_index=True)
            for index_s, row_s in output_request_sirene.iterrows():
                if not any([pd.isna(row_s['coordonneeLambertAbscisseEtablissement']),pd.isna(row_s['coordonneeLambertOrdonneeEtablissement'])]):
                    continue
                else:
                    geocodingAddress=AddressSearch.search_address_API_BAN(
                        q=f"{row_s['numeroVoieEtablissement']}{row_s['indiceRepetitionEtablissement'] if not pd.isna(row_s['indiceRepetitionEtablissement']) else ''} {row_s['typeVoieEtablissement']} {row_s['libelleVoieEtablissement']}, {row_s['codePostalEtablissement']} {row_s['libelleCommuneEtablissement']}",
                        limit=1,
                        citycode=row_s['codeCommuneEtablissement'])
                    if not geocodingAddress.empty:
                        geocodingAddress.to_crs("EPSG:2154", inplace=True)
                        output_request_sirene.loc[index_s,'coordonneeLambertAbscisseEtablissement'] = geocodingAddress.geometry.x.iloc[0]
                        output_request_sirene.loc[index_s,'coordonneeLambertOrdonneeEtablissement'] = geocodingAddress.geometry.y.iloc[0]
                    else:
                        output_request_sirene.loc[index_s,'coordonneeLambertAbscisseEtablissement'] = None
                        output_request_sirene.loc[index_s,'coordonneeLambertOrdonneeEtablissement'] = None
            output_request_sirene_gdf = gpd.GeoDataFrame(
                output_request_sirene,
                geometry=gpd.points_from_xy(output_request_sirene['coordonneeLambertAbscisseEtablissement'], output_request_sirene['coordonneeLambertOrdonneeEtablissement'], crs='EPSG:2154'),
                crs='EPSG:2154')
            output_request_sirene_gdf.to_crs("EPSG:4326", inplace=True)
            clipped_points = output_request_sirene_gdf.clip(unique_gdf['geometry']) 
            if not clipped_points.empty:
                output_gdf = pd.concat([output_gdf, clipped_points], ignore_index=True)
                output_gdf.set_geometry('geometry', inplace=True)
                output_gdf.drop_duplicates(['siret','siren'], inplace=True)
                return output_gdf
            else:
                raise ValueError('No establishments found within the polygon using the addresses (Overpass API) found within the polygon.')
        except Exception as e:
            raise e

if __name__ == "__main__":
    params={
    "api_key":'', #Add your api-key here!
    "champs": 'siren,dateCreationUniteLegale,siret,dateCreationEtablissement,trancheEffectifsEtablissement,enseigne1Etablissement,codeCommuneEtablissement,numeroVoieEtablissement,typeVoieEtablissement,libelleVoieEtablissement,codePostalEtablissement,libelleCommuneEtablissement,activitePrincipaleEtablissement,etatAdministratifEtablissement,coordonneeLambertAbscisseEtablissement,coordonneeLambertOrdonneeEtablissement',
    "nombre": 100,
    "curseur": '*',
    "date": '2099-01-01'
    }
    gdf= gpd.read_file('your_path/polygon.geojson')
    gdf.to_crs(epsg=4326, inplace=True)
    selection_by_coordinates=siretInPolygonFilteredByCoordinates(polygon=gdf,params=params,activity=[46,47]).establishments_SIRENE_in_polygon_coordinates()
    selection_by_address = siretInPolygonFilteredByAddresses(polygon=gdf,params=params,activity=[46,47]).establishments_SIRENE_in_polygon_address()
    apiSireneUtils.mergeRequestTypeOutput(selection_by_coordinates,selection_by_address).to_file('your_path/result_API_SIRENE.geojson', driver='GeoJSON')