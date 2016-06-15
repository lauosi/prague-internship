import arcpy
from arcpy import env
import os

'''
Calculates the area of properties owned by public sector and owned by the City of Prague witihin selected polygons and counts the ratio the mentioned areas to the area of calculation regions
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
ownership = arcpy.GetParameterAsText(2)
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

	# creates draf version of the zones_in feature class and selects the polygons with properties owned by public sector and by the City of Prague 
	arcpy.Select_analysis(zones_in,"calculationRegions")
	
	arcpy.Select_analysis(ownership,"ownPublic", "KATVL IN ( 2101, 2104, 2204, 1001, 1002, 1003, 1004, 1006, 7101, 1201, 2204, 1301, 1303 )")
	arcpy.Select_analysis(ownership,"ownPrague", "KATVL IN ( 2101, 2104, 2204 )")
	
	#arcpy.Select_analysis(ownership,"ownPublic", "TRIDAVL IN ('ČR včetně státem ovládaných subjektů', 'Hl.m. Praha včetně jím ovládaných subjektů bez MČ' , 'Kraje ČR mimo hl.m. Prahu včetně jimi ovládaných subjektů' , 'Městské části hl.m. Prahy včetně jimi ovládaných subjektů' , 'Obce ČR mimo hl.m. Prahu včetně jimi ovládaných subjektů' )")
	#arcpy.Select_analysis(ownership,"ownPrague", "TRIDAVL IN ('Hl.m. Praha včetně jím ovládaných subjektů bez MČ' , 'Městské části hl.m. Prahy včetně jimi ovládaných subjektů' )")
	
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")
	
	# connects zones ID with proper polygons of ownPublic and ownPrague feature classes
	arcpy.Intersect_analysis(["calculationRegions","ownPublic"], "ownPublic_inters", "ALL", "0.1 METERS", "INPUT")
	arcpy.Intersect_analysis(["calculationRegions","ownPrague"], "ownPrague_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# calculates total area of properties owned by public sector and by the City of Prague in the calculation regions 
	arcpy.Dissolve_management("ownPublic_inters", "PublicInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	arcpy.Dissolve_management("ownPrague_inters", "PragueInZones", "ZONE_ID", "", "MULTI_PART", "DISSOLVE_LINES")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# creates the new columns with areas of properties owned by public sector & by the City of Prague
	arcpy.AddField_management("PublicInZones","OwnedByPublic","FLOAT")
	arcpy.CalculateField_management("PublicInZones", "OwnedByPublic", "[SHAPE_Area]", "VB")
	arcpy.AddField_management("PragueInZones","OwnedByPrague","FLOAT")
	arcpy.CalculateField_management("PragueInZones", "OwnedByPrague", "[SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful field addition.")
	
	# adds field 'OwnedByPublic' and 'OwnedByPrague'to calculation regions
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PublicInZones","ZONE_ID", "OwnedByPublic")
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PragueInZones","ZONE_ID", "OwnedByPrague")

	# returns 0 if value is None 
	arcpy.CalculateField_management("calculationRegions", "OwnedByPublic", "r(!OwnedByPublic!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("calculationRegions", "OwnedByPrague", "r(!OwnedByPrague!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	# calculates the ratio of the areas owned by the public sector to the area of calculation regions
	arcpy.AddField_management("calculationRegions","RatioOwnPublic","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "RatioOwnPublic", "[OwnedByPublic] / [SHAPE_Area]", "VB")
	
	# calculates the ratio of the areas owned by the City of Prague to the area of calculation regions
	arcpy.AddField_management("calculationRegions","RatioOwnPrague","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "RatioOwnPrague", "[OwnedByPrague] / [SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "OwnedByPrague", "VlastnenoPrahou", "VlastnenoPrahou")
	arcpy.AlterField_management("calculationRegions", "RatioOwnPrague", "PodilVlastPrahou", "PodilVlastPrahou")
	arcpy.AlterField_management("calculationRegions", "OwnedByPublic", "VlastnenoVerSektorem", "VlastnenoVerSektorem")
	arcpy.AlterField_management("calculationRegions", "RatioOwnPublic", "PodilVlastVerSekt", "PodilVlastVerSekt")
	
	arcpy.AddMessage("Successful calculations.")
	
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
    
    
