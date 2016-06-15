import arcpy
from arcpy import env
import os

'''
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
KODNAZEV = [1, 2, 3, 4, 5]
numRing = ["0", "1", "2", "3", "4", "5"]	

env.workspace = "C:\\Esri\\temp_data.gdb" 

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
	'''
	# gets rid of <Null> values in distance field
	arcpy.CalculateField_management(TABULKA, "VZDALENOST", "r(!VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 
	arcpy.TableSelect_analysis(TABULKA, "TABULKA", "VZDALENOST > 0")
	
	# copy the table for adding rings
	arcpy.TableSelect_analysis("TABULKA", "TABULKA_R")
	'''
	arcpy.TableSelect_analysis(TABULKA, "TABULKA")
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions 
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	'''
	#***
	# ading an information about the ring to each ZSJ
	arcpy.MakeFeatureLayer_management ("pasmaMesta", "pasmaMesta_view")
	arcpy.MakeFeatureLayer_management ("RegionsHome", "ZSJ_COPY")
	arcpy.AddField_management("ZSJ_COPY","NoRing","LONG")
	arcpy.AddMessage("Successful layer creation.")
	
	for kod in KODNAZEV:
		arcpy.SelectLayerByAttribute_management ("pasmaMesta_view", "NEW_SELECTION", "OBLAST = "+str(kod))
		arcpy.SelectLayerByLocation_management ("ZSJ_COPY", "HAVE_THEIR_CENTER_IN", "pasmaMesta_view")
		arcpy.CalculateField_management("ZSJ_COPY", "NoRing", kod, "PYTHON_9.3")
		arcpy.SelectLayerByAttribute_management ("ZSJ_COPY", "CLEAR_SELECTION")
	arcpy.Delete_management ("ZSJ_COPY")
	arcpy.AddMessage("Successful ring num addidtion.")
	
	joinFieldImported("TABULKA_R", "DOPR_ZSJDPS_KOD", "RegionsHome", "KOD_ZSJ7", "NoRing")
	arcpy.AddMessage("Successful join.")
	
	# adds 0 to rows that are outside the city rings
	arcpy.CalculateField_management("TABULKA_R", "NoRing", "r(!NoRing!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	#***
	arcpy.AddMessage("Statistics analysis can take some time...")
	
	arcpy.Statistics_analysis ("TABULKA_R", "tabulkaToPivot", [["CELKEM", "SUM"]], ["DOPR_ZSJDOP_KOD", "NoRing"])
	arcpy.AddMessage("Successful calculation of pivot table.")
	
	# pivoting the table to get total number of people working in every ring
	arcpy.PivotTable_management ("tabulkaToPivot", "DOPR_ZSJDOP_KOD", "NoRing", "SUM_CELKEM", "pivot_TOTAL")
	arcpy.AddMessage("Successful pivoting.")
	
	joinFieldImported("RegionsHome", "KOD_ZSJ7", "pivot_TOTAL", "DOPR_ZSJDOP_KOD", "NoRing0;NoRing1;NoRing2;NoRing3;NoRing4;NoRing5")
	arcpy.AddMessage("Successful join fields from pivoted table.")
	
	# calculates the ratio of people living in particular ZSJ and working in one of the city ring
	for num in numRing:
		arcpy.AddField_management("RegionsHome","podilZSJ"+num,"FLOAT")
		arcpy.CalculateField_management("RegionsHome", "podilZSJ"+num, "!NoRing"+num+"!/(!NoRing0!+!NoRing1!+!NoRing2!+!NoRing3!+!NoRing4!+!NoRing5!)", "PYTHON_9.3")
	'''
	
	# creates flaten tables for HOME and for WORK
	arcpy.Statistics_analysis ("TABULKA", "tabulka_home", [["VZDALENOST", "SUM"], ["Osobokm_celkem", "SUM"], ["Osobokm_HD", "SUM"], ["Osobokm_IAD", "SUM"], ["Osobokm_kolo", "SUM"], ["Osobokm_pesi", "SUM"],["CELKEM", "SUM"], ["Celkem_os_HD", "SUM"], ["Celkem_os_IAD", "SUM"], ["Celkem_os_kolo", "SUM"], ["Celkem_os_pesi", "SUM"]], "DOPR_ZSJDOP_KOD")
	arcpy.Statistics_analysis ("TABULKA", "tabulka_work", [["VZDALENOST", "SUM"], ["Osobokm_celkem", "SUM"], ["Osobokm_HD", "SUM"], ["Osobokm_IAD", "SUM"], ["Osobokm_kolo", "SUM"], ["Osobokm_pesi", "SUM"],["CELKEM", "SUM"], ["Celkem_os_HD", "SUM"], ["Celkem_os_IAD", "SUM"], ["Celkem_os_kolo", "SUM"], ["Celkem_os_pesi", "SUM"]], "DOPR_ZSJDPS_KOD")
	arcpy.AddMessage("Successful calculation of values in the HOME and WORK tables.")
	
	joinFieldImported ("RegionsHome", "KOD_ZSJ7", "tabulka_home", "DOPR_ZSJDOP_KOD", "SUM_VZDALENOST;SUM_Osobokm_celkem;SUM_Osobokm_HD;SUM_Osobokm_IAD;SUM_Osobokm_kolo;SUM_Osobokm_pesi;SUM_CELKEM;SUM_Celkem_os_HD;SUM_Celkem_os_IAD;SUM_Celkem_os_kolo;SUM_Celkem_os_pesi")
	arcpy.AddMessage("Successful join fields for home regions.")
	joinFieldImported ("RegionsWork", "KOD_ZSJ7", "tabulka_work", "DOPR_ZSJDPS_KOD", "SUM_VZDALENOST;SUM_Osobokm_celkem;SUM_Osobokm_HD;SUM_Osobokm_IAD;SUM_Osobokm_kolo;SUM_Osobokm_pesi;SUM_CELKEM;SUM_Celkem_os_HD;SUM_Celkem_os_IAD;SUM_Celkem_os_kolo;SUM_Celkem_os_pesi")
	arcpy.AddMessage("Successful join fields for work regions.")
	
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
	
	
	
	
	'''
	HERE IS WHERE YOU NEED YOU NEED TO CHANGE podilZSJ5 -> TO OTHER NUMBERS [podilZSJ1, podilZSJ2, podilZSJ3, podilZSJ4, podilZSJ5] TO CALCULATE NUMBER OF PEOPLE WORKING IN DIFFERENT RINGS
	'''
	
	arcpy.AddField_management("ResidentsInIntersected","PTOTAL_ZSJ","FLOAT")
	arcpy.CalculateField_management("ResidentsInIntersected", "PTOTAL_ZSJ", "!podilZSJ5!*!PTOTAL!", "PYTHON_9.3")
	
	'''
	'''
	
	'''
	# calculates total number of people in ZSJ 
	arcpy.Dissolve_management("ResidentsInIntersected", "RESIDENTSInInt", ["KOD_ZSJ7", "ZONE_ID"], "PTOTAL SUM")
	arcpy.JoinField_management("RESIDENTSInInt","KOD_ZSJ7","ResidentsInIntersected","KOD_ZSJ7", ["podilZSJ0", "podilZSJ1", "podilZSJ2", "podilZSJ3", "podilZSJ4", "podilZSJ5"])
	
	# calculates number of people living in the particular ZSJ and working in one of the city rings
	for num in numRing:
		arcpy.AddField_management("RESIDENTSInInt", "WorkInRingInt"+num,"LONG")
		arcpy.CalculateField_management("RESIDENTSInInt", "WorkInRingInt"+num, "!podilZSJ"+num+"!*!SUM_PTOTAL!", "PYTHON_9.3")
	arcpy.AddMessage("Successful addidtion 1.")
	'''
	
	arcpy.AddField_management("ResidentsInIntersected","DistanceAndResidents_TOTAL","FLOAT")
	arcpy.CalculateField_management("ResidentsInIntersected", "DistanceAndResidents_TOTAL", "!AverageTD_ZSJ_H!*!PTOTAL_ZSJ!", "PYTHON_9.3")
	arcpy.AddField_management("EmployedInIntersected","DistanceAndEmployed_TOTAL","FLOAT")
	arcpy.CalculateField_management("EmployedInIntersected", "DistanceAndEmployed_TOTAL", "!AverageTD_ZSJ_W!*!prac!", "PYTHON_9.3")
	arcpy.AddField_management("ResidentsInIntersected","RevenueResidents_TOTAL","FLOAT")
	arcpy.AddMessage("Successful addidtion 2.")
	
	for mean in meansOfTransportation:
		# sum the residents and employed for selected distances
		arcpy.AddField_management("ResidentsInIntersected","DistanceAndResidents_"+mean,"FLOAT")
		arcpy.CalculateField_management("ResidentsInIntersected", "DistanceAndResidents_"+mean, "!AverageTD_"+mean+"_H!*!PTOTAL_ZSJ!", "PYTHON_9.3")
		arcpy.AddField_management("EmployedInIntersected","DistanceAndEmployed_"+mean,"FLOAT")
		arcpy.CalculateField_management("EmployedInIntersected", "DistanceAndEmployed_"+mean, "!AverageTD_"+mean+"_W!*!prac!", "PYTHON_9.3")
		
		# sum the residents and employed for selected ratios
		arcpy.AddField_management("ResidentsInIntersected","RatioAndResidents_"+mean,"FLOAT")
		arcpy.CalculateField_management("ResidentsInIntersected", "RatioAndResidents_"+mean, "!RES_Celkem_os_"+mean+"!*!PTOTAL_ZSJ!", "PYTHON_9.3")
		arcpy.AddField_management("EmployedInIntersected","RatioAndEmployed_"+mean,"FLOAT")
		arcpy.CalculateField_management("EmployedInIntersected", "RatioAndEmployed_"+mean, "!EMP_Celkem_os_"+mean+"!*!prac!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful addidtion 3.")
	
	arcpy.AddMessage("Successful calculation of needed factors.")
	
	# sums up the distances, ratios and revenues and number of residents/employed
	arcpy.Dissolve_management("ResidentsInIntersected", "RESIDENTSInZones", "ZONE_ID", "DistanceAndResidents_TOTAL SUM; DistanceAndResidents_HD SUM; DistanceAndResidents_IAD SUM; DistanceAndResidents_kolo SUM; DistanceAndResidents_pesi SUM; RatioAndResidents_HD SUM; RatioAndResidents_IAD SUM; RatioAndResidents_kolo SUM; RatioAndResidents_pesi SUM; PTOTAL_ZSJ SUM")
	arcpy.Dissolve_management("EmployedInIntersected", "EMPLOYEDInZones", "ZONE_ID", "DistanceAndEmployed_TOTAL SUM; DistanceAndEmployed_HD SUM; DistanceAndEmployed_IAD SUM; DistanceAndEmployed_kolo SUM; DistanceAndEmployed_pesi SUM; RatioAndEmployed_HD SUM; RatioAndEmployed_IAD SUM; RatioAndEmployed_kolo SUM; RatioAndEmployed_pesi SUM; prac SUM")
	arcpy.AddMessage("Successful dissolution.")
	
	'''
	# sums up the number of people living in particular calculation region (lokality) and working in one of the city rings
	arcpy.Dissolve_management("RESIDENTSInInt", "RESIDENTSInZ_toJoin", "ZONE_ID", " WorkInRingInt0 SUM; WorkInRingInt1 SUM; WorkInRingInt2 SUM; WorkInRingInt3 SUM; WorkInRingInt4 SUM; WorkInRingInt5 SUM")
	arcpy.JoinField_management("RESIDENTSInZones","ZONE_ID","RESIDENTSInZ_toJoin","ZONE_ID", ["SUM_WorkInRingInt0", "SUM_WorkInRingInt1", "SUM_WorkInRingInt2", "SUM_WorkInRingInt3", "SUM_WorkInRingInt4", "SUM_WorkInRingInt5"])
	
	# alter field names
	arcpy.AlterField_management("RESIDENTSInZones", "SUM_WorkInRingInt0", "WorkInRing0")
	arcpy.AlterField_management("RESIDENTSInZones", "SUM_WorkInRingInt1", "WorkInRing1")
	arcpy.AlterField_management("RESIDENTSInZones", "SUM_WorkInRingInt2", "WorkInRing2")
	arcpy.AlterField_management("RESIDENTSInZones", "SUM_WorkInRingInt3", "WorkInRing3")
	arcpy.AlterField_management("RESIDENTSInZones", "SUM_WorkInRingInt4", "WorkInRing4")
	arcpy.AlterField_management("RESIDENTSInZones", "SUM_WorkInRingInt5", "WorkInRing5")

	# calculates sum of people working in every ring 1-2-3-4 and 0 which means outside 
	arcpy.AddField_management("RESIDENTSInZones","SumWorkingRing","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "SumWorkingRing", "!WorkInRing0!+!WorkInRing1!+!WorkInRing2!+!WorkInRing3!+!WorkInRing4!+!WorkInRing5!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	# calculates the ratio for every zone (what percentage of people living in that zone works in one of the city ring)
	for num in numRing:
		arcpy.AddField_management("RESIDENTSInZones", "RatioInRing"+num,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "RatioInRing"+num, "!WorkInRing"+num+"!/!SumWorkingRing!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition 1.")
	'''	
	
	arcpy.AddField_management("RESIDENTSInZones","SUM_PTOTAL_Z","LONG")
	arcpy.CalculateField_management("RESIDENTSInZones", "SUM_PTOTAL_Z", "!SUM_PTOTAL_ZSJ!", "PYTHON_9.3")
	
	# calculates average travel distances for residents and employed
	arcpy.AddField_management("RESIDENTSInZones", "ATD_RESIDENTS_TOTAL","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "ATD_RESIDENTS_TOTAL", "!SUM_DistanceAndResidents_TOTAL!/!SUM_PTOTAL_Z!", "PYTHON_9.3")
	arcpy.AddField_management("EMPLOYEDInZones", "ATD_EMPLOYED_TOTAL","FLOAT")
	arcpy.CalculateField_management("EMPLOYEDInZones", "ATD_EMPLOYED_TOTAL", "!SUM_DistanceAndEmployed_TOTAL!/!SUM_prac!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition 2.")
	
	# calculates total revenue for residents and employed
	arcpy.AddField_management("RESIDENTSInZones", "RPR_RESIDENTS_TOTAL","FLOAT")
	arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RESIDENTS_TOTAL", "!ATD_RESIDENTS_TOTAL!*!SUM_PTOTAL_Z!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition 3.")

	for mean in meansOfTransportation:
		# calculates average travel distance for residents and employed
		arcpy.AddField_management("RESIDENTSInZones", "ATD_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "ATD_RESIDENTS_"+mean, "!SUM_DistanceAndResidents_"+mean+"!/!SUM_PTOTAL_Z!", "PYTHON_9.3")
		
		arcpy.AddField_management("EMPLOYEDInZones", "ATD_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "ATD_EMPLOYED_"+mean, "!SUM_DistanceAndEmployed_"+mean+"!/!SUM_prac!", "PYTHON_9.3")
		
		# calculates travel ratios for residents and employed
		arcpy.AddField_management("RESIDENTSInZones", "TR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "TR_RESIDENTS_"+mean, "!SUM_RatioAndResidents_"+mean+"!/!SUM_PTOTAL_Z!", "PYTHON_9.3")
		
		arcpy.AddField_management("EMPLOYEDInZones", "TR_EMPLOYED_"+mean,"FLOAT")
		arcpy.CalculateField_management("EMPLOYEDInZones", "TR_EMPLOYED_"+mean, "!SUM_RatioAndEmployed_"+mean+"!/!SUM_prac!", "PYTHON_9.3")
		
		# calculates revenue passenger kilometers total for residents and employed
		arcpy.AddField_management("RESIDENTSInZones", "RPR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "RPR_RESIDENTS_"+mean, "!ATD_RESIDENTS_"+mean+"!*!SUM_PTOTAL_Z!*!TR_RESIDENTS_"+mean+"!", "PYTHON_9.3")
		
	arcpy.AddMessage("Successful calculation of Average Travel Distance for Residents and Employed within given polygons.")
	arcpy.AddMessage("Successful calculation of Travel Ratios for Residents and Employed within given polygons.")
	arcpy.AddMessage("Successful calculation of Revenue Passenger Kilometers Total for Residents and Employed within given polygons.")
	
	for mean in meansOfTransportation:
		arcpy.AddField_management("RESIDENTSInZones", "RTR_RESIDENTS_"+mean,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "RTR_RESIDENTS_"+mean, "!RPR_RESIDENTS_"+mean+"!/!RPR_RESIDENTS_TOTAL!", "PYTHON_9.3")
	arcpy.AddMessage("Successful calculation of Ratio of Total Revenue for Residents and Employed within given polygons.")
	
	
	# adds new index to the calculationRegions so the joining fields management will work quicker
	arcpy.AddIndex_management("calculationRegions","ZONE_ID","codeIndex")
	# adds the result columns with TRAVEL RATIOS for home and work to the RESULTS
	arcpy.JoinField_management("calculationRegions","ZONE_ID","RESIDENTSInZones","ZONE_ID", ["ATD_RESIDENTS_TOTAL", "ATD_RESIDENTS_HD", "ATD_RESIDENTS_IAD", "ATD_RESIDENTS_kolo", "ATD_RESIDENTS_pesi","TR_RESIDENTS_HD", "TR_RESIDENTS_IAD", "TR_RESIDENTS_kolo", "TR_RESIDENTS_pesi", "RPR_RESIDENTS_TOTAL", "RPR_RESIDENTS_OTHER", "RPR_RESIDENTS_HD", "RPR_RESIDENTS_IAD", "RPR_RESIDENTS_kolo", "RPR_RESIDENTS_pesi", "RTR_RESIDENTS_OTHER", "RTR_RESIDENTS_HD", "RTR_RESIDENTS_IAD", "RTR_RESIDENTS_kolo", "RTR_RESIDENTS_pesi"])
	#arcpy.JoinField_management("calculationRegions","ZONE_ID","RESIDENTSInZones","ZONE_ID", ["WorkInRing0", "WorkInRing1", "WorkInRing2", "WorkInRing3", "WorkInRing4", "WorkInRing5", "RatioInRing0", "RatioInRing1", "RatioInRing2", "RatioInRing3", "RatioInRing4", "RatioInRing5", "ATD_RESIDENTS_TOTAL", "ATD_RESIDENTS_HD", "ATD_RESIDENTS_IAD", "ATD_RESIDENTS_kolo", "ATD_RESIDENTS_pesi","TR_RESIDENTS_HD", "TR_RESIDENTS_IAD", "TR_RESIDENTS_kolo", "TR_RESIDENTS_pesi", "RPR_RESIDENTS_TOTAL", "RPR_RESIDENTS_OTHER", "RPR_RESIDENTS_HD", "RPR_RESIDENTS_IAD", "RPR_RESIDENTS_kolo", "RPR_RESIDENTS_pesi", "RTR_RESIDENTS_OTHER", "RTR_RESIDENTS_HD", "RTR_RESIDENTS_IAD", "RTR_RESIDENTS_kolo", "RTR_RESIDENTS_pesi"])
	#arcpy.JoinField_management("calculationRegions","ZONE_ID", "EMPLOYEDInZones","ZONE_ID", ["ATD_EMPLOYED_TOTAL", "ATD_EMPLOYED_HD", "ATD_EMPLOYED_IAD", "ATD_EMPLOYED_kolo", "ATD_EMPLOYED_pesi", "TR_EMPLOYED_HD", "TR_EMPLOYED_IAD", "TR_EMPLOYED_kolo", "TR_EMPLOYED_pesi", "RPR_EMPLOYED_TOTAL", "RPR_EMPLOYED_OTHER", "RPR_EMPLOYED_HD", "RPR_EMPLOYED_IAD", "RPR_EMPLOYED_kolo", "RPR_EMPLOYED_pesi", "RTR_EMPLOYED_OTHER", "RTR_EMPLOYED_HD", "RTR_EMPLOYED_IAD", "RTR_EMPLOYED_kolo", "RTR_EMPLOYED_pesi"])
	arcpy.AddMessage("Successful join.")
	
	# alter names from english to czech
	arcpy.AlterField_management ("calculationRegions", "ATD_RESIDENTS_TOTAL", "AVG_distance", "AVG_distance")
	arcpy.AlterField_management ("calculationRegions", "ATD_RESIDENTS_HD", "AVG_distance_HD", "AVG_distance_HD")
	arcpy.AlterField_management ("calculationRegions", "ATD_RESIDENTS_IAD", "AVG_distance_IAD", "AVG_distance_IAD")
	arcpy.AlterField_management ("calculationRegions", "ATD_RESIDENTS_kolo", "AVG_distance_kolo", "AVG_distance_kolo")
	arcpy.AlterField_management ("calculationRegions", "ATD_RESIDENTS_pesi", "AVG_distance_pesi", "AVG_distance_pesi")
	
	arcpy.AlterField_management ("calculationRegions", "TR_RESIDENTS_HD", "podil_cest_HD", "podil_cest_HD")
	arcpy.AlterField_management ("calculationRegions", "TR_RESIDENTS_IAD", "podil_cest_IAD", "podil_cest_IAD")
	arcpy.AlterField_management ("calculationRegions", "TR_RESIDENTS_kolo", "podil_cest_kolo", "podil_cest_kolo")
	arcpy.AlterField_management ("calculationRegions", "TR_RESIDENTS_pesi", "podil_cest_pesi", "podil_cest_pesi")
	
	arcpy.AlterField_management ("calculationRegions", "RPR_RESIDENTS_TOTAL", "osobokm_celkem", "osobokm_celkem")
	arcpy.AlterField_management ("calculationRegions", "RPR_RESIDENTS_HD", "osobokm_HD", "osobokm_HD")
	arcpy.AlterField_management ("calculationRegions", "RPR_RESIDENTS_IAD", "osobokm_IAD", "osobokm_IAD")
	arcpy.AlterField_management ("calculationRegions", "RPR_RESIDENTS_kolo", "osobokm_kolo", "osobokm_kolo")
	arcpy.AlterField_management ("calculationRegions", "RPR_RESIDENTS_pesi", "osobokm_pesi", "osobokm_pesi")
	
	arcpy.AlterField_management ("calculationRegions", "RTR_RESIDENTS_HD", "podil_osobokm_HD", "podil_osobokm_HD")
	arcpy.AlterField_management ("calculationRegions", "RTR_RESIDENTS_IAD", "podil_osobokm_IAD", "podil_osobokm_IAD")
	arcpy.AlterField_management ("calculationRegions", "RTR_RESIDENTS_kolo", "podil_osobokm_kolo", "podil_osobokm_kolo")
	arcpy.AlterField_management ("calculationRegions", "RTR_RESIDENTS_pesi", "podil_osobokm_pesi", "podil_osobokm_pesi")
	
	'''
	arcpy.AlterField_management ("calculationRegions", "WorkInRing0", "prac_v_oblast_0", "prac_v_oblast_0")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing1", "prac_v_oblast_1", "prac_v_oblast_1")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing2", "prac_v_oblast_2", "prac_v_oblast_2")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing3", "prac_v_oblast_3", "prac_v_oblast_3")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing4", "prac_v_oblast_4", "prac_v_oblast_4")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing5", "prac_v_oblast_5", "prac_v_oblast_5")
	
	arcpy.AlterField_management ("calculationRegions", "RatioInRing0", "podil_oblast0", "podil_oblast0")
	arcpy.AlterField_management ("calculationRegions", "RatioInRing1", "podil_oblast1", "podil_oblast1")
	arcpy.AlterField_management ("calculationRegions", "RatioInRing2", "podil_oblast2", "podil_oblast2")
	arcpy.AlterField_management ("calculationRegions", "RatioInRing3", "podil_oblast3", "podil_oblast3")
	arcpy.AlterField_management ("calculationRegions", "RatioInRing4", "podil_oblast4", "podil_oblast4")
	arcpy.AlterField_management ("calculationRegions", "RatioInRing5", "podil_oblast5", "podil_oblast5")
	'''
	arcpy.AddMessage("Successful fields alteration.")
	

	#HERE GOES THE CHECKING PART
	
	#adds two new fields to check correctness of the calculations of travel ratio (if sum = 1 , the calculations are correct)
	# arcpy.AddField_management("calculationRegions","ResRatioSUM","FLOAT")
	# arcpy.CalculateField_management("calculationRegions", "ResRatioSUM", "!TR_RESIDENTS_HD! + !TR_RESIDENTS_IAD! + !TR_RESIDENTS_kolo! + !TR_RESIDENTS_pesi!", "PYTHON_9.3")
	# arcpy.AddField_management("calculationRegions","EmpRatioSUM","FLOAT")
	# arcpy.CalculateField_management("calculationRegions", "EmpRatioSUM", "!TR_EMPLOYED_HD! + !TR_EMPLOYED_IAD! + !TR_EMPLOYED_kolo! + !TR_EMPLOYED_pesi!", "PYTHON_9.3")
	
	#adds two new fields to check correctness of the calculations of ratio total revenue (if sum = 1 , the calculations are correct)
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
