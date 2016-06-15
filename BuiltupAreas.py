import arcpy
import os
from arcpy import env

'''
Calculates the built-up area witihin polygons and counts the ratio the built-up area to the area of calculation regions
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
builtUp= arcpy.GetParameterAsText(2)

arcpy.env.overwriteOutput=True

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
	
	# creates draf version of the zones_in and builtUp feature classes 
	arcpy.Select_analysis(zones_in,"calculationRegions")
	arcpy.Select_analysis(builtUp,"buildings", )
	
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")
	
	# obtains the ID of the zone in which paved surfaces are located
	arcpy.Intersect_analysis(["calculationRegions","buildings"], "buildings_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# calculates total area of built-up areas in the calculation regions 
	arcpy.Dissolve_management("buildings_inters", "BuildInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# creates the new column 'BuiltUpArea'
	arcpy.AddField_management("BuildInZones","BuiltUpArea","FLOAT")
	arcpy.CalculateField_management("BuildInZones", "BuiltUpArea", "[SHAPE_Area]", "VB")

	# adds field 'BuiltUpArea' to calculation regions
	arcpy.JoinField_management("calculationRegions","ZONE_ID","BuildInZones","ZONE_ID", "BuiltUpArea")

	# returns 0 if value is None 
	arcpy.CalculateField_management("calculationRegions", "BuiltUpArea", "r(!BuiltUpArea!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")

	# calculates the ratio of the built-up areas to the area of calculation regions
	arcpy.AddField_management("calculationRegions","PodilZastavenaPlocha","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilZastavenaPlocha", "[BuiltUpArea] / [SHAPE_Area] *100", "VB")
	
	arcpy.AlterField_management("calculationRegions", "BuiltUpArea", "ZastavenaPlocha", "ZastavenaPlocha")
	arcpy.AddMessage("Successful calculation.")
	
	# gives the proper name to the output file
	arcpy.Select_analysis("calculationRegions", results)
	
	arcpy.AddMessage("Your feature class was successfully created: {0}".format(results))
	
	# clean this mess up
	arcpy.Delete_management(TEMP)
	arcpy.AddMessage("Temporary directory was deleted.")
	arcpy.AddMessage("Thank you for using Help Tools, have a nice day. <('')")

except arcpy.ExecuteError:
	msgs = arcpy.GetMessages(2)
	arcpy.AddError(msgs)
	
except:
	arcpy.AddError("Operation failed. Your feature class was not created.") 

    
