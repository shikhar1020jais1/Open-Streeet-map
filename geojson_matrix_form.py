
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from shapely.geometry import LineString
import numpy as np
import matplotlib.pyplot as plt
from osm2geojson import json2geojson 
import requests

def get_data_from_overpass(query):
  endpoint = "https://overpass-api.de/api/interpreter"
  response = requests.get(endpoint,params={'data':query})
  overpass_json_data = response.json()
  geojson_data = json2geojson(overpass_json_data)
  return geojson_data

#take a list of polygon coordinates. return a normalized polygon collections (real world coordinates converted into matrix coordinates)
def normalization_of_polygon_collection(polygon_collection,bbox):
    #perform normalization and inversion of default geojson coordiantes
    polygon_collection = list(map(lambda x: list(map(lambda y:[int(round(y[1]-bbox[0],3)*RESOLUTION_FACTOR),int(round(y[0]-bbox[1],3)*RESOLUTION_FACTOR)],x)),polygon_collection))    
    #convert it into shapely polygon objects
    polygon_collection = list(map(lambda p:Polygon(p) ,polygon_collection))  
    return (polygon_collection)

def normalization_of_node_collection(node_collection,bbox):
    node_collection = list(map(lambda x:[int(round(x[1]-bbox[0],3)*RESOLUTION_FACTOR),int(round(x[0]-bbox[1],3)*RESOLUTION_FACTOR)],node_collection))
    node_collection = list(map(lambda x:(x[0],x[1]),node_collection))
    return (node_collection)

def noramalizatioin_of_line_collection(line_collection,bbox):
    line_collection = list(map(lambda x: list(map(lambda y:[int(round(y[1]-bbox[0],3)*RESOLUTION_FACTOR),int(round(y[0]-bbox[1],3)*RESOLUTION_FACTOR)],x)),line_collection))    
    line_collection = list(map(lambda x:LineString(x),line_collection))
    return(line_collection)


#overpass query and data fetching operations
def get_water_data(BOUNDARY_BOX):
    bbox = f"{BOUNDARY_BOX[0]},{BOUNDARY_BOX[1]},{BOUNDARY_BOX[2]},{BOUNDARY_BOX[3]}"
    water_query = f"[out:json][timeout:100];(way[waterway]({bbox});node[water]({bbox});way['water'='lake']({bbox});way[natural=water]({bbox});relation[natural=water]({bbox}););out body;>;out skel qt;"
    result = get_data_from_overpass(water_query)
    water_polygons = []
    water_lines = []
    for i in result["features"]:
        if i['geometry']['type']=="LineString":
            water_lines.append(i)
        if(i['geometry']['type']=="Polygon"):
            water_polygons.append(i)
    return(water_polygons,water_lines)

#overpass query and data fetching operations and filteration of polygon shapes
def get_forest_data(BOUNDARY_BOX):
    bbox = f"{BOUNDARY_BOX[0]},{BOUNDARY_BOX[1]},{BOUNDARY_BOX[2]},{BOUNDARY_BOX[3]}"
    forest_query = f"[out:json][timeout:100];(way['natural'='wood']({bbox});way['landuse'='recreation_ground']({bbox});way['landuse'='meadow']({bbox});way['natural'='scrub']({bbox});way['leisure'='park']({bbox}););out body;>;out skel qt;"
    result = get_data_from_overpass(forest_query)
    forest_polygons = []
    for i in result["features"]:
        if(i['geometry']['type']=="Polygon"):
            forest_polygons.append(i)
    return(forest_polygons)

# retriving the schools and hospitals as points. so that these areas can be used as restricted area.
def get_node_data(BOUNDARY_BOX):
    bbox = f"{BOUNDARY_BOX[0]},{BOUNDARY_BOX[1]},{BOUNDARY_BOX[2]},{BOUNDARY_BOX[3]}"
    nodes_query = f"[out:json][timeout:100];(node['amenity'='hospital']({bbox});node['amenity'='school']({bbox});node['amenity'='college']({bbox});node['amenity'='university']({bbox}););out body;>;out skel qt;"
    result = get_data_from_overpass(nodes_query)
    node_points = []
    for i in result["features"]:
        if(i['geometry']['type']=="Point"):
            node_points.append(i)
    return(node_points)

    



RESOLUTION_FACTOR = 1000
RESOLUTION_DECIMAL = 3
    

    
print("Enter comma seperated without brackets: ")
Start = list(map(float,input("Enter Start Location : ").split(",")))
End = list(map(float,input("Enter End Location : ").split(",")))
BOUNDARY_BOX=Start+End;
(water_polygons,water_lines) = get_water_data(BOUNDARY_BOX)
forest_polygons = get_forest_data(BOUNDARY_BOX)
node_points = get_node_data(BOUNDARY_BOX)

    
    
bbox = [0,0,int((round(BOUNDARY_BOX[2],RESOLUTION_DECIMAL)-round(BOUNDARY_BOX[0],RESOLUTION_DECIMAL))*RESOLUTION_FACTOR),int(round(BOUNDARY_BOX[3]-BOUNDARY_BOX[1],RESOLUTION_DECIMAL)*RESOLUTION_FACTOR)]
print(bbox,"MATRIX INDICES")  

    
#getting list of featurs from fetaurecollection objects
water_polygon_collection = list(map(lambda x : x["geometry"]["coordinates"][0],water_polygons))
waterline_collection = list(map(lambda x:x["geometry"]["coordinates"],water_lines))
forest_polygon_collection = list(map(lambda x : x["geometry"]["coordinates"][0],forest_polygons))
nodes_collection = list(map(lambda x:x["geometry"]["coordinates"],node_points))
    
    
#converting real world coordinates to normalized coordinates to plot on matrix indexes(index can be [0 to n] and only positive integer)
water_polygon_list = normalization_of_polygon_collection(water_polygon_collection,BOUNDARY_BOX)
waterline_list = noramalizatioin_of_line_collection(waterline_collection,BOUNDARY_BOX)
forest_polygon_list = normalization_of_polygon_collection(forest_polygon_collection,BOUNDARY_BOX)
nodes_list = set(normalization_of_node_collection(nodes_collection,BOUNDARY_BOX))
    
    
#creating empty matrix
matrix = [[{"water":0,"forest":0,"school":0,"population":0} for _ in range(0,bbox[3])] for _ in range(0,bbox[2])]
    
    
    
#calculation of lat and longs for normalized cells
base_lat = round(BOUNDARY_BOX[0],RESOLUTION_DECIMAL)
base_lng = round(BOUNDARY_BOX[1],RESOLUTION_DECIMAL)

    

#filling water in matrix
for i in range(0,len(matrix)):
    for j in range(0,len(matrix[0])):
        point = Point(i,j)
        for polygon in water_polygon_list:
            if(polygon.covers(point)):
                matrix[i][j]["water"] = 1
        for line in waterline_list:
            if(line.distance(point)<0.5):
                matrix[i][j]["water"] = 1
                    
#filling forest in matrix
for i in range(0,len(matrix)):
    for j in range(0,len(matrix[0])):
        point = Point(i,j)
        for polygon in forest_polygon_list:
            if(polygon.covers(point)):
                matrix[i][j]["forest"] = 1
                    
#filling nodes in matrix
for i in range(0,len(matrix)):
    for j in range(0,len(matrix[0])):
        point = (i,j)
        if(point in nodes_list):
            matrix[i][j]["school"] = 1
                
#to convert the matrix objects orientation according to real world map
matrix.reverse()

#adding real world coordinates (this step should be performed only after the reversing of matrix)
for i in range(0,len(matrix)):
    for j in range(0,len(matrix[0])):
        matrix[i][j]["latitude"]= round(base_lat + (i+1)*(1/RESOLUTION_FACTOR),RESOLUTION_DECIMAL)
        matrix[i][j]["longitude"] = round(base_lng + (j+1)*(1/RESOLUTION_FACTOR),RESOLUTION_DECIMAL)

            
plt.imshow(list(map(lambda x:list(map(lambda y:y["water"],x)),matrix)),cmap='Blues')
plt.xticks([])
plt.yticks([])
plt.suptitle('Matrix elements: Water Bodies', fontsize=20)
plt.xlabel('Columns', fontsize=18)
plt.ylabel('Rows', fontsize=16)
plt.show()

plt.imshow(list(map(lambda x:list(map(lambda y:y["forest"],x)),matrix)),cmap="Greens")
plt.xticks([])
plt.yticks([])
plt.suptitle('Matrix elements: Forest Bodies', fontsize=20)
plt.xlabel('Columns', fontsize=18)
plt.ylabel('Rows', fontsize=16)
plt.show()

plt.imshow(list(map(lambda x:list(map(lambda y:y["school"],x)),matrix)),cmap="Reds")
plt.xticks([])
plt.yticks([])

plt.suptitle('Matrix elements: Schools/Hospitals', fontsize=20)
plt.xlabel('Columns', fontsize=18)
plt.ylabel('Rows', fontsize=16)
plt.show()
    
    #use this matrix as final output
OUTMatrix = matrix

ROWS = len(OUTMatrix) 
COLS =len(OUTMatrix[0])
#print(OUTMatrix[ROWS-1][COLS-1])
# BOUNDARY_BOX = [27.1794487823,77.454256286,27.245857,77.526784667]
