import arcpy
from arcpy import env
import os

'''
Calculates the typical, minimum and maxiumum number of stories for buildings in selected zones.

'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
INPUTbuildingHeights = arcpy.GetParameterAsText(2)
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
	
	# creates draf version of the zones_in feature class
	arcpy.Select_analysis(zones_in,"calculationRegions")
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	# selects grids where typical number of stories is greater than 0
	arcpy.Select_analysis(INPUTbuildingHeights, "buildHeight", "podlaz_MOD > 0")
	arcpy.AddMessage("Successful selection.")
	
	# adds an calculation regions IDs to the buildHeight table
	arcpy.Intersect_analysis(["calculationRegions", "buildHeight"], "buildHeight_inters")
	arcpy.AddMessage("Successful intersection.")
	
	# summarize the area of buildings with typical number of stores within zones
	arcpy.Dissolve_management("buildHeight_inters", "buildHeightInZone",["ZONE_ID","podlaz_MOD"],[["Shape_Area","SUM"]])	
	arcpy.AddMessage("Successful dissolution.")
	
	# sorts list using area to find the most common number of stories for every zone
	arcpy.Sort_management("buildHeightInZone", "typicalSORTED", [["SUM_Shape_Area", "DESCENDING"]])
	arcpy.Dissolve_management("typicalSORTED", "typicalSORTED_DISS", ["ZONE_ID"], [["podlaz_MOD","FIRST"]])
	arcpy.AlterField_management("typicalSORTED_DISS","FIRST_podlaz_MOD","TypickaPodlaznost","TypickaPodlaznost")
	arcpy.AddMessage("Successful acquirement of typical numbers of stories.")
	
	# sorts list using the typical number of stories to find the lowest and the highest number of stories
	arcpy.Sort_management("buildHeightInZone", "minmaxSORTED", [["podlaz_MOD", "ASCENDING"]])
	arcpy.Dissolve_management("minmaxSORTED", "minmaxSORTED_DISS",["ZONE_ID"],[["podlaz_MOD","FIRST"],["podlaz_MOD","LAST"]])
	arcpy.AlterField_management("minmaxSORTED_DISS","FIRST_podlaz_MOD","MinimalniPodlaznost", "MinimalniPodlaznost")
	arcpy.AlterField_management("minmaxSORTED_DISS","LAST_podlaz_MOD","MaximalniPodlaznost", "MaximalniPodlaznost")
	arcpy.JoinField_management("calculationRegions", "ZONE_ID", "typicalSORTED_DISS", "ZONE_ID", ["TypickaPodlaznost"])
	arcpy.JoinField_management("calculationRegions", "ZONE_ID", "minmaxSORTED_DISS", "ZONE_ID", ["MinimalniPodlaznost","MaximalniPodlaznost"])
	arcpy.AddMessage("Successful acquirement of minimum and maximum numbers of stories.")
	
	# gives the proper name to the output file
	arcpy.Select_analysis("calculationRegions", results)
	arcpy.AddMessage("Your feature class was successfully created: {0}".format(results))
	
	# clean this mess up
	arcpy.Delete_management(TEMP)
	arcpy.AddMessage("Temporary directory was deleted.")
	arcpy.AddMessage("Thank you for using Help Tools, have a nice day. <('')")

except arcpy.ExecuteError:
	msgs1 = arcpy.GetMessages(1)
	arcpy.AddError(msgs1)
	msgs2 = arcpy.GetMessages(2)
	arcpy.AddError(msgs2)
	
except:
    arcpy.AddError("Operation failed. Your feature class was not created.") 
