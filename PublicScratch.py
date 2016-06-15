import arcpy
from arcpy import env
import os

'''
Calculates the area of public spaces (both streets and park zones) and counts the ratio of the public spaces area to the area of calculation regions
'''
# creates parameters
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
landUseLayer = arcpy.GetParameterAsText(2)

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
	arcpy.AddMessage("Processing can take few minutes. Be patient :)")
	
	# selects the proper polygons from land use layer and creates draf version of the zones_in layer
	arcpy.Select_analysis(zones_in, "calculationRegions")
	arcpy.Select_analysis(landUseLayer,"landUsePublic", "KOD = 'RPH' OR KOD = 'RPP' OR KOD = 'RPU' OR KOD = 'VC' OR KOD = 'VM' OR KOD = 'VN' OR KOD = 'VPM' OR KOD = 'VPN' OR KOD = 'VPP'")
	arcpy.Select_analysis(landUseLayer,"landUseRoads", "KOD = 'VC' OR KOD = 'VM' OR KOD = 'VN' OR KOD = 'VPM' OR KOD = 'VPN' OR KOD = 'VPP'")
	arcpy.Select_analysis(landUseLayer,"landUseParks", "KOD = 'RPH' OR KOD = 'RPP' OR KOD = 'RPU'")
	
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")
	
	# obtains the ID of the zone in which public spaces are located
	arcpy.Intersect_analysis(["calculationRegions","landUsePublic"], "PublicSpaces_inters", "ALL", "0.1 METERS", "INPUT")
	arcpy.Intersect_analysis(["calculationRegions","landUseRoads"], "Road_inters", "ALL", "0.1 METERS", "INPUT")
	arcpy.Intersect_analysis(["calculationRegions","landUseParks"], "Parks_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# calculates total area of public spaces in the calculation regions 
	arcpy.Dissolve_management("PublicSpaces_inters", "PublicInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	arcpy.Dissolve_management("Road_inters", "RoadsInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	arcpy.Dissolve_management("Parks_inters", "ParksInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# creates the new column with area of 'AREA_PUBLIC'
	arcpy.AddField_management("PublicInZones","AREA_PUBLIC","FLOAT")
	arcpy.CalculateField_management("PublicInZones", "AREA_PUBLIC", "[SHAPE_Area]", "VB")

	arcpy.AddField_management("RoadsInZones","AREA_ROADS","FLOAT")
	arcpy.CalculateField_management("RoadsInZones", "AREA_ROADS", "[SHAPE_Area]", "VB")

	arcpy.AddField_management("ParksInZones","AREA_PARKS","FLOAT")
	arcpy.CalculateField_management("ParksInZones", "AREA_PARKS", "[SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful calculation.")
	
	# adds column with calculated areas of public spaces within every calculation region
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PublicInZones","ZONE_ID", "AREA_PUBLIC")
	arcpy.JoinField_management("calculationRegions","ZONE_ID","RoadsInZones","ZONE_ID", "AREA_ROADS")
	arcpy.JoinField_management("calculationRegions","ZONE_ID","ParksInZones","ZONE_ID", "AREA_PARKS")

	# returns 0 if value is None 
	arcpy.CalculateField_management("calculationRegions", "AREA_PUBLIC", "r(!AREA_PUBLIC!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("calculationRegions", "AREA_ROADS", "r(!AREA_ROADS!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("calculationRegions", "AREA_PARKS", "r(!AREA_PARKS!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")

	# calculates the ratio of the public spaces area to the area of calculation regions
	arcpy.AddField_management("calculationRegions","PodilVerejnaProst,"FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilVerejnaProst", "[AREA_PUBLIC] / [SHAPE_Area]", "VB")

	arcpy.AddField_management("calculationRegions","PodilUlicniProst","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilUlicniProst", "[AREA_ROADS] / [SHAPE_Area]", "VB")

	arcpy.AddField_management("calculationRegions","PodilParkovaProst","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilParkovaProst", "[AREA_PARKS] / [SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "AREA_PUBLIC", "VerejnaProstranstvi", "VerejnaProstranstvi")
	arcpy.AlterField_management("calculationRegions", "AREA_ROADS", "UlicniProstranstvi", "UlicniProstranstvi")
	arcpy.AlterField_management("calculationRegions", "AREA_PARKS", "ParkovaProstranstvi", "ParkovaProstranstvi")
	
	arcpy.CopyFeatures_management ("calculationRegions", results)
	
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



