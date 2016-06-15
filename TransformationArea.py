import arcpy
from arcpy import env
import os

'''
Calculates the area of transition zones (PromenaPlocha), number of new inhabitants (Novi_Bydlici), number of
new workers (Novi_Pracujici), new gross floor area (Nova_HPP) in the calculation regions 
and the ratio (PromenaPlochaRatio) of the area of transition zones (PromenaPlocha) to the area of calculation regions.
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
transArea = arcpy.GetParameterAsText(2)

#transArea = ''
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

	# creates draf version of the zones_in feature class and transArea
	arcpy.Select_analysis(zones_in,"calculationRegions")
	arcpy.Select_analysis(transArea,"transArea_temp")
		
	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	# stores the area of transformation zones before intersection
	arcpy.AddField_management("transArea_temp","Area_factor","FLOAT")
	arcpy.CalculateField_management("transArea_temp", "Area_factor", "[SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful field addition.")
	
	# connects zones ID with proper polygons of transformation areas
	arcpy.Intersect_analysis(["calculationRegions", "transArea_temp" ], "transArea_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# calculates the factor which will be used to establish number of new inhabitants, new workers and new gross floor area in the calculation zones
	arcpy.AddField_management("transArea_inters","factor","FLOAT")
	arcpy.CalculateField_management("transArea_inters", "factor", "[SHAPE_Area] / [Area_factor]", "VB")
	
	#calculates the number of new inhabitants, new workers and new gross floor area for every polygon after intersection
	arcpy.AddField_management("transArea_inters","new_inhabitants","LONG")
	arcpy.CalculateField_management("transArea_inters", "new_inhabitants", "[R_NARUST]*[factor]", "VB")
	
	arcpy.AddField_management("transArea_inters","new_workers","LONG")
	arcpy.CalculateField_management("transArea_inters", "new_workers", "[P_NARUST]*[factor]", "VB")
	
	arcpy.AddField_management("transArea_inters","new_grossarea","LONG")
	arcpy.CalculateField_management("transArea_inters", "new_grossarea", "[HPP_NARUST]*[factor]", "VB")
	
	arcpy.AddMessage("Successful calculation of the proportion.")
	
	# calculates total area of transformation zones, number of new inhabitants and workers, and new gross floor area in the calculation regions 
	arcpy.Dissolve_management("transArea_inters", "TransInZones", "ZONE_ID", "new_inhabitants SUM; new_workers SUM; new_grossarea SUM", "MULTI_PART", "DISSOLVE_LINES")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# creates the new columns with area of transformation zones within calculation zones
	arcpy.AddField_management("TransInZones","PromenaPlocha","FLOAT")
	arcpy.CalculateField_management("TransInZones", "PromenaPlocha", "[SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful field addition.")
	
	# changes field names for proper ones 
	arcpy.AlterField_management("TransInZones", "SUM_new_inhabitants", "Novi_Bydlici")
	arcpy.AlterField_management("TransInZones", "SUM_new_workers", "Novi_Pracujici")
	arcpy.AlterField_management("TransInZones", "SUM_new_grossarea", "Nova_HPP")
	
	arcpy.AddMessage("Successful alteration of fields names.")
	
	# adds field 'PromenaPlocha'to calculation regions
	arcpy.JoinField_management("calculationRegions","ZONE_ID","TransInZones","ZONE_ID", ["PromenaPlocha", "Novi_Bydlici", "Novi_Pracujici", "Nova_HPP"])
	
	# returns 0 if value is None 
	arcpy.CalculateField_management("calculationRegions", "PromenaPlocha", "r(!PromenaPlocha!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")

	# calculates the ratio of the area of transformation zones to the area of calculation regions
	arcpy.AddField_management("calculationRegions","PodilPromenaPlocha","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilPromenaPlocha", "[PromenaPlocha] / [SHAPE_Area]", "VB")
		
	arcpy.AddMessage("Successful field addition.")
	
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
    
    
