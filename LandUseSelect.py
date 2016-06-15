import arcpy
from arcpy import env
import os

'''
Calculates total area of selected land use classes and the ratio of the mentioned area to the area of calculation regions."
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
landUseLayer = arcpy.GetParameterAsText(2)
sql_express = arcpy.GetParameterAsText(3)

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
	
	# selects the proper polygons from land use layer and creates draf version of the zones_in layer
	arcpy.Select_analysis(zones_in,"calculationRegions")
	arcpy.Select_analysis(landUseLayer,"landUsePublic", sql_express)
	
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")
	
	# obtains the ID of the zone in which public spaces are located
	arcpy.Intersect_analysis(["calculationRegions","landUsePublic"], "landUse_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# calculates total area of public spaces in the calculation regions 
	arcpy.Dissolve_management("landUse_inters", "PublicInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# creates the new column with area of 'Public_spaces'
	arcpy.AddField_management("PublicInZones","TOTAL_AREA","FLOAT")
	arcpy.CalculateField_management("PublicInZones", "TOTAL_AREA", "[SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful calculation.")
	
	# adds column with calculated areas of public spaces within every calculation region
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PublicInZones","ZONE_ID", "TOTAL_AREA")

	# returns 0 if value is None 
	arcpy.CalculateField_management("calculationRegions", "TOTAL_AREA", "r(!TOTAL_AREA!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")

	# calculates the ratio of the public spaces area to the area of calculation regions
	arcpy.AddField_management("calculationRegions","Podil","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "Podil", "[TOTAL_AREA] / [SHAPE_Area] *100", "VB")

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

    
    
    


