import arcpy
from arcpy import env
import os

'''
bez usuniecia dystansu < 0


Calculates the Average Travel Distance (ATD - total and considering different means of transport) for residents and employed in given zones

Calculates the Travel Ratio (TR considering different means of transport) for residents and employed in given zones

Calculates the Ratio of Total Revenue Passenger Kilometers (osobokm) done by different means of transport for residents and employed in given zones
'''

zones_in = arcpy.GetParameterAsText(0)
rings_in = arcpy.GetParameterAsText(1)
results = arcpy.GetParameterAsText(2)
TABULKA = arcpy.GetParameterAsText(3)
ZSJ = arcpy.GetParameterAsText(4)
RESIDENTS = arcpy.GetParameterAsText(5)
EMPLOYED = arcpy.GetParameterAsText(6)

#*************************************************START helper*************************************************
#  Join Field
# -*- coding: utf-8 -*-
#
#  A faster Join Field tool
#
#  Esri, November 2015

# Define generator for join data
def joindataGen(joinTable,fieldList,sortField):
    with arcpy.da.SearchCursor(joinTable,fieldList,sql_clause=['DISTINCT',
                                                               'ORDER BY '+sortField]) as cursor:
        for row in cursor:
            yield row

# Function for progress reporting
def percentile(n,pct):
    return int(float(n)*float(pct)/100.0)

def joinFieldImported(inTable, inJoinField, joinTable, outJoinField, joinFields):
	# Add join fields
	arcpy.AddMessage('\nAdding join fields...')
	fList = [f for f in arcpy.ListFields(joinTable) if f.name in joinFields.split(';')]
	for i in range(len(fList)):
		name = fList[i].name
		type = fList[i].type
		if type in ['Integer','OID']:
			arcpy.AddField_management(inTable,name,field_type='LONG')
		elif type == 'String':
			arcpy.AddField_management(inTable,name,field_type='TEXT',field_length=fList[i].length)
		elif type == 'Double':
			arcpy.AddField_management(inTable,name,field_type='DOUBLE')
		elif type == 'Date':
			arcpy.AddField_management(inTable,name,field_type='DATE')
		else:
			arcpy.AddError('\nUnknown field type: {0} for field: {1}'.format(type,name))

	# Write values to join fields
	arcpy.AddMessage('\nJoining data...')
	# Create generator for values
	fieldList = [outJoinField] + joinFields.split(';')
	joinDataGen = joindataGen(joinTable,fieldList,outJoinField)
	version = sys.version_info[0]
	if version == 2:
		joinTuple = joinDataGen.next()
	else:
		joinTuple = next(joinDataGen)
	# 
	fieldList = [inJoinField] + joinFields.split(';')
	count = int(arcpy.GetCount_management(inTable).getOutput(0))
	breaks = [percentile(count,b) for b in range(10,100,10)]
	j = 0
	with arcpy.da.UpdateCursor(inTable,fieldList,sql_clause=(None,'ORDER BY '+inJoinField)) as cursor:
		for row in cursor:
			j+=1
			if j in breaks:
				arcpy.AddMessage(str(int(round(j*100.0/count))) + ' percent complete...')
			row = list(row)
			key = row[0]
			try:
				while joinTuple[0] < key:
					if version == 2:
						joinTuple = joinDataGen.next()
					else:
						joinTuple = next(joinDataGen)
				if key == joinTuple[0]:
					for i in range(len(joinTuple))[1:]:
						row[i] = joinTuple[i]
					row = tuple(row)
					cursor.updateRow(row)
			except StopIteration:
				arcpy.AddWarning('\nEnd of join table.')
				break

	arcpy.SetParameter(5,inTable)
	arcpy.AddMessage('\nDone.')
#*************************************************END helper*************************************************

arcpy.env.overwriteOutput=True
meansOfTransportation = ['HD','IAD','kolo','pesi']
KODNAZEV = [1, 2, 3, 4]
numRing = ["0", "1", "2", "3", "4"]	


#env.workspace = "C:\\Esri\\temp_data.gdb"

# start the script
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
	# creates draf version of the ZSJ for home towns and work towns
	arcpy.Select_analysis(ZSJ,"RegionsHome")
	arcpy.Select_analysis(ZSJ,"RegionsWork")
	# creates draf version of the ProstPasmaMesta feature class
	arcpy.Select_analysis(rings_in,"pasmaMesta")
	# copy the table for adding rings
	arcpy.TableSelect_analysis(TABULKA, "TABULKA")
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions 
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	#***
	# ading an information about the ring to each ZSJ
	arcpy.MakeFeatureLayer_management ("pasmaMesta", "pasmaMesta_view")
	arcpy.MakeFeatureLayer_management ("RegionsHome", "ZSJ_COPY")
	arcpy.AddField_management("ZSJ_COPY","NoRing","LONG")
	arcpy.AddMessage("Successful layer creation.")
	
	for kod in KODNAZEV:
		arcpy.SelectLayerByAttribute_management ("pasmaMesta_view", "NEW_SELECTION", "KODNAZEV = "+str(kod))
		arcpy.SelectLayerByLocation_management ("ZSJ_COPY", "HAVE_THEIR_CENTER_IN", "pasmaMesta_view")
		arcpy.CalculateField_management("ZSJ_COPY", "NoRing", kod, "PYTHON_9.3")
		arcpy.SelectLayerByAttribute_management ("ZSJ_COPY", "CLEAR_SELECTION")
	arcpy.Delete_management ("ZSJ_COPY")
	arcpy.AddMessage("Successful ring num addidtion.")
	
	joinFieldImported("TABULKA", "DOPR_ZSJDPS_KOD", "RegionsHome", "KOD_ZSJ7", "NoRing")
	arcpy.AddMessage("Successful join.")
	
	# adds 0 to rows that are outside the city rings
	arcpy.CalculateField_management("TABULKA", "NoRing", "r(!NoRing!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	#***
	arcpy.AddMessage("Statistics analysis can take some time...")
	
	arcpy.Statistics_analysis ("TABULKA", "tabulkaToPivot", [["CELKEM", "SUM"]], ["DOPR_ZSJDOP_KOD", "NoRing"])
	arcpy.AddMessage("Successful calculation of pivot table.")
	
	# pivoting the table to get total number of people working in every ring
	arcpy.PivotTable_management ("tabulkaToPivot", "DOPR_ZSJDOP_KOD", "NoRing", "SUM_CELKEM", "pivot_TOTAL")
	arcpy.AddMessage("Successful pivoting.")
	
	# creates flaten tables for HOME and for WORK
	arcpy.Statistics_analysis (TABULKA, "tabulka_home", [["VZDALENOST", "SUM"], ["Osobokm_celkem", "SUM"], ["Osobokm_HD", "SUM"], ["Osobokm_IAD", "SUM"], ["Osobokm_kolo", "SUM"], ["Osobokm_pesi", "SUM"],["CELKEM", "SUM"], ["Celkem_os_HD", "SUM"], ["Celkem_os_IAD", "SUM"], ["Celkem_os_kolo", "SUM"], ["Celkem_os_pesi", "SUM"]], "DOPR_ZSJDOP_KOD")
	arcpy.Statistics_analysis (TABULKA, "tabulka_work", [["VZDALENOST", "SUM"], ["Osobokm_celkem", "SUM"], ["Osobokm_HD", "SUM"], ["Osobokm_IAD", "SUM"], ["Osobokm_kolo", "SUM"], ["Osobokm_pesi", "SUM"],["CELKEM", "SUM"], ["Celkem_os_HD", "SUM"], ["Celkem_os_IAD", "SUM"], ["Celkem_os_kolo", "SUM"], ["Celkem_os_pesi", "SUM"]], "DOPR_ZSJDPS_KOD")
	arcpy.AddMessage("Successful calculation of values in the HOME and WORK tables.")
	
	joinFieldImported("RegionsHome", "KOD_ZSJ7", "pivot_TOTAL", "DOPR_ZSJDOP_KOD", "NoRing0;NoRing1;NoRing2;NoRing3;NoRing4")
	arcpy.AddMessage("Successful join fields from pivoted table.")
	joinFieldImported ("RegionsHome", "KOD_ZSJ7", "tabulka_home", "DOPR_ZSJDOP_KOD", "SUM_VZDALENOST;SUM_Osobokm_celkem;SUM_Osobokm_HD;SUM_Osobokm_IAD;SUM_Osobokm_kolo;SUM_Osobokm_pesi;SUM_CELKEM;SUM_Celkem_os_HD;SUM_Celkem_os_IAD;SUM_Celkem_os_kolo;SUM_Celkem_os_pesi")
	arcpy.AddMessage("Successful join fields for home regions.")
	joinFieldImported ("RegionsWork", "KOD_ZSJ7", "tabulka_work", "DOPR_ZSJDPS_KOD", "SUM_VZDALENOST;SUM_Osobokm_celkem;SUM_Osobokm_HD;SUM_Osobokm_IAD;SUM_Osobokm_kolo;SUM_Osobokm_pesi;SUM_CELKEM;SUM_Celkem_os_HD;SUM_Celkem_os_IAD;SUM_Celkem_os_kolo;SUM_Celkem_os_pesi")
	arcpy.AddMessage("Successful join fields for work regions.")
	
	# gets rid of <Null> values in distance field
	#arcpy.CalculateField_management("RegionsHomeToSelect", "SUM_VZDALENOST", "r(!SUM_VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 
	#arcpy.CalculateField_management("RegionsWorkToSelect", "SUM_VZDALENOST", "r(!SUM_VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	# uses only the rows with distance grater than 0
	#arcpy.Select_analysis("RegionsHomeToSelect", "RegionsHome", "SUM_VZDALENOST > 0")
	#arcpy.Select_analysis("RegionsWorkToSelect", "RegionsWork", "SUM_VZDALENOST > 0")
	arcpy.AddMessage("Successful selection of valid rows.")
	
	# gets rid of <Null> values in Regions Home and Regions Work
	arcpy.CalculateField_management("RegionsHome", "SUM_Osobokm_celkem", "r(!SUM_Osobokm_celkem!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("RegionsHome", "SUM_CELKEM", "r(!SUM_CELKEM!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("RegionsWork", "SUM_Osobokm_celkem", "r(!SUM_Osobokm_celkem!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("RegionsWork", "SUM_CELKEM", "r(!SUM_CELKEM!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	# gets rid of <Null> values in Regions Home and Regions Work for all mean of transportation from the list
	for mean in meansOfTransportation:
		arcpy.CalculateField_management("RegionsHome", "SUM_Celkem_os_"+mean, "r(!SUM_Celkem_os_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 
		arcpy.CalculateField_management("RegionsHome", "SUM_Osobokm_"+mean, "r(!SUM_Osobokm_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
		arcpy.CalculateField_management("RegionsWork", "SUM_Celkem_os_"+mean, "r(!SUM_Celkem_os_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 
		arcpy.CalculateField_management("RegionsWork", "SUM_Osobokm_"+mean, "r(!SUM_Osobokm_"+mean+"!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.AddMessage("Successful field calculations.")
	
	#*************************************************************************************************************************************************************************************************
	
	# calculates AverageTD_ZSJ_H (Average Travel Distance for every zone in ZSJ for home zones)
	arcpy.AddField_management("RegionsHome","AverageTD_ZSJ_H","FLOAT")
	arcpy.CalculateField_management("RegionsHome", "AverageTD_ZSJ_H", "!SUM_Osobokm_celkem!/!SUM_CELKEM!", "PYTHON_9.3")
	
	# calculates AverageTD_ZSJ_W (Average Travel Distance for every zone in ZSJ for work zones)
	arcpy.AddField_management("RegionsWork","AverageTD_ZSJ_W","FLOAT")
	arcpy.CalculateField_management("RegionsWork", "AverageTD_ZSJ_W", "!SUM_Osobokm_celkem!/!SUM_CELKEM!", "PYTHON_9.3")
	#calculates (new) number of people
	arcpy.AddField_management("RegionsHome","SUM_CELKEM_NEW","FLOAT")
	arcpy.CalculateField_management("RegionsHome", "SUM_CELKEM_NEW", "!SUM_Celkem_os_HD!+!SUM_Celkem_os_IAD!+!SUM_Celkem_os_kolo!+!SUM_Celkem_os_pesi!", "PYTHON_9.3")
	arcpy.AddField_management("RegionsWork","SUM_CELKEM_NEW","FLOAT")
	arcpy.CalculateField_management("RegionsWork", "SUM_CELKEM_NEW", "!SUM_Celkem_os_HD!+!SUM_Celkem_os_IAD!+!SUM_Celkem_os_kolo!+!SUM_Celkem_os_pesi!", "PYTHON_9.3")

	for mean in meansOfTransportation:
		#calculates Average Travel Distance for every zone in ZSJ for home zones and work zones
		arcpy.AddField_management("RegionsHome","AverageTD_"+mean+"_H","FLOAT")
		arcpy.CalculateField_management("RegionsHome", "AverageTD_"+mean+"_H", "!SUM_Osobokm_"+mean+"!/!SUM_Celkem_os_"+mean+"!", "PYTHON_9.3")
		arcpy.AddField_management("RegionsWork","AverageTD_"+mean+"_W","FLOAT")
		arcpy.CalculateField_management("RegionsWork", "AverageTD_"+mean+"_W", "!SUM_Osobokm_"+mean+"!/!SUM_Celkem_os_"+mean+"!", "PYTHON_9.3")
		
		#calculates ratio of travels done by all kinds of transportation for residents and for employed
		arcpy.AddField_management("RegionsHome","RES_Celkem_os_"+mean,"FLOAT")
		arcpy.CalculateField_management("RegionsHome", "RES_Celkem_os_"+mean, "!SUM_Celkem_os_"+mean+"!/!SUM_CELKEM_NEW!", "PYTHON_9.3")
		arcpy.AddField_management("RegionsWork","EMP_Celkem_os_"+mean,"FLOAT")
		arcpy.CalculateField_management("RegionsWork", "EMP_Celkem_os_"+mean, "!SUM_Celkem_os_"+mean+"!/!SUM_CELKEM_NEW!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful calculation of Average Travel Distances for every zone in ZSJ.")
	arcpy.AddMessage("Successful calculation of Travels Ratio for residents and employed in ZSJ.")
	
	# provides an ID and divide areas
	arcpy.Intersect_analysis(["calculationRegions", "RegionsHome"], "RegionsHome_inters")
	arcpy.Intersect_analysis(["calculationRegions", "RegionsWork"], "RegionsWork_inters")
	arcpy.AddMessage("Successful intersection.")
	
	# calculates the number of residents in intersected zones
	arcpy.Intersect_analysis([RESIDENTS,"RegionsHome_inters"], "ResidentsInIntersected", "ALL", "0.1 METERS", "INPUT")
	# calculates the number of employed in intersected zones
	arcpy.Intersect_analysis([EMPLOYED,"RegionsWork_inters"], "EmployedInIntersected", "ALL", "0.1 METERS", "INPUT")
	arcpy.AddMessage("Successful intersection with RESIDENTS and EMPLOYED feature classes.")

	# calculates weighted sum for number of people working in every ring
	for num in numRing:
		arcpy.AddField_management("ResidentsInIntersected","WeightedNoRing"+num,"LONG")
		arcpy.CalculateField_management("ResidentsInIntersected", "WeightedNoRing"+num, "!NoRing"+num+"!*!PTOTAL!", "PYTHON_9.3")
	arcpy.AddMessage("Successful addidtion 1.")
	
	arcpy.AddField_management("ResidentsInIntersected","DistanceAndResidents_TOTAL","FLOAT")
	arcpy.CalculateField_management("ResidentsInIntersected", "DistanceAndResidents_TOTAL", "!AverageTD_ZSJ_H!*!PTOTAL!", "PYTHON_9.3")
	arcpy.AddField_management("EmployedInIntersected","DistanceAndEmployed_TOTAL","FLOAT")
	arcpy.CalculateField_management("EmployedInIntersected", "DistanceAndEmployed_TOTAL", "!AverageTD_ZSJ_W!*!prac!", "PYTHON_9.3")
	arcpy.AddField_management("ResidentsInIntersected","RevenueResidents_TOTAL","FLOAT")
	arcpy.CalculateField_management("ResidentsInIntersected", "RevenueResidents_TOTAL", "!SUM_Osobokm_celkem!*!PTOTAL!", "PYTHON_9.3")
	arcpy.AddField_management("EmployedInIntersected","RevenueEmployed_TOTAL","FLOAT")
	arcpy.CalculateField_management("EmployedInIntersected", "RevenueEmployed_TOTAL", "!SUM_Osobokm_celkem!*!prac!", "PYTHON_9.3")
	arcpy.AddMessage("Successful addidtion 2.")
	
	for mean in meansOfTransportation:
		# sum the residents and employed for selected distances
		arcpy.AddField_management("ResidentsInIntersected","DistanceAndResidents_"+mean,"FLOAT")
		arcpy.CalculateField_management("ResidentsInIntersected", "DistanceAndResidents_"+mean, "!AverageTD_"+mean+"_H!*!PTOTAL!", "PYTHON_9.3")
		arcpy.AddField_management("EmployedInIntersected","DistanceAndEmployed_"+mean,"FLOAT")
		arcpy.CalculateField_management("EmployedInIntersected", "DistanceAndEmployed_"+mean, "!AverageTD_"+mean+"_W!*!prac!", "PYTHON_9.3")
		
		# sum the residents and employed for selected ratios
		arcpy.AddField_management("ResidentsInIntersected","RatioAndResidents_"+mean,"FLOAT")
		arcpy.CalculateField_management("ResidentsInIntersected", "RatioAndResidents_"+mean, "!RES_Celkem_os_"+mean+"!*!PTOTAL!", "PYTHON_9.3")
		arcpy.AddField_management("EmployedInIntersected","RatioAndEmployed_"+mean,"FLOAT")
		arcpy.CalculateField_management("EmployedInIntersected", "RatioAndEmployed_"+mean, "!EMP_Celkem_os_"+mean+"!*!prac!", "PYTHON_9.3")
	
		# sum the residents and employed for selected revenues
		arcpy.AddField_management("ResidentsInIntersected","RevenueResidents_"+mean,"FLOAT")
		arcpy.CalculateField_management("ResidentsInIntersected", "RevenueResidents_"+mean, "!SUM_Osobokm_"+mean+"!*!PTOTAL!", "PYTHON_9.3")
		arcpy.AddField_management("EmployedInIntersected","RevenueEmployed_"+mean,"FLOAT")
		arcpy.CalculateField_management("EmployedInIntersected", "RevenueEmployed_"+mean, "!SUM_Osobokm_"+mean+"!*!prac!", "PYTHON_9.3")
	arcpy.AddMessage("Successful addidtion 3.")
	
	arcpy.AddMessage("Successful calculation of needed factors.")
	
	# sums up the distances, ratios and revenues and number of residents/employed
	arcpy.Dissolve_management("ResidentsInIntersected", "RESIDENTSInZones", "ZONE_ID", "WeightedNoRing0 SUM; WeightedNoRing1 SUM; WeightedNoRing2 SUM; WeightedNoRing3 SUM; WeightedNoRing4 SUM; WeightedNoRing4 SUM; DistanceAndResidents_TOTAL SUM; DistanceAndResidents_HD SUM; DistanceAndResidents_IAD SUM; DistanceAndResidents_kolo SUM; DistanceAndResidents_pesi SUM; RatioAndResidents_HD SUM; RatioAndResidents_IAD SUM; RatioAndResidents_kolo SUM; RatioAndResidents_pesi SUM; RevenueResidents_TOTAL SUM; RevenueResidents_HD SUM; RevenueResidents_IAD SUM; RevenueResidents_kolo SUM; RevenueResidents_pesi SUM; PTOTAL SUM")
	arcpy.Dissolve_management("EmployedInIntersected", "EMPLOYEDInZones", "ZONE_ID", "DistanceAndEmployed_TOTAL SUM; DistanceAndEmployed_HD SUM; DistanceAndEmployed_IAD SUM; DistanceAndEmployed_kolo SUM; DistanceAndEmployed_pesi SUM; RatioAndEmployed_HD SUM; RatioAndEmployed_IAD SUM; RatioAndEmployed_kolo SUM; RatioAndEmployed_pesi SUM; RevenueEmployed_TOTAL SUM; RevenueEmployed_HD SUM; RevenueEmployed_IAD SUM; RevenueEmployed_kolo SUM; RevenueEmployed_pesi SUM; prac SUM")
	arcpy.AddMessage("Successful dissolution.")
	
	# calculates number of residents that are working in different rings 
	for num in numRing:
		arcpy.AddField_management("RESIDENTSInZones", "WorkInRing"+num,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "WorkInRing"+num, "!SUM_WeightedNoRing"+num+"!/!SUM_PTOTAL!", "PYTHON_9.3")
	arcpy.AddMessage("Successful dissolution.")
	
	# calculates sum of people working in every ring 1-2-3-4 and 0 which means outside 
	arcpy.AddField_management("RESIDENTSInZones","SumWorkingRing","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "SumWorkingRing", "!WorkInRing0!+!WorkInRing1!+!WorkInRing2!+!WorkInRing3!+!WorkInRing4!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	# calculates the ratio for every zone (what percentage of people living in that zone works in one of the city ring)
	for num in numRing:
		arcpy.AddField_management("RESIDENTSInZones", "RatioInRing"+num,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "RatioInRing"+num, "!WorkInRing"+num+"!/!SumWorkingRing!*100", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition 1.")
		
	# calculates average travel distances for residents and employed
	arcpy.AddField_management("RESIDENTSInZones", "ATD_RESIDENTS_TOTAL","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "ATD_RESIDENTS_TOTAL", "!SUM_DistanceAndResidents_TOTAL!/!SUM_PTOTAL!", "PYTHON_9.3")
	arcpy.AddField_management("EMPLOYEDInZones", "ATD_EMPLOYED_TOTAL","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "ATD_EMPLOYED_TOTAL", "!SUM_DistanceAndEmployed_TOTAL!/!SUM_prac!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition 2.")
	
	# calculates total revenue for residents and employed
	arcpy.AddField_management("RESIDENTSInZones", "RPR_RESIDENTS_TOTAL","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RESIDENTS_TOTAL", "!SUM_RevenueResidents_TOTAL!/!SUM_PTOTAL!", "PYTHON_9.3")
	arcpy.AddField_management("EMPLOYEDInZones", "RPR_EMPLOYED_TOTAL","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "RPR_EMPLOYED_TOTAL", "!SUM_RevenueEmployed_TOTAL!/!SUM_prac!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition 3.")

	for mean in meansOfTransportation:
		# calculates average travel distance for residents and employed
		arcpy.AddField_management("RESIDENTSInZones", "ATD_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "ATD_RESIDENTS_"+mean, "!SUM_DistanceAndResidents_"+mean+"!/!SUM_PTOTAL!", "PYTHON_9.3")
		
		arcpy.AddField_management("EMPLOYEDInZones", "ATD_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "ATD_EMPLOYED_"+mean, "!SUM_DistanceAndEmployed_"+mean+"!/!SUM_prac!", "PYTHON_9.3")
		
		# calculates travel ratios for residents and employed
		arcpy.AddField_management("RESIDENTSInZones", "TR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "TR_RESIDENTS_"+mean, "!SUM_RatioAndResidents_"+mean+"!/!SUM_PTOTAL!*100", "PYTHON_9.3")
		
		arcpy.AddField_management("EMPLOYEDInZones", "TR_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "TR_EMPLOYED_"+mean, "!SUM_RatioAndEmployed_"+mean+"!/!SUM_prac!*100", "PYTHON_9.3")
		
		# calculates revenue passenger kilometers total for residents and employed
		arcpy.AddField_management("RESIDENTSInZones", "RPR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RESIDENTS_"+mean, "!SUM_RevenueResidents_"+mean+"!/!SUM_PTOTAL!", "PYTHON_9.3")
		
		arcpy.AddField_management("EMPLOYEDInZones", "RPR_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "RPR_EMPLOYED_"+mean, "!SUM_RevenueEmployed_"+mean+"!/!SUM_prac!", "PYTHON_9.3")
		
	arcpy.AddMessage("Successful calculation of Average Travel Distance for Residents and Employed within given polygons.")
	arcpy.AddMessage("Successful calculation of Travel Ratios for Residents and Employed within given polygons.")
	arcpy.AddMessage("Successful calculation of Revenue Passenger Kilometers Total for Residents and Employed within given polygons.")
	
	# calculates sum of revenues to calculate the total one 
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
	arcpy.AddMessage("Successful calculation of Ratio of Total Revenue for Residents and Employed within given polygons.")
	
	# calculates the revenue for other means of transportation (different than HD, IAD, kolo, pesi)
	arcpy.AddField_management("RESIDENTSInZones", "RTR_RESIDENTS_OTHER","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "RTR_RESIDENTS_OTHER", "!RPR_RESIDENTS_OTHER!/!RPR_RESIDENTS_TOTAL!*100", "PYTHON_9.3")
	arcpy.AddField_management("EMPLOYEDInZones", "RTR_EMPLOYED_OTHER","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "RTR_EMPLOYED_OTHER", "!RPR_EMPLOYED_OTHER!/!RPR_EMPLOYED_TOTAL!*100", "PYTHON_9.3")
	
	# adds new index to the calculationRegions so the joining fields management will work quicker
	arcpy.AddIndex_management("calculationRegions","ZONE_ID","codeIndex")
	# adds the result columns with TRAVEL RATIOS for home and work to the RESULTS 
	arcpy.JoinField_management("calculationRegions","ZONE_ID","RESIDENTSInZones","ZONE_ID", ["WorkInRing0", "WorkInRing1", "WorkInRing2", "WorkInRing3", "WorkInRing4", "RatioInRing0", "RatioInRing1", "RatioInRing2", "RatioInRing3", "RatioInRing4", "ATD_RESIDENTS_TOTAL", "ATD_RESIDENTS_HD", "ATD_RESIDENTS_IAD", "ATD_RESIDENTS_kolo", "ATD_RESIDENTS_pesi","TR_RESIDENTS_HD", "TR_RESIDENTS_IAD", "TR_RESIDENTS_kolo", "TR_RESIDENTS_pesi", "RPR_RESIDENTS_TOTAL", "RPR_RESIDENTS_OTHER", "RPR_RESIDENTS_HD", "RPR_RESIDENTS_IAD", "RPR_RESIDENTS_kolo", "RPR_RESIDENTS_pesi", "RTR_RESIDENTS_OTHER", "RTR_RESIDENTS_HD", "RTR_RESIDENTS_IAD", "RTR_RESIDENTS_kolo", "RTR_RESIDENTS_pesi"])
	arcpy.JoinField_management("calculationRegions","ZONE_ID", "EMPLOYEDInZones","ZONE_ID", ["ATD_EMPLOYED_TOTAL", "ATD_EMPLOYED_HD", "ATD_EMPLOYED_IAD", "ATD_EMPLOYED_kolo", "ATD_EMPLOYED_pesi", "TR_EMPLOYED_HD", "TR_EMPLOYED_IAD", "TR_EMPLOYED_kolo", "TR_EMPLOYED_pesi", "RPR_EMPLOYED_TOTAL", "RPR_EMPLOYED_OTHER", "RPR_EMPLOYED_HD", "RPR_EMPLOYED_IAD", "RPR_EMPLOYED_kolo", "RPR_EMPLOYED_pesi", "RTR_EMPLOYED_OTHER", "RTR_EMPLOYED_HD", "RTR_EMPLOYED_IAD", "RTR_EMPLOYED_kolo", "RTR_EMPLOYED_pesi"])
	arcpy.AddMessage("Successful join.")
	
	# some problems here
	# adds the result columns with TRAVEL RATIOS for home and work to the RESULTS 
	#joinFieldImported("calculationRegions","ZONE_ID","RESIDENTSInZones","ZONE_ID", "WorkInRing0;WorkInRing1;WorkInRing2;WorkInRing3;WorkInRing4;RatioInRing0;RatioInRing1;RatioInRing2;RatioInRing3;RatioInRing4;ATD_RESIDENTS_TOTAL;ATD_RESIDENTS_HD;ATD_RESIDENTS_IAD;ATD_RESIDENTS_kolo;ATD_RESIDENTS_pesi;TR_RESIDENTS_HD;TR_RESIDENTS_IAD;TR_RESIDENTS_kolo;TR_RESIDENTS_pesi;RPR_RESIDENTS_TOTAL;RPR_RESIDENTS_OTHER;RPR_RESIDENTS_HD;RPR_RESIDENTS_IAD;RPR_RESIDENTS_kolo;RPR_RESIDENTS_pesi;RTR_RESIDENTS_OTHER;RTR_RESIDENTS_HD;RTR_RESIDENTS_IAD;RTR_RESIDENTS_kolo;RTR_RESIDENTS_pesi")
	#joinFieldImported("calculationRegions","ZONE_ID", "EMPLOYEDInZones","ZONE_ID", "ATD_EMPLOYED_TOTAL;ATD_EMPLOYED_HD;ATD_EMPLOYED_IAD;ATD_EMPLOYED_kolo;ATD_EMPLOYED_pesi;TR_EMPLOYED_HD;TR_EMPLOYED_IAD;TR_EMPLOYED_kolo;TR_EMPLOYED_pesi;RPR_EMPLOYED_TOTAL;RPR_EMPLOYED_OTHER;RPR_EMPLOYED_HD;RPR_EMPLOYED_IAD;RPR_EMPLOYED_kolo;RPR_EMPLOYED_pesi;RTR_EMPLOYED_OTHER;RTR_EMPLOYED_HD;RTR_EMPLOYED_IAD;RTR_EMPLOYED_kolo;RTR_EMPLOYED_pesi")
	arcpy.AddMessage("Successful fields addition.")
	#HERE GOES THE CHECKING PART - not important right now
	#adds two new fields to check correctness of the calculations of travel ratio (if sum = 100 , the calculations are correct)
	# arcpy.AddField_management("calculationRegions","ResRatioSUM","FLOAT")
	# arcpy.CalculateField_management("calculationRegions", "ResRatioSUM", "!TR_RESIDENTS_HD! + !TR_RESIDENTS_IAD! + !TR_RESIDENTS_kolo! + !TR_RESIDENTS_pesi!", "PYTHON_9.3")
	# arcpy.AddField_management("calculationRegions","EmpRatioSUM","FLOAT")
	# arcpy.CalculateField_management("calculationRegions", "EmpRatioSUM", "!TR_EMPLOYED_HD! + !TR_EMPLOYED_IAD! + !TR_EMPLOYED_kolo! + !TR_EMPLOYED_pesi!", "PYTHON_9.3")
	
	#adds two new fields to check correctness of the calculations of ratio total revenue (if sum = 100 , the calculations are correct)
	# arcpy.AddField_management("calculationRegions", "RTR_RE_100","LONG")
	# arcpy.CalculateField_management("calculationRegions", "RTR_RE_100", "!RTR_RESIDENTS_OTHER!+!RTR_RESIDENTS_HD!+!RTR_RESIDENTS_IAD!+!RTR_RESIDENTS_kolo!+!RTR_RESIDENTS_pesi!", "PYTHON_9.3")
	# arcpy.AddField_management("calculationRegions", "RTR_EM_100","LONG")
	# arcpy.CalculateField_management("calculationRegions", "RTR_EM_100", "!RTR_EMPLOYED_OTHER!+!RTR_EMPLOYED_HD!+!RTR_EMPLOYED_IAD!+!RTR_EMPLOYED_kolo!+!RTR_EMPLOYED_pesi!", "PYTHON_9.3")
	# arcpy.AddMessage("Successful fields addition.")
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
