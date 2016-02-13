#!/usr/bin/env python

import json
import time

def pointInPolygon(polyCorners, polyX, polyY, x, y):

    j = polyCorners - 1
    oddNodes = False

    for i in range (0,polyCorners):
        if (polyY[i]<y and polyY[j]>=y) or (polyY[j]<y and polyY[i]>=y):
            if (polyX[i]+(y-polyY[i])/(polyY[j]-polyY[i])*(polyX[j]-polyX[i])<x):
                oddNodes= not oddNodes
        j = i

    return oddNodes

with open('vertices.json') as vertices_file:
    vertices_file = json.load(vertices_file)

#x_cords = (vertices_file['point0_X'], vertices_file['point1_X'], vertices_file['point2_X'], vertices_file['point3_X'])
#x_cords = [int(i) for i in x_cords]
#y_cords = (vertices_file['point0_Y'], vertices_file['point1_Y'], vertices_file['point2_Y'], vertices_file['point3_Y'])
#y_cords = [int(i) for i in y_cords]
num_cords = len(vertices_file['points'])
x_cords = []
y_cords = []
for i in range (0,num_cords):
    x_cords.append(vertices_file["points"][i][0])
    y_cords.append(vertices_file["points"][i][1])

#define test point
x = 1.1
y = 0.1

result = pointInPolygon(num_cords,x_cords,y_cords,x,y)

print(result)
time.sleep(5)
