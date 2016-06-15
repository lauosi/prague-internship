import arcpy
from arcpy import env
import os
import sys

'''
Calculates the Travel Ratio (TR considering different means of transport) for residents and employed in given zones
'''

zones_in = arcpy.GetParameterAsText(0)
rings_in = arcpy.GetParameterAsText(1)
results = arcpy.GetParameterAsText(2)
TABULKA = arcpy.GetParameterAsText(3)
ZSJ = arcpy.GetParameterAsText(4)
RESIDENTS = arcpy.GetParameterAsText(5)
EMPLOYED = arcpy.GetParameterAsText(6)

#*************************************************START helper*************************************************
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
env.workspace = "C:\\Esri\\temp_data.gdb" 
KODNAZEV = [1, 2, 3, 4, 5]
numRing = ["0", "1", "2", "3", "4", "5"]	

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
	arcpy.Select_analysis(ZSJ,"RegionsHomeToSelect")
	arcpy.Select_analysis(rings_in,"pasmaMesta")
	# gets rid of <Null> values in distance field
	arcpy.CalculateField_management(TABULKA, "VZDALENOST", "r(!VZDALENOST!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0") 
	arcpy.TableSelect_analysis(TABULKA, "TABULKA", "VZDALENOST > 0")
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions 
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	# ading an information about the ring to each ZSJ
	arcpy.MakeFeatureLayer_management ("pasmaMesta", "pasmaMesta_view")
	arcpy.MakeFeatureLayer_management ("RegionsHomeToSelect", "ZSJ_COPY")
	arcpy.AddField_management("ZSJ_COPY","NoRing","LONG")
	arcpy.AddMessage("Successful layer creation.")
	
	for kod in KODNAZEV:
		arcpy.SelectLayerByAttribute_management ("pasmaMesta_view", "NEW_SELECTION", "OBLAST = "+str(kod))
		arcpy.SelectLayerByLocation_management ("ZSJ_COPY", "HAVE_THEIR_CENTER_IN", "pasmaMesta_view")
		arcpy.CalculateField_management("ZSJ_COPY", "NoRing", kod, "PYTHON_9.3")
		arcpy.SelectLayerByAttribute_management ("ZSJ_COPY", "CLEAR_SELECTION")
	arcpy.Delete_management ("ZSJ_COPY")
	arcpy.AddMessage("Successful ring num addidtion.")
	
	joinFieldImported("TABULKA", "DOPR_ZSJDPS_KOD", "RegionsHomeToSelect", "KOD_ZSJ7", "NoRing")
	arcpy.AddMessage("Successful join.")
	
	arcpy.CalculateField_management("TABULKA", "NoRing", "r(!NoRing!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
    # creates flaten tables for HOME and for WORK
	arcpy.Statistics_analysis ("TABULKA", "tabulka_home", [["VZDALENOST", "SUM"], ["CELKEM", "SUM"], ["Celkem_os_HD", "SUM"], ["Celkem_os_IAD", "SUM"], ["Celkem_os_kolo", "SUM"], ["Celkem_os_pesi", "SUM"]], ["DOPR_ZSJDOP_KOD", "NoRing"])
	arcpy.AddMessage("Successful calculation of values in the HOME and WORK tables.")
    
	# pivoting
	arcpy.PivotTable_management ("tabulka_home", "DOPR_ZSJDOP_KOD", "NoRing", "SUM_CELKEM", "pivot_TOTAL")
	joinFieldImported("RegionsHomeToSelect", "KOD_ZSJ7", "pivot_TOTAL", "DOPR_ZSJDOP_KOD", "NoRing0;NoRing1;NoRing2;NoRing3;NoRing4;NoRing5")
	arcpy.AddMessage("Successful join.")
	
	for num in numRing:
		arcpy.AddField_management("RegionsHomeToSelect","podilZSJ"+num,"FLOAT")
		arcpy.CalculateField_management("RegionsHomeToSelect", "podilZSJ"+num, "!NoRing"+num+"!/(!NoRing0!+!NoRing1!+!NoRing2!+!NoRing3!+!NoRing4!+!NoRing5!)", "PYTHON_9.3")
	
	# provides ID and divide areas
	arcpy.Intersect_analysis(["calculationRegions", "RegionsHomeToSelect"], "RegionsHome_inters")
	arcpy.Intersect_analysis(["calculationRegions", "RegionsHomeToSelect"], "RegionsWork_inters")
	arcpy.AddMessage("Successful intersection.")
	
	# calculates the number of residents in intersected zones
	arcpy.Intersect_analysis([RESIDENTS,"RegionsHome_inters"], "ResidentsInIntersected", "ALL", "0.1 METERS", "INPUT")
	arcpy.AddMessage("Successful intersection with RESIDENTS.")
	
	arcpy.Dissolve_management("ResidentsInIntersected", "RESIDENTSInInt", ["KOD_ZSJ7", "ZONE_ID"], "PTOTAL SUM")
	
	arcpy.JoinField_management("RESIDENTSInInt","KOD_ZSJ7","ResidentsInIntersected","KOD_ZSJ7", ["podilZSJ0", "podilZSJ1", "podilZSJ2", "podilZSJ3", "podilZSJ4", "podilZSJ5"])
	
	for num in numRing:
		arcpy.AddField_management("RESIDENTSInInt", "WorkInRingInt"+num,"LONG")
		arcpy.CalculateField_management("RESIDENTSInInt", "WorkInRingInt"+num, "!podilZSJ"+num+"!*!SUM_PTOTAL!", "PYTHON_9.3")
	
	arcpy.Dissolve_management("RESIDENTSInInt", "RESIDENTSInZones", "ZONE_ID", " WorkInRingInt0 SUM; WorkInRingInt1 SUM; WorkInRingInt2 SUM; WorkInRingInt3 SUM; WorkInRingInt4 SUM; WorkInRingInt5 SUM")
	
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
		arcpy.AddField_management("RESIDENTSInZones", "podil_oblast"+num,"FLOAT")
		arcpy.CalculateField_management("RESIDENTSInZones", "podil_oblast"+num, "!WorkInRing"+num+"!/!SumWorkingRing!", "PYTHON_9.3")
		
	arcpy.JoinField_management("calculationRegions", "ZONE_ID", "RESIDENTSInZones", "ZONE_ID", ["WorkInRing0","WorkInRing1","WorkInRing2","WorkInRing3","WorkInRing4","WorkInRing5","RatioInRing0","podil_oblast1","podil_oblast2","podil_oblast3","podil_oblast4","podil_oblast5"])
	
	arcpy.AlterField_management ("calculationRegions", "WorkInRing0", "prac_v_oblast_0", "prac_v_oblast_0")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing1", "prac_v_oblast_1", "prac_v_oblast_1")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing2", "prac_v_oblast_2", "prac_v_oblast_2")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing3", "prac_v_oblast_3", "prac_v_oblast_3")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing4", "prac_v_oblast_4", "prac_v_oblast_4")
	arcpy.AlterField_management ("calculationRegions", "WorkInRing5", "prac_v_oblast_5", "prac_v_oblast_5")
	
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
