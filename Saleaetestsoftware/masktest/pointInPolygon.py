#!/usr/bin/env python

#  Derived from alienryderflex.com/polygon/
#  Globals which should be set before calling this function:
#
#  int    polyCorners  =  how many corners the polygon has (no repeats)
#  float  polyX()      =  horizontal coordinates of corners
#  float  polyY()      =  vertical coordinates of corners
#  float  x, y         =  point to be tested
#
#  (Globals are used in this example for purposes of speed.  Change as
#  desired.)
#
#  The function will return YES if the point x,y is inside the polygon, or
#  NO if it is not.  If the point is exactly on the edge of the polygon,
#  then the function may return YES or NO.
#
#  Note that division by zero is avoided because the division is protected
#  by the "if" clause which surrounds it.

def pointInPolygon(polyCorners, polyX, polyY, x, y):

    j = polyCorners - 1
    oddNodes = False

    for i in range (0,polyCorners):
        if (polyY(i)<y and polyY(j)>=y or polyY(j)<y and polyY(i)>=y):
            if (polyX(i)+(y- polyY(i))/(polyY(j)-polyY(i))*(polyX(j)-polyX(i))<x):
                oddNodes= not oddNodes
        j = i

    return oddNodes