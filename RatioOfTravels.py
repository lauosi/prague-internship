import arcpy
from arcpy import env
import os

'''
Calculates the Travel Ratio (TR considering different means of transport) for residents and employed in given zones
'''

zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
TABULKA = arcpy.GetParameterAsText(2)
ZSJ = arcpy.GetParameterAsText(3)
RESIDENTS = arcpy.GetParameterAsText(4)
EMPLOYED = arcpy.GetParameterAsText(5)

arcpy.env.overwriteOutput=True
meansOfTransportation = ['HD','IAD','kolo','pesi']
#env.workspace = "C:\\Esri\\temp_data.gdb" 
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
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions 
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
		
	# creates draf version of the ZSJ for home towns and work towns
	arcpy.Select_analysis(ZSJ,"RegionsHomeToSelect")
	arcpy.Select_analysis(ZSJ,"RegionsWorkToSelect")
	arcpy.AddMessage("Successful selection.")
	
	arcpy.AddMessage("Statistics analysis can take some time...")
	# creates flaten tables for HOME and for WORK
	arcpy.Statistics_analysis (TABULKA, "tabulka_home", [["VZDALENOST", "SUM"], ["CELKEM", "SUM"], ["Celkem_os_HD", "SUM"], ["Celkem_os_IAD", "SUM"], ["Celkem_os_kolo", "SUM"], ["Celkem_os_pesi", "SUM"]], "DOPR_ZSJDOP_KOD")
	arcpy.Statistics_analysis (TABULKA, "tabulka_work", [["VZDALENOST", "SUM"], ["CELKEM", "SUM"], ["Celkem_os_HD", "SUM"], ["Celkem_os_IAD", "SUM"], ["Celkem_os_kolo", "SUM"], ["Celkem_os_pesi", "SUM"]], "DOPR_ZSJDPS_KOD")
	arcpy.AddMessage("Successful calculation of values in the HOME and WORK tables.")
		
	# adds index to quickly locate the needed columns
	arcpy.AddIndex_management ("RegionsHomeToSelect", "KOD_ZSJ7", "codeIndex1")
	arcpy.AddIndex_management ("RegionsWorkToSelect", "KOD_ZSJ7", "codeIndex2")
	
	# IMPORTANT PART - joins ZSJ regions with the data table made by Matej (TABULKA)
	arcpy.AddMessage("Join can take some time...")
	arcpy.JoinField_management ("RegionsHomeToSelect", "KOD_ZSJ7", "tabulka_home", "DOPR_ZSJDOP_KOD", ["SUM_VZDALENOST", "SUM_CELKEM", "SUM_Celkem_os_HD", "SUM_Celkem_os_IAD", "SUM_Celkem_os_kolo", "SUM_Celkem_os_pesi"])
	arcpy.AddMessage("Successful join for HOME regions.")
	
	arcpy.JoinField_management ("RegionsWorkToSelect", "KOD_ZSJ7", "tabulka_work", "DOPR_ZSJDPS_KOD", ["SUM_VZDALENOST", "SUM_CELKEM", "SUM_Celkem_os_HD", "SUM_Celkem_os_IAD", "SUM_Celkem_os_kolo", "SUM_Celkem_os_pesi"])
	arcpy.AddMessage("Successful join for WORK regions.")
	
	# gets rid of <Null> values in distance field
	arcpy.CalculateField_management("RegionsHomeToSelect", "SUM_VZDALENOST", "r(!SUM_VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 
	arcpy.CalculateField_management("RegionsWorkToSelect", "SUM_VZDALENOST", "r(!SUM_VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	# uses only the rows with distance grater than 0
	arcpy.Select_analysis("RegionsHomeToSelect", "RegionsHome", "SUM_VZDALENOST > 0")
	arcpy.Select_analysis("RegionsWorkToSelect", "RegionsWork", "SUM_VZDALENOST > 0")
	arcpy.AddMessage("Successful selection of valid rows.")
	
	# gets rid of <Null> values in Regions Home and Regions Work
	arcpy.CalculateField_management("RegionsHome", "SUM_CELKEM", "r(!SUM_CELKEM!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("RegionsWork", "SUM_CELKEM", "r(!SUM_CELKEM!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	for mean in meansOfTransportation:
		arcpy.CalculateField_management("RegionsHome", "SUM_Celkem_os_"+mean, "r(!SUM_Celkem_os_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 	
		arcpy.CalculateField_management("RegionsWork", "SUM_Celkem_os_"+mean, "r(!SUM_Celkem_os_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 	 
	arcpy.AddMessage("Successful fields calculation.")
	
	#*************************************************************************************************************************************************************************************************START
	#calculates (new) number of people
	arcpy.AddField_management("RegionsHome","SUM_CELKEM_NEW","FLOAT")
	arcpy.CalculateField_management("RegionsHome", "SUM_CELKEM_NEW", "!SUM_Celkem_os_HD!+!SUM_Celkem_os_IAD!+!SUM_Celkem_os_kolo!+!SUM_Celkem_os_pesi!", "PYTHON_9.3")
	
	arcpy.AddField_management("RegionsWork","SUM_CELKEM_NEW","FLOAT")
	arcpy.CalculateField_management("RegionsWork", "SUM_CELKEM_NEW", "!SUM_Celkem_os_HD!+!SUM_Celkem_os_IAD!+!SUM_Celkem_os_kolo!+!SUM_Celkem_os_pesi!", "PYTHON_9.3")
	
	# calculates ratio of travels done by all kinds of transportation for residents and for employed
	for mean in meansOfTransportation:
		arcpy.AddField_management("RegionsHome","RES_Celkem_os_"+mean,"FLOAT")
		arcpy.CalculateField_management("RegionsHome", "RES_Celkem_os_"+mean, "!SUM_Celkem_os_"+mean+"!/!SUM_CELKEM_NEW!", "PYTHON_9.3")
		
		arcpy.AddField_management("RegionsWork","EMP_Celkem_os_"+mean,"FLOAT")
		arcpy.CalculateField_management("RegionsWork", "EMP_Celkem_os_"+mean, "!SUM_Celkem_os_"+mean+"!/!SUM_CELKEM_NEW!", "PYTHON_9.3")
	arcpy.AddMessage("Successful calculation of ratio of travels for residents and employed in ZSJ.")
	#*************************************************************************************************************************************************************************************************END
	
	# provides ID and divide areas
	arcpy.Intersect_analysis(["calculationRegions", "RegionsHome"], "RegionsHome_inters")
	arcpy.Intersect_analysis(["calculationRegions", "RegionsWork"], "RegionsWork_inters")
	arcpy.AddMessage("Successful intersection.")
	
	# calculates the number of residents in intersected zones
	arcpy.Intersect_analysis([RESIDENTS,"RegionsHome_inters"], "ResidentsInIntersected", "ALL", "0.1 METERS", "INPUT")
	
	# calculates the number of employed in intersected zones
	arcpy.Intersect_analysis([EMPLOYED,"RegionsWork_inters"], "EmployedInIntersected", "ALL", "0.1 METERS", "INPUT")
	arcpy.AddMessage("Successful intersection with RESIDENTS and EMPLOYED feature classes.")

	#*************************************************************************************************************************************************************************************************START
	for mean in meansOfTransportation:
		# sum the residents and employed for selected ratios
		arcpy.AddField_management("ResidentsInIntersected","RatioAndResidents_"+mean,"FLOAT")
		arcpy.CalculateField_management("ResidentsInIntersected", "RatioAndResidents_"+mean, "!RES_Celkem_os_"+mean+"!*!PTOTAL!", "PYTHON_9.3")
		arcpy.AddField_management("EmployedInIntersected","RatioAndEmployed_"+mean,"FLOAT")
		arcpy.CalculateField_management("EmployedInIntersected", "RatioAndEmployed_"+mean, "!EMP_Celkem_os_"+mean+"!*!prac!", "PYTHON_9.3")
	
	# sums up the ratios and number of residents/employed
	arcpy.Dissolve_management("ResidentsInIntersected", "RESIDENTSInZones", "ZONE_ID", "RatioAndResidents_HD SUM; RatioAndResidents_IAD SUM; RatioAndResidents_kolo SUM; RatioAndResidents_pesi SUM; PTOTAL SUM")
	arcpy.Dissolve_management("EmployedInIntersected", "EMPLOYEDInZones", "ZONE_ID", "RatioAndEmployed_HD SUM; RatioAndEmployed_IAD SUM; RatioAndEmployed_kolo SUM; RatioAndEmployed_pesi SUM; prac SUM")
	
	# calculates travel ratios for residents and employed
	for mean in meansOfTransportation:
		arcpy.AddField_management("RESIDENTSInZones", "TR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "TR_RESIDENTS_"+mean, "!SUM_RatioAndResidents_"+mean+"!/!SUM_PTOTAL!", "PYTHON_9.3")
		
		arcpy.AddField_management("EMPLOYEDInZones", "TR_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "TR_EMPLOYED_"+mean, "!SUM_RatioAndEmployed_"+mean+"!/!SUM_prac!", "PYTHON_9.3")
	arcpy.AddMessage("Successful calculation of Travel Ratios for Residents and Employed within given polygons.")
	#*************************************************************************************************************************************************************************************************END
	
	# adds new index to the calculationRegions so the joining fields management will work quicker
	arcpy.AddIndex_management("calculationRegions","ZONE_ID","codeIndexZ")
	
	#*************************************************************************************************************************************************************************************************START
	# adds the result columns with TRAVEL RATIOS for home and work to the RESULTS 
	arcpy.JoinField_management("calculationRegions","ZONE_ID","RESIDENTSInZones","ZONE_ID", ["TR_RESIDENTS_HD", "TR_RESIDENTS_IAD", "TR_RESIDENTS_kolo", "TR_RESIDENTS_pesi"])
	arcpy.JoinField_management("calculationRegions","ZONE_ID", "EMPLOYEDInZones","ZONE_ID", ["TR_EMPLOYED_HD", "TR_EMPLOYED_IAD", "TR_EMPLOYED_kolo", "TR_EMPLOYED_pesi"])
	
	arcpy.AddMessage("Successful fields addition.")
	
	# adds two new fields to check correctness of the calculations (if sum = 1 , the calculations are correct)
	arcpy.AddField_management("calculationRegions","ResRatioSUM","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "ResRatioSUM", "!TR_RESIDENTS_HD! + !TR_RESIDENTS_IAD! + !TR_RESIDENTS_kolo! + !TR_RESIDENTS_pesi!", "PYTHON_9.3")
	arcpy.AddField_management("calculationRegions","EmpRatioSUM","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "EmpRatioSUM", "!TR_EMPLOYED_HD! + !TR_EMPLOYED_IAD! + !TR_EMPLOYED_kolo! + !TR_EMPLOYED_pesi!", "PYTHON_9.3")
	#*************************************************************************************************************************************************************************************************END
	
	# gives the proper names to the output file
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
