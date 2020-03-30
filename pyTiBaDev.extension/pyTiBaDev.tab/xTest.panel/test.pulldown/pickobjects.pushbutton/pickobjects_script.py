"""
- create Levels from ExcelTable
- create FloorPlan and/or CeilingPlan 

Excel Layout. 
Data Row to start A4  A3 = Headers
Elevation/ Levelname/ Create Flooprlan/ CreateCeilingPlan
- uses last used LevelType 
"""


__author__ = "Tillmann Baumeister"

from Autodesk.Revit.DB import FilteredElementCollector, Transaction, BuiltInParameter, Level
from Autodesk.Revit import DB
import System
from System.Runtime.InteropServices import Marshal 
import sys, os
from rpw.ui.forms import TaskDialog 
from pyrevit import forms 
from Autodesk.Revit.UI.Selection import ObjectType

uidoc = __revit__.ActiveUIDocument 
doc = __revit__.ActiveUIDocument.Document # doc = DocumentManager.Instance.CurrentDBDocument 
uiapp = __revit__ # is the same as uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application 


# PickObjects  ---> Finish Button in OptionsBar! 
ref = uidoc.Selection.PickObjects(ObjectType.Element)

for i in ref: 
    print i, i.ElementId, doc.GetElement(i.ElementId), "---------------------------------\n"

elem = doc.GetElement(ref[0].ElementId)


#from Darren Thomas - StackOverflow
# def pickobjects():
    # from Autodesk.Revit.UI.Selection import ObjectType
    # __window__.Hide()
    # picked = uidoc.Selection.PickObjects(ObjectType.Element)
    # __window__.Show()
    # __window__.Topmost = True
    # return picked

# refs = pickobjects()

