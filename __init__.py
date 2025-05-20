"""
/***************************************************************************
    __init__ - FelixToolBox init file
                             -------------------
        begin                : 05/03/2025
        email                : felix.gardot@gmail.com
	copyright            : (c) 2025 by Félix GARDOT
        github               : https://github.com/EwStinky
 ***************************************************************************/
"""

def classFactory(iface):
	from .FelixToolBox_menu import felixtoolbox_menu
	return felixtoolbox_menu(iface)

