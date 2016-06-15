import arcpy
from arcpy import env
import os

'''
Here is the description

'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
buildStructure= arcpy.GetParameterAsText(2)

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
	
	# assigns an ID number to the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	
	arcpy.AddMessage("Successful field addition.")
	
	# selects required types of building structure 
	arcpy.Select_analysis(buildStructure,"buildStSelected", "CHARAKTER IN ( 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10 , 11 )")
	
	arcpy.AddMessage("Successful selection.")
	
	# provides ID for building structure polygons 
	arcpy.Intersect_analysis(["calculationRegions", "buildStSelected"], "buildStr_inters", "ALL", "0.1 METERS", "INPUT")
	
	arcpy.AddMessage("Successful intersection.")
	
	# creates reversed table 
	arcpy.PivotTable_management("buildStr_inters", "ZONE_ID", "CHARAKTER", "SHAPE_Area", "pivot_struct")
	
	arcpy.AddMessage("Successful pivot table creation.")
	
	# calculates summary statistics for fields in pivot_struct table
	#arcpy.Statistics_analysis ("pivot_struct", "pivot_struct_flat", [["CHARAKTER1", "SUM"], ["CHARAKTER2", "SUM"], ["CHARAKTER3", "SUM"], ["CHARAKTER4", "SUM"], ["CHARAKTER5", "SUM"], ["CHARAKTER6", "SUM"], ["CHARAKTER7", "SUM"], ["CHARAKTER8", "SUM"], ["CHARAKTER9", "SUM"]], "ZONE_ID")
	arcpy.Statistics_analysis ("pivot_struct", "pivot_struct_flat", [["CHARAKTER1", "SUM"], ["CHARAKTER2", "SUM"], ["CHARAKTER3", "SUM"], ["CHARAKTER4", "SUM"], ["CHARAKTER5", "SUM"], ["CHARAKTER6", "SUM"], ["CHARAKTER7", "SUM"], ["CHARAKTER8", "SUM"], ["CHARAKTER9", "SUM"], ["CHARAKTER10", "SUM"], ["CHARAKTER11", "SUM"]], "ZONE_ID")
	
	arcpy.AddMessage("Successful table flattening.")
	
	arcpy.JoinField_management("calculationRegions","ZONE_ID","pivot_struct_flat","ZONE_ID", ["SUM_CHARAKTER1", "SUM_CHARAKTER2", "SUM_CHARAKTER3", "SUM_CHARAKTER4", "SUM_CHARAKTER5", "SUM_CHARAKTER6", "SUM_CHARAKTER7", "SUM_CHARAKTER8", "SUM_CHARAKTER9", "SUM_CHARAKTER10", "SUM_CHARAKTER11"])

	# alters the fields name 
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER1", "rostla_zastavba")
	arcpy.AddField_management("calculationRegions","podil_rostla_zast","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_rostla_zast", "[rostla_zastavba] / [SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER2", "blokova_zastavba")
	arcpy.AddField_management("calculationRegions","podil_blokova_zast","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_blokova_zast", "[blokova_zastavba]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER3", "zahradni_mesto")
	arcpy.AddField_management("calculationRegions","podil_zahradni_mesto","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_zahradni_mesto", "[zahradni_mesto]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER4", "modernisticka_zastavba")
	arcpy.AddField_management("calculationRegions","podil_modernisticka","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_modernisticka", "[modernisticka_zastavba]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER5", "vesnice")
	arcpy.AddField_management("calculationRegions","podil_vesnice","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_vesnice", "[vesnice]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER6", "heterogenni_zastavba")
	arcpy.AddField_management("calculationRegions","podil_heterogenni_zast","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_heterogenni_zast", "[heterogenni_zastavba]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER7", "areal_vybavenost")
	arcpy.AddField_management("calculationRegions","podil_areal_vybav","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_areal_vybav", "[areal_vybavenost]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER8", "areal_produkce")
	arcpy.AddField_management("calculationRegions","podil_areal_prod","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_areal_prod", "[areal_produkce]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER9", "areal_rekreace")
	arcpy.AddField_management("calculationRegions","podil_areal_rekr","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_areal_rekr", "[areal_rekreace]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER10", "linearni_struktura")
	arcpy.AddField_management("calculationRegions","podil_linearni_str","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_linearni_str", "[linearni_struktura]/[SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "SUM_CHARAKTER11", "jina_struktura_mesta")
	arcpy.AddField_management("calculationRegions","podil_jina_strukt","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "podil_jina_strukt", "[jina_struktura_mesta]/[SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful alteration of fields names.")
	
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