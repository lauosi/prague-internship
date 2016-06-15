import arcpy
from arcpy import env
import os

'''
Calculates the areas of impervious public spaces and biologically active public space and counts their ratios to the area of calculation regions
'''
# creates parameters
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)
landUseLayer = arcpy.GetParameterAsText(2)
technicalMap = arcpy.GetParameterAsText(3)

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
	arcpy.AddMessage("Processing can take few minutes. Be patient :)")

	# selects the proper polygons from land use feature class, technical map and creates draf version of the zones_in feature class
	arcpy.Select_analysis(zones_in, "calculationRegions")
	arcpy.Select_analysis(landUseLayer,"landUsePublic", "KOD = 'RPH' OR KOD = 'RPP' OR KOD = 'RPU' OR KOD = 'VC' OR KOD = 'VM' OR KOD = 'VN' OR KOD = 'VPM' OR KOD = 'VPN' OR KOD = 'VPP'")
	arcpy.Select_analysis(technicalMap,"pavedAreas", "CTVUK_KOD = 600 OR CTVUK_KOD = 601 OR CTVUK_KOD = 602 OR CTVUK_KOD = 603 OR CTVUK_KOD = 604 OR CTVUK_KOD = 700 OR CTVUK_KOD = 701 OR CTVUK_KOD = 702 OR CTVUK_KOD = 703 OR CTVUK_KOD = 704 OR CTVUK_KOD = 705 OR CTVUK_KOD = 1003")

	# creates new feature classes with impervious public spaces and biologically active public spaces 
	arcpy.Intersect_analysis(["landUsePublic","pavedAreas"], "PublicImpervious")
	arcpy.Erase_analysis ("landUsePublic", "PublicImpervious", "PublicBiological")
	arcpy.AddMessage("Successful selection.")
	
	# assigns an ID number to all the calculation regions
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	# obtains the ID of the zone in which selected type of public space (imprevious or biological) are located
	arcpy.Intersect_analysis(["calculationRegions","PublicImpervious"], "PublicImpervious_inters")
	arcpy.Intersect_analysis(["calculationRegions","PublicBiological"], "PublicBiological_inters")
	arcpy.AddMessage("Successful intersection.")
	
	# calculates total area of public spaces (imprevious and biological) in the calculation regions 
	arcpy.Dissolve_management("PublicImpervious_inters", "PublicImperviousInZones", "ZONE_ID")
	arcpy.Dissolve_management("PublicBiological_inters", "PublicBiologicalInZones", "ZONE_ID")
	
	arcpy.AddMessage("Successful dissolution.")
	
	# creates the new column for total areas for imprevious and biologically active public spaces 
	arcpy.AddField_management("PublicImperviousInZones","AreaPubImpervious","FLOAT")
	arcpy.CalculateField_management("PublicImperviousInZones", "AreaPubImpervious", "[SHAPE_Area]", "VB")

	arcpy.AddField_management("PublicBiologicalInZones","AreaPubBiological","FLOAT")
	arcpy.CalculateField_management("PublicBiologicalInZones", "AreaPubBiological", "[SHAPE_Area]", "VB")
	
	arcpy.AddMessage("Successful calculation.")
	
	# adds column with calculated areas of imprevious and biologically active public spaces within every calculation region
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PublicImperviousInZones","ZONE_ID", "AreaPubImpervious")
	arcpy.JoinField_management("calculationRegions","ZONE_ID","PublicBiologicalInZones","ZONE_ID", "AreaPubBiological")
	
	# returns 0 if value is None 
	arcpy.CalculateField_management("calculationRegions", "AreaPubImpervious", "r(!AreaPubImpervious!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	arcpy.CalculateField_management("calculationRegions", "AreaPubBiological", "r(!AreaPubBiological!)", "PYTHON_9.3", "def r(x):\\n if x:\\n  return x\\n else:\\n  return 0")
	
	# calculates the ratio of the public spaces areas(imprevious and biological) to the area of calculation regions
	arcpy.AddField_management("calculationRegions","PodilZpevVerProstr","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilZpevVerProstr", "[AreaPubImpervious] / [SHAPE_Area]", "VB")

	arcpy.AddField_management("calculationRegions","PodilNezpevVerProstr","FLOAT")
	arcpy.CalculateField_management("calculationRegions", "PodilNezpevVerProstr", "[AreaPubBiological] / [SHAPE_Area]", "VB")
	
	arcpy.AlterField_management("calculationRegions", "AreaPubImpervious", "ZpevneneVerProstr", "ZpevneneVerProstr")
	arcpy.AlterField_management("calculationRegions", "AreaPubBiological", "NezpevVerProstr", "NezpevVerProstr")
	
	arcpy.CopyFeatures_management ("calculationRegions", results)
	
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



