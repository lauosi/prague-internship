import arcpy
from arcpy import env
import os

'''
Calculates the area of paved surfaces and counts the ratio of the paved area to the area of calculation regions
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
technicalMap = arcpy.GetParameterAsText(2)

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

	# selects the proper polygons from technical map and creates draf version of the zones_in layer
	arcpy.Select_analysis(zones_in,"calculationRegions")
	arcpy.Select_analysis(technicalMap,"pavedAreas", "CTVUK_KOD = 600 OR CTVUK_KOD = 601 OR CTVUK_KOD = 602 OR CTVUK_KOD = 603 OR CTVUK_KOD = 604 OR CTVUK_KOD = 700 OR CTVUK_KOD = 701 OR CTVUK_KOD = 702 OR CTVUK_KOD = 703 OR CTVUK_KOD = 704 OR CTVUK_KOD = 705 OR CTVUK_KOD = 1003")
	
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")
	
	# obtains the ID of the zone in which paved surfaces are located
	arcpy.Intersect_analysis(["calculationRegions","pavedAreas"], "PavedArea_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# calculates total area of paved surfaces in the calculation regions 
	arcpy.Dissolve_management("PavedArea_inters", "PavedInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# creates the new column 'PAVED_AREA'
	arcpy.AddField_management("PavedInZones","PAVED_AREA","FLOAT")
	arcpy.CalculateField_management("PavedInZones", "PAVED_AREA", "[SHAPE_Area]", "VB")

	# adds column with paved surfaces of public spaces within every calculation region
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PavedInZones","ZONE_ID", "PAVED_AREA")

	# returns 0 if value is None 
	arcpy.CalculateField_management("calculationRegions", "PAVED_AREA", "r(!PAVED_AREA!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")

	# calculates the ratio of the paved area to the area of calculation regions
	arcpy.AddField_management("calculationRegions","PodilZpevnenychPloch","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilZpevnenychPloch", "[PAVED_AREA] / [SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "PAVED_AREA", "ZpevnenePlochy", "ZpevnenePlochy")
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
    
