# FelixToolbox

Félix's Toolbox is a QGIS plugin designed to regroup multiple GIS-oriented python scripts that were created through the time, for various professional projects. 
Félix's Toolbox provides intuitive features to facilitate various tasks that either do not exist in QGIS, or require several processes.
Because it is not oriented on one specific topic, Félix's Toolbox contains several tools that are not necesseraly related to each other, and are added throughout time.

## 🛠 Project Structure

- `icons/`: Directory containing the icons used for the plugin menu.
- `library/`: Directory containing every python file created, each file is corresponding to processing of a tool.
  - `__init__.py`: file selecting all the required python files needed for the tool processing.
  - `toolName.py`: file containing all the processes for the use of this tool.
- `ui/`: Directory containing UI files for each tool that requires one.
  - `__init__.py`: file selecting all the required python files needed for the tool's UI.
  - `toolName.ui`: UI file personalized for each specific tool.
  - `utils.py`: file containing several useful classes or functions the correct use and management of the UI.
- `__init__.py`: file initializing the QGIS plugin.
- `FelixToolBox_menu.py` : file containing the plugin's framework for its menu and submenus.
- `LICENSE` : GNU GENERAL PUBLIC LICENSE
- `metadata.txt`: metadata of the plugin.
- `requirements.txt`: Python dependencies required to run the plugin.

## 🎁 Features

👉 **Isochrone ORS API**: Requests isochrones from the ORS (Openrouteservice) API for the selected point layers and their parameters, and then dissolve for each layer the isochrones per time unit.

👉 **Isochrone IGN API**: Similar to the Isochrone ORS API tool, but limited to France and does not require any API key. It requests isochrones from the IGN (Institut national de l'information géographique et forestière) API for the selected layers and their parameters, and then dissolve for each layer the isochrones per time unit.

👉 **Map Screenshot**: Produces instantly a map of your current QGIS instance view with all its active layers, with a personalized title and sources if needed.

👉 **Address to Point**: Geocodes addresses from the Nominatim API or the BAN API (France only) by writing addresses or by using a CSV file.

👉 **Siret located within polygon**: Produces a point layer of every active establishement located within a selected polygon. These establishements come from the SIRENE API (Système d’Identification du Répertoire des Entreprises et des Établissements). The API provides comprehensive, up-to-date information about companies, establishments, and self-employed individuals in France.

## ⚙️ Installation 

1. Download the plugin from the [GitHub repository](https://github.com/your-repo/FelixToolbox).
2. Open QGIS and navigate to `Plugins > Manage and Install Plugins`.
3. Click on the `Install from ZIP` tab and select the downloaded ZIP file.
4. Click `Install Plugin` and restart QGIS if necessary.
5. Verify that the plugin is activated in `Installed`

## 🌵 Usage

1. Open QGIS and activate the plugin from `Plugins > FelixToolbox`.
2. Access the tools from the `FelixToolbox` menu or toolbar.
3. Follow the on-screen instructions for each tool.

## ⚠️ Requirements

- QGIS 3.x or later
- Python 3.x
- pandas
- geopandas < 1.0.0 (because of the version used in QGIS 3.x)
- requests

## 🎉 Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request. Please ensure your code adheres to the project's coding standards. 

## 📜 License

This project is licensed under the GNU GENERAL PUBLIC LICENSE.

## 🔧 Support

If you encounter any issues or have questions, please open an issue on the [GitHub repository](https://github.com/EwStinky/FelixToolbox).

## 📢 Attributions

All emojis used in the plugin are designed by OpenMoji – the open-source emoji and icon project. License: CC BY-SA 4.0
https://github.com/hfg-gmuend/openmoji/tree/master

