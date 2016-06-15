import arcpy
from arcpy import env
import os

'''
Here is the description
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
distanceToTheCenter= arcpy.GetParameterAsText(2)
center = arcpy.GetParameterAsText(3)

'''
def DistanceClass(distanceToTheCenter, center):
	# converts distanceToTheCenter to geodatabase feature classes
	arcpy.FeatureClassToGeodatabase_conversion(distanceToTheCenter, 'C:/Esri/temp_data.gdb')
	# distanceToTheCenter: feature class "PIDCopy" needs to be clipped using "centrum_p", and then the donut hole needs to be replaced with 6 polygons each one for every distance (ToBreak : 5, 10, 15, 30, 45, 60)
	arcpy.Erase_analysis ("PIDCopy", center, "PIDCopy_clipped")
	arcpy.Merge_management (["PIDCopy_clipped", center, center, center, center, center, center], "distances")
	arcpy.CalculateField_management("distances", "ToBreak", "r(!ToBreak!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	lst = [5, 10, 15, 30, 45, 60] 
	fc = 'C:/Esri/temp_data.gdb/distances'
	field = ['ToBreak']
	
	# Create update cursor for feature class 
	with arcpy.da.UpdateCursor(fc, field) as cursor:
		i = 0
		for row in cursor:
			if (row[0] == 0): 
				print row[0]
				row[0] = lst[i]
				i += 1
				
			# Update the cursor with the updated list
			cursor.updateRow(row)
'''

def updatedDistanceClass(distanceToTheCenter, center):
	# converts distanceToTheCenter to geodatabase feature classes
	arcpy.FeatureClassToGeodatabase_conversion(distanceToTheCenter, 'C:/Esri/temp_data.gdb')
	# distanceToTheCenter: feature class "PIDCopy" needs to be clipped using "centrum_p", and then the donut hole needs to be replaced with 6 polygons each one for every distance (ToBreak : 5, 10, 15, 30, 45, 60)
	arcpy.Erase_analysis ("PIDCopy", center, "PIDCopy_clipped")
	
	lst = [] 
	# Create update cursor for feature class 
	with arcpy.da.UpdateCursor('C:/Esri/temp_data.gdb/PIDCopy_clipped', ['ToBreak']) as cursor:
		for row in cursor:
			if (row[0] != 0 and row[0] not in lst):
				lst.append(row[0])
				
	merged = ["PIDCopy_clipped"]
	for i in range(len(lst)):
		merged.append(center)
	arcpy.Merge_management (merged, "distances")
	arcpy.CalculateField_management("distances", "ToBreak", "r(!ToBreak!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	#arcpy.Sort_management ("distances", "distances_sorted", [["ToBreak", "DESCENDING"]])
	
	# Create update cursor for feature class 
	with arcpy.da.UpdateCursor('C:/Esri/temp_data.gdb/distances', ['ToBreak'], 'ToBreak = 0') as cursor2:
		i = 0
		for row in cursor2:
			#if (row[0] == 0): 
			#print row[0]
			row[0] = lst[i]
			i += 1
				
			# Update the cursor with the updated list
			cursor2.updateRow(row)
			
try:
	# creates temprary directory
	try:
		TEMP = "C:\\Esri\\temp_data.gdb" 
		if arcpy.Exists(TEMP):  
			arcpy.Delete_management(TEMP)         
		arcpy.CreateFileGDB_management("C:\\Esri", "temp_data.gdb")
		env.workspace = TEMP
	except:
		TEMP = "C:\\Windows\\Temp\\temp_data.gdb"
		if arcpy.Exists(TEMP):  
			arcpy.Delete_management(TEMP)         
		arcpy.CreateFileGDB_management("C:\\Windows\\Temp", "temp_data.gdb")
		env.workspace = TEMP
	
	arcpy.AddMessage("Temporary directory was created. Path: {0}".format(TEMP))
	
	# creates draf version of the zones_in feature class
	arcpy.Select_analysis(zones_in,"calculationRegions")

	# assigns an ID number to the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	# updates input distanceToTheCenter
	updatedDistanceClass(distanceToTheCenter, center)
	#arcpy.Dissolve_management("distances", "distances_DISS", "ToBreak")
	
	# gets ID of the zones
	arcpy.Intersect_analysis(["calculationRegions", "distances"], "distance_inters")
	arcpy.AddMessage("Successful intersection.")
	
	# calculates the areas of the polygons with specified distance from the city center
	arcpy.AddField_management("distance_inters","Time_Area","FLOAT")
	arcpy.CalculateField_management("distance_inters", "Time_Area", "!shape.area@squaremeters!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")
	
	# rows - > columns
	arcpy.PivotTable_management("distance_inters", "ZONE_ID", "ToBreak", "Time_Area", "pivot_distance")
	
	arcpy.AddMessage("Successful pivot table creation.")
	
	# ZONE_ID flattening
	arcpy.Statistics_analysis ("pivot_distance", "pivot_dist_flat", [["ToBreak5", "SUM"], ["ToBreak10", "SUM"],["ToBreak15", "SUM"],["ToBreak30", "SUM"],["ToBreak45", "SUM"],["ToBreak60", "SUM"]], "ZONE_ID")
	
	arcpy.AddMessage("Successful table flattening.")
	
	# add distance fields to calculation regions feature class
	arcpy.JoinField_management("calculationRegions","ZONE_ID","pivot_dist_flat","ZONE_ID", ["SUM_ToBreak5", "SUM_ToBreak10", "SUM_ToBreak15", "SUM_ToBreak30", "SUM_ToBreak45", "SUM_ToBreak60"])
	
	# divides the distance field areas by the area of the zones
	# remember - those are polygons dist from 0-x, so the last one (60) should have  %= 100 
	arcpy.AddField_management("calculationRegions","PodilDo5minMHD","LONG")
	arcpy.CalculateField_management("calculationRegions", "PodilDo5minMHD", "[SUM_ToBreak5] / [SHAPE_Area]", "VB")
	
	arcpy.AddField_management("calculationRegions","PodilDo10minMHD","LONG")
	arcpy.CalculateField_management("calculationRegions", "PodilDo10minMHD", "[SUM_ToBreak10] / [SHAPE_Area]", "VB")
	
	arcpy.AddField_management("calculationRegions","PodilDo15minMHD","LONG")
	arcpy.CalculateField_management("calculationRegions", "PodilDo15minMHD", "[SUM_ToBreak15] / [SHAPE_Area]", "VB")
	
	arcpy.AddField_management("calculationRegions","PodilDo30minMHD","LONG")
	arcpy.CalculateField_management("calculationRegions", "PodilDo30minMHD", "[SUM_ToBreak30] / [SHAPE_Area]", "VB")
	
	arcpy.AddField_management("calculationRegions","PodilDo45minMHD","LONG")
	arcpy.CalculateField_management("calculationRegions", "PodilDo45minMHD", "[SUM_ToBreak45] / [SHAPE_Area]", "VB")
	
	arcpy.AddField_management("calculationRegions","PodilDo60minMHD","LONG")
	arcpy.CalculateField_management("calculationRegions", "PodilDo60minMHD", "[SUM_ToBreak60] / [SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful calculations.")
	
	#alters the names of the fields
	arcpy.AlterField_management("calculationRegions", "SUM_ToBreak5", "PlochaDo5minMHD")
	arcpy.AlterField_management("calculationRegions", "SUM_ToBreak10", "PlochaDo10minMHD")
	arcpy.AlterField_management("calculationRegions", "SUM_ToBreak15", "PlochaDo15minMHD")
	arcpy.AlterField_management("calculationRegions", "SUM_ToBreak30", "PlochaDo30minMHD")
	arcpy.AlterField_management("calculationRegions", "SUM_ToBreak45", "PlochaDo45minMHD")
	arcpy.AlterField_management("calculationRegions", "SUM_ToBreak60", "PlochaDo60minMHD")
	
	arcpy.AddMessage("Successful alteration of fields names.")
	
	# gives the proper name to the output file
	arcpy.Select_analysis("calculationRegions", results)
	arcpy.AddMessage("Your feature class was successfully created: {0}".format(results))
	
	# clean this mess up
	#arcpy.Delete_management(TEMP)
	arcpy.AddMessage("Temporary directory was deleted.")
	arcpy.AddMessage("Thank you for using Help Tools, have a nice day. <('')")

except arcpy.ExecuteError:
	msgs = arcpy.GetMessages(2)
	arcpy.AddError(msgs)
	
except:
    arcpy.AddError("Operation failed. Your feature class was not created.") 
