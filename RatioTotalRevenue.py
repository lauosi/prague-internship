import arcpy
from arcpy import env
import os

'''
Calculates the Ratio of Total Revenue Passenger Kilometers (osobokm) done by different means of transport for residents and employed in given zones
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
	arcpy.Statistics_analysis (TABULKA, "tabulka_home", [["VZDALENOST", "SUM"], ["Osobokm_celkem", "SUM"], ["Osobokm_HD", "SUM"], ["Osobokm_IAD", "SUM"], ["Osobokm_kolo", "SUM"], ["Osobokm_pesi", "SUM"],["CELKEM", "SUM"]], "DOPR_ZSJDOP_KOD")
	arcpy.Statistics_analysis (TABULKA, "tabulka_work", [["VZDALENOST", "SUM"], ["Osobokm_celkem", "SUM"], ["Osobokm_HD", "SUM"], ["Osobokm_IAD", "SUM"], ["Osobokm_kolo", "SUM"], ["Osobokm_pesi", "SUM"],["CELKEM", "SUM"]], "DOPR_ZSJDPS_KOD")
	arcpy.AddMessage("Successful calculation of values in the HOME and WORK tables.")
		
	# adds index to quickly locate the needed columns
	arcpy.AddIndex_management ("RegionsHomeToSelect", "KOD_ZSJ7", "codeIndex1")
	arcpy.AddIndex_management ("RegionsWorkToSelect", "KOD_ZSJ7", "codeIndex2")
	
	# IMPORTANT PART - joins ZSJ regions with the data table made by Matej (TABULKA)
	arcpy.AddMessage("Join can take some time...")
	arcpy.JoinField_management ("RegionsHomeToSelect", "KOD_ZSJ7", "tabulka_home", "DOPR_ZSJDOP_KOD", ["SUM_VZDALENOST", "SUM_Osobokm_celkem", "SUM_Osobokm_HD", "SUM_Osobokm_IAD", "SUM_Osobokm_kolo", "SUM_Osobokm_pesi", "SUM_CELKEM"])
	arcpy.AddMessage("Successful join for HOME regions.")
	
	arcpy.JoinField_management ("RegionsWorkToSelect", "KOD_ZSJ7", "tabulka_work", "DOPR_ZSJDPS_KOD", ["SUM_VZDALENOST", "SUM_Osobokm_celkem", "SUM_Osobokm_HD", "SUM_Osobokm_IAD", "SUM_Osobokm_kolo", "SUM_Osobokm_pesi", "SUM_CELKEM"])
	arcpy.AddMessage("Successful join for WORK regions.")
	
	# gets rid of <Null> values in distance field
	arcpy.CalculateField_management("RegionsHomeToSelect", "SUM_VZDALENOST", "r(!SUM_VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 
	arcpy.CalculateField_management("RegionsWorkToSelect", "SUM_VZDALENOST", "r(!SUM_VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	# uses only the rows with distance grater than 0
	arcpy.Select_analysis("RegionsHomeToSelect", "RegionsHome", "SUM_VZDALENOST > 0")
	arcpy.Select_analysis("RegionsWorkToSelect", "RegionsWork", "SUM_VZDALENOST > 0")
	arcpy.AddMessage("Successful selection of valid rows.")
	
	# gets rid of <Null> values in Regions Home and Regions Work
	arcpy.CalculateField_management("RegionsHome", "SUM_Osobokm_celkem", "r(!SUM_Osobokm_celkem!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("RegionsWork", "SUM_Osobokm_celkem", "r(!SUM_Osobokm_celkem!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	for mean in meansOfTransportation:
		arcpy.CalculateField_management("RegionsHome", "SUM_Osobokm_"+mean, "r(!SUM_Osobokm_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
		arcpy.CalculateField_management("RegionsWork", "SUM_Osobokm_"+mean, "r(!SUM_Osobokm_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
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
	arcpy.AddField_management("ResidentsInIntersected","RevenueResidents_TOTAL","FLOAT")
	arcpy.CalculateField_management("ResidentsInIntersected", "RevenueResidents_TOTAL", "!SUM_Osobokm_celkem!*!PTOTAL!", "PYTHON_9.3")
	arcpy.AddField_management("EmployedInIntersected","RevenueEmployed_TOTAL","FLOAT")
	arcpy.CalculateField_management("EmployedInIntersected", "RevenueEmployed_TOTAL", "!SUM_Osobokm_celkem!*!prac!", "PYTHON_9.3")
	
	for mean in meansOfTransportation:
		# sum the residents and employed for selected ratios
		arcpy.AddField_management("ResidentsInIntersected","RevenueResidents_"+mean,"FLOAT")
		arcpy.CalculateField_management("ResidentsInIntersected", "RevenueResidents_"+mean, "!SUM_Osobokm_"+mean+"!*!PTOTAL!", "PYTHON_9.3")
		arcpy.AddField_management("EmployedInIntersected","RevenueEmployed_"+mean,"FLOAT")
		arcpy.CalculateField_management("EmployedInIntersected", "RevenueEmployed_"+mean, "!SUM_Osobokm_"+mean+"!*!prac!", "PYTHON_9.3")
	
	# sums up the ratios and number of residents/employed
	arcpy.Dissolve_management("ResidentsInIntersected", "RESIDENTSInZones", "ZONE_ID", "RevenueResidents_TOTAL SUM; RevenueResidents_HD SUM; RevenueResidents_IAD SUM; RevenueResidents_kolo SUM; RevenueResidents_pesi SUM; PTOTAL SUM")
	arcpy.Dissolve_management("EmployedInIntersected", "EMPLOYEDInZones", "ZONE_ID", "RevenueEmployed_TOTAL SUM; RevenueEmployed_HD SUM; RevenueEmployed_IAD SUM; RevenueEmployed_kolo SUM; RevenueEmployed_pesi SUM; prac SUM")
	
	# calculates travel ratios for residents and employed
	arcpy.AddField_management("RESIDENTSInZones", "RPR_RESIDENTS_TOTAL","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RESIDENTS_TOTAL", "!SUM_RevenueResidents_TOTAL!/!SUM_PTOTAL!", "PYTHON_9.3")
	arcpy.AddField_management("EMPLOYEDInZones", "RPR_EMPLOYED_TOTAL","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "RPR_EMPLOYED_TOTAL", "!SUM_RevenueEmployed_TOTAL!/!SUM_prac!", "PYTHON_9.3")
		
	for mean in meansOfTransportation:
		arcpy.AddField_management("RESIDENTSInZones", "RPR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RESIDENTS_"+mean, "!SUM_RevenueResidents_"+mean+"!/!SUM_PTOTAL!", "PYTHON_9.3")
		
		arcpy.AddField_management("EMPLOYEDInZones", "RPR_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "RPR_EMPLOYED_"+mean, "!SUM_RevenueEmployed_"+mean+"!/!SUM_prac!", "PYTHON_9.3")
	arcpy.AddMessage("Successful calculation of Revenue Passenger Kilometers Total for Residents and Employed within given polygons.")

	arcpy.AddField_management("RESIDENTSInZones", "RPR_RES_SUM","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RES_SUM", "!RPR_RESIDENTS_HD!+!RPR_RESIDENTS_IAD!+!RPR_RESIDENTS_kolo!+!RPR_RESIDENTS_pesi!", "PYTHON_9.3")
	arcpy.AddField_management("RESIDENTSInZones", "RPR_RESIDENTS_OTHER","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RESIDENTS_OTHER", "!RPR_RESIDENTS_TOTAL! - !RPR_RES_SUM!", "PYTHON_9.3")
	
	arcpy.AddField_management("EMPLOYEDInZones", "RPR_EMP_SUM","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "RPR_EMP_SUM", "!RPR_EMPLOYED_HD!+!RPR_EMPLOYED_IAD!+!RPR_EMPLOYED_kolo!+!RPR_EMPLOYED_pesi!", "PYTHON_9.3")
	arcpy.AddField_management("EMPLOYEDInZones", "RPR_EMPLOYED_OTHER","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "RPR_EMPLOYED_OTHER", "!RPR_EMPLOYED_TOTAL! - !RPR_EMP_SUM!", "PYTHON_9.3")
	
	for mean in meansOfTransportation:
		arcpy.AddField_management("RESIDENTSInZones", "RTR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "RTR_RESIDENTS_"+mean, "!RPR_RESIDENTS_"+mean+"!/!RPR_RESIDENTS_TOTAL!*100", "PYTHON_9.3")
		arcpy.AddField_management("EMPLOYEDInZones", "RTR_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "RTR_EMPLOYED_"+mean, "!RPR_EMPLOYED_"+mean+"!/!RPR_EMPLOYED_TOTAL!*100", "PYTHON_9.3")
	arcpy.AddMessage("Successful calculation of Revenue Passenger Kilometers Total for Residents and Employed within given polygons.")
	
	arcpy.AddField_management("RESIDENTSInZones", "RTR_RESIDENTS_OTHER","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "RTR_RESIDENTS_OTHER", "!RPR_RESIDENTS_OTHER!/!RPR_RESIDENTS_TOTAL!*100", "PYTHON_9.3")
	arcpy.AddField_management("EMPLOYEDInZones", "RTR_EMPLOYED_OTHER","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "RTR_EMPLOYED_OTHER", "!RPR_EMPLOYED_OTHER!/!RPR_EMPLOYED_TOTAL!*100", "PYTHON_9.3")
	#*************************************************************************************************************************************************************************************************END
	
	# adds new index to the calculationRegions so the joining fields management will work quicker
	arcpy.AddIndex_management("calculationRegions","ZONE_ID","codeIndexZone")
	
	#*************************************************************************************************************************************************************************************************START
	# adds the result columns with TRAVEL RATIOS for home and work to the RESULTS 
	arcpy.JoinField_management("calculationRegions","ZONE_ID","RESIDENTSInZones","ZONE_ID", ["RPR_RESIDENTS_TOTAL", "RPR_RESIDENTS_OTHER", "RPR_RESIDENTS_HD", "RPR_RESIDENTS_IAD", "RPR_RESIDENTS_kolo", "RPR_RESIDENTS_pesi", "RTR_RESIDENTS_OTHER", "RTR_RESIDENTS_HD", "RTR_RESIDENTS_IAD", "RTR_RESIDENTS_kolo", "RTR_RESIDENTS_pesi"])
	arcpy.JoinField_management("calculationRegions","ZONE_ID", "EMPLOYEDInZones","ZONE_ID", ["RPR_EMPLOYED_TOTAL", "RPR_EMPLOYED_OTHER", "RPR_EMPLOYED_HD", "RPR_EMPLOYED_IAD", "RPR_EMPLOYED_kolo", "RPR_EMPLOYED_pesi", "RTR_EMPLOYED_OTHER", "RTR_EMPLOYED_HD", "RTR_EMPLOYED_IAD", "RTR_EMPLOYED_kolo", "RTR_EMPLOYED_pesi"])
	
	# SUM RTR TO CHECK!
	arcpy.AddField_management("calculationRegions", "RTR_RE_100","LONG")
	arcpy.CalculateField_management("calculationRegions", "RTR_RE_100", "!RTR_RESIDENTS_OTHER!+!RTR_RESIDENTS_HD!+!RTR_RESIDENTS_IAD!+!RTR_RESIDENTS_kolo!+!RTR_RESIDENTS_pesi!", "PYTHON_9.3")
	arcpy.AddField_management("calculationRegions", "RTR_EM_100","LONG")
	arcpy.CalculateField_management("calculationRegions", "RTR_EM_100", "!RTR_EMPLOYED_OTHER!+!RTR_EMPLOYED_HD!+!RTR_EMPLOYED_IAD!+!RTR_EMPLOYED_kolo!+!RTR_EMPLOYED_pesi!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful fields addition.")
	#*************************************************************************************************************************************************************************************************END
	
	# gives the proper names to the output file
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
