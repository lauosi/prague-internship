import arcpy
from arcpy import env
import os

'''
here is the description
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
TechnicalInfrastructure = arcpy.GetParameterAsText(2)

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
	arcpy.Select_analysis(zones_in, "calculationRegions")
	arcpy.AddMessage("Successful selection.")
	
	# KATEGORIZACE PODLE DRUHU VEDENI
	expr_2= '''
	def druh_vedeni(kod):
		if kod >= 106081 and kod <= 121800:
			return "kanalizace"
		elif kod >= 306081 and kod <= 321800:
			return "plynovod"
		elif kod >= 206081 and kod <= 206831:
			return "kolektor"
		elif kod >= 406081 and kod <= 421800:
			return "vodovod"
		elif kod >= 506081 and kod <= 521851:
			return "teplovod"
		elif kod >= 605161 and kod <= 621851:
			return "silnoproud"
		elif kod >= 706010 and kod <= 736751:
			return "slaboproud"
		elif kod >= 806081 and kod <= 821851:
			return "produktovod"
		elif kod >= 906081 and kod <= 921800:
			return "potrubni_posta"
		elif kod >= 252180 and kod <= 282187:
			return "neurceno"
	'''
	lokality_TI = arcpy.Intersect_analysis (["calculationRegions", TechnicalInfrastructure], "lokality_TI", "ALL", "", "")
	arcpy.AddMessage("Successful intersection.")
	arcpy.AddField_management("lokality_TI", "druh_ti", "TEXT")
	arcpy.CalculateField_management("lokality_TI", "druh_ti", "druh_vedeni(!CTMTP_KOD!)", "PYTHON_9.3", expr_2)
	lokality_TI_diss = arcpy.Dissolve_management("lokality_TI", "lokality_TI_diss",["NAZEV", "druh_ti"], "SHAPE_Length SUM", "MULTI_PART", "DISSOLVE_LINES")
	arcpy.AddMessage("Successful dissolution.")
	arcpy.PivotTable_management("lokality_TI_diss", "NAZEV", "druh_ti", "SUM_SHAPE_Length", "lokality_TI_pivot")
	arcpy.AddMessage("Successful table flattening.")
	joinFieldImported("calculationRegions" ,"NAZEV" ,"lokality_TI_pivot", "NAZEV", "kanalizace;plynovod;kolektor;vodovod;teplovod;silnoproud;slaboproud;produktovod;potrubni_posta;neurceno")
	
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
