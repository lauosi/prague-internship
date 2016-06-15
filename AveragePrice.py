import arcpy
from arcpy import env
import os

'''
Calculates the mean land price in given polygons
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
priceMap = arcpy.GetParameterAsText(2)

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
	
	# creates draf version of the zones_in and priceMap
	arcpy.Select_analysis(zones_in,"calculationRegions")
	arcpy.Select_analysis(priceMap,"priceMaptemp", "CENA !='N'")
	
	arcpy.AddMessage("Successful selection.")
	
	# adds new field PRICE with numeric fields (field CENA was a text field so it was impossible to do further calculations)
	arcpy.AddField_management("priceMaptemp","PRICE","FLOAT")
	arcpy.CalculateField_management("priceMaptemp", "PRICE", "[CENA]", "VB")

	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")

	# obtains the IDs of areas with particular price
	arcpy.Intersect_analysis(["calculationRegions","priceMaptemp"], "priceMap_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# calculates weight for every polygon in price map
	arcpy.AddField_management("priceMap_inters","PRICE_WEIGHTED","FLOAT")
	arcpy.CalculateField_management("priceMap_inters", "PRICE_WEIGHTED", "[PRICE] * [SHAPE_Area]", "VB")
	
	# prepares field AREA for further calculations (dissolve)
	arcpy.AddField_management("priceMap_inters","AREA","FLOAT")
	arcpy.CalculateField_management("priceMap_inters", "AREA", "[SHAPE_Area]", "VB")
	
	# sums up areas and prices, and calculates min and max price within each polygon
	arcpy.Dissolve_management("priceMap_inters", "PriceInZone", "ZONE_ID", "AREA SUM; PRICE_WEIGHTED SUM; PRICE MIN; PRICE MAX", "MULTI_PART", "DISSOLVE_LINES")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# adds field MEAN PRICE and calculates weighted mean price based on area 
	arcpy.AddField_management("PriceInZone","MEAN_PRICE","FLOAT")
	arcpy.CalculateField_management("PriceInZone", "MEAN_PRICE", "[SUM_PRICE_WEIGHTED]/[SUM_AREA]", "VB")
	
	arcpy.AddMessage("Successful calculation of mean price.")
	
	# adds column with PRICES to calculation regions
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PriceInZone","ZONE_ID", ["MEAN_PRICE", "MIN_PRICE", "MAX_PRICE"])

	# returns 0 if value is None 
	#arcpy.CalculateField_management("calculationRegions", "MEAN_PRICE", "r(!MEAN_PRICE!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	arcpy.AlterField_management("calculationRegions", "MIN_PRICE", "MinCena", "MinCena")
	arcpy.AlterField_management("calculationRegions", "MAX_PRICE", "MaxCena", "MaxCena")
	arcpy.AlterField_management("calculationRegions", "MEAN_PRICE", "PrumCena", "PrumCena")

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
    
    
