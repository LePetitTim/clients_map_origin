import overpy
import csv
import json
from geojson import FeatureCollection, Feature
from difflib import SequenceMatcher
from shapely.geometry import shape, mapping
from shapely.ops import cascaded_union
import fiona
import requests
from collections import OrderedDict


def xstr(s):
    return '' if s is None else str(s)


def check_geometry(dict, element):
    if dict["geojson"]['type'] == "Polygon" or dict["geojson"]['type'] == "MultiPolygon":
        if not element.get("geometry"):
            element["geometry"] = shape(dict["geojson"])
        else:
            element["geometry"] = cascaded_union([shape(dict["geojson"]), element["geometry"]])


def check_conditions(name_c, element_c):
    if "parc national" in name_c or "parc amazonien" in name_c:
        print(name_c)
        get_national_park(name_c, element_c)
    elif "parc naturel" in name_c:
        get_regional_park(name_c, element_c)
    elif "communauté de communes" in name_c:
        get_township(name_c, element_c)
    elif "départemental" in name_c:
        get_administrative_boundary(name_c, element_c)
    elif "régional" in name_c:
        get_administrative_boundary(name_c, element_c)
    else:
        get_other(name_c, element_c)
        pass
        requests.get("https://nominatim.openstreetmap.org/search.php?q=" + name
                         .replace(" ", "+") + "&polygon_geojson=1&viewbox=&format=json")


def get_other(name, element):
    response = requests.get("https://nominatim.openstreetmap.org/search.php?q=" + name
                            .replace(" ", "+") + "&polygon_geojson=1&viewbox=&format=json")
    tab = json.loads(response.content.decode('utf-8'))
    if not tab:
        return None
    for value in tab:
        check_geometry(value, element)


def get_administrative_boundary(name, element):
    response = requests.get("https://nominatim.openstreetmap.org/search.php?q=" + name.split(" ")[-1]
                             .replace(" ", "+") + "&polygon_geojson=1&viewbox=&format=json")
    tab = json.loads(response.content.decode('utf-8'))
    if len(tab) > 0:
        value = tab[0]
    else:
        return None
    check_geometry(value, element)


def get_township(name, element):
    response = requests.get("https://nominatim.openstreetmap.org/search.php?q=" + name.split(" ")[-1].replace(" ", "+")
                             + "&osm_type=city&polygon_geojson=1&viewbox=&format=json")
    tab = json.loads(response.content.decode('utf-8'))
    i = 0
    while i < len(tab) and tab[i]["class"] != "boundary":
        i += 1
    value = tab[i]
    check_geometry(value, element)


def get_national_park(name, element):
    response_to_check = []
    response_to_check.append(requests.get("https://nominatim.openstreetmap.org/search.php?q=" + name
                             .replace(" ", "+") + "(cœur)" + "&polygon_geojson=1&viewbox=&format=json"))
    response_to_check.append(requests.get(
        "https://nominatim.openstreetmap.org/search.php?q=aire+d'adhésion+du+" + name
        .replace(" ", "+") + "&polygon_geojson=1&viewbox=&format=json"))
    for response in response_to_check:
        tab = json.loads(response.content.decode('utf-8'))
        for value in tab:
            check_geometry(value, element)


def get_regional_park(name, element):
    response = requests.get("https://nominatim.openstreetmap.org/search.php?q=" + name.replace(" ", "+")
                            + "&polygon_geojson=1&viewbox=&format=json")
    tab = json.loads(response.content.decode('utf-8'))
    for value in tab:
        if value["type"] == "protected_area":
            check_geometry(value, element)

# Geotrek Clients
file = open('Liste-clients_Geotrek.csv', "r")
spamreader = csv.DictReader(file, delimiter=';', quotechar='"')
data_csv = []

for row in spamreader:
    data_csv.append(row)

values_name = {}

jsonfile = open('file.json', 'w')

with open('Parcs_site_proteges.geojson', 'r', encoding='utf8') as json_file:
    data = json.load(json_file)
for t in data["features"]:
    try:
        values_name[t["properties"]["name"]] = shape(t["geometry"])
    except KeyError as e:
        pass

for element in data_csv:
    name = xstr(element.get("NOM DE LA STRUCTURE")).lower()
    type = xstr(element.get("TYPE DE STRUCTURE")).lower()
    regroup = xstr(element.get("REGROUPEMENT DE STRUCTURES")).lower()
    if regroup:
        names = regroup.split("\n")
        for name in names:
            check_conditions(name, element)
    else:
        check_conditions(name, element)

schema = {'geometry': 'MultiPolygon', 'properties': {'id':'int','nom': "str", 'type_struc': 'str', 'Annee_Proj': "str", "Site_web": "str"}}


with fiona.open('Clients.shp', 'w', 'ESRI Shapefile', schema, encoding='utf-8') as c:
    for i, element in enumerate(data_csv):
        if element.get("geometry"):
            c.write({'geometry':  mapping(element["geometry"]), 'properties': {'id' : int(element.get("NOMBRE DE CLIENT")), 'nom': element.get("NOM DE LA STRUCTURE"), 'type_struc': element.get("TYPE DE STRUCTURE"), 'Annee_Proj': element.get("ANNÉE DU PROJET"), "Site_web": element.get("SITE WEB")}})
