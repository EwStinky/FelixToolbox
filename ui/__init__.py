
"""
/***************************************************************************
    __init__ - FelixToolBox QGIS plugins library
                             -------------------
        begin                : 19/03/2025
        email                : felix.gardot@gmail.com
	    copyright            : (c) 2025 by Félix GARDOT
        github               : https://!github.com/EwStinky
 ***************************************************************************/
"""
__version__ = '1.0.0'
__all__ = ['ui_mg_isochrone','ui_run_isochrone','ui_mg_address2point','ui_run_address2point','ui_mg_isochrone_ign','ui_run_isochrone_ign']

from .Isochrone_ORS_Tools_API_Dialog import ui_mg_isochrone,ui_run_isochrone
from .address2Point_Dialog import ui_mg_address2point,ui_run_address2point
from .Isochrone_IGN_API_Dialog import ui_mg_isochrone_ign,ui_run_isochrone_ign
