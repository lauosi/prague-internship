import arcpy
from arcpy import env
import os

'''
Calculates the distance to the horse statue on the Wenceslas Square (Václavské náměstí formerly known as Koňský trh). 
'It is probably the best-known Prague statue, and also a very popular meeting place of Prague citizens is the St. Wenceslas Monument in the upper part of the Wenceslas Square. 
It represents the patron of the country, St. Wenceslas, the Duke of Bohemia in the 10 th century. 
This monument saw many important events of Czech history, including the establishment of the independent republic Czechoslovakia in 1918.' 
(http://www.prague.cz/st-wenceslas-monument/) 
'''
zones_in = arcpy.GetParameterAsText(0)
results = arcpy.GetParameterAsText(1)

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
	
	#creates the horse statue
	horse = arcpy.Point()
	horse.X = -742324.618979
	horse.Y = -1043941.435188
	theHorse = arcpy.PointGeometry(horse)
	arcpy.CopyFeatures_management(theHorse, r"C:\Esri\temp_data.gdb\theHorseStatue")
	arcpy.AddMessage("Successful location retrieval. The Horse Statue FC has been created.")
	
	#creates draf version of the zones_in feature class
	arcpy.Select_analysis(zones_in,"calculationRegions")
	arcpy.AddField_management("calculationRegions","ZONE_ID","LONG")
	arcpy.CalculateField_management("calculationRegions", "ZONE_ID", "!OBJECTID!", "PYTHON_9.3")
	arcpy.AddMessage("Successful field addition.")
	
	#transforms polygons into points
	arcpy.FeatureToPoint_management("calculationRegions", "RegToPoints", "CENTROID")
	arcpy.AddMessage("Successful transformation polygons to points.")
	
	#creates the output table with distances 
	arcpy.PointDistance_analysis("RegToPoints", "theHorseStatue", "distToHorse")
	arcpy.AddMessage("Successful calculation of distance.")
	
	#joins table with distances with table of zones
	arcpy.JoinField_management("calculationRegions", "ZONE_ID", "distToHorse", "INPUT_FID", "DISTANCE")
	
	# changes the name and lets people know what the DISTANCE field contains 
	arcpy.AlterField_management('calculationRegions', 'DISTANCE', 'odKone', 'odKone')
	
	# gives the proper name to the output file
	arcpy.Select_analysis("calculationRegions", results)
	arcpy.AddMessage("Your feature class was successfully created: {0}".format(results))
	
	# cleans this mess up
	arcpy.Delete_management(TEMP)
	arcpy.AddMessage("Temporary directory was deleted.")
	arcpy.AddMessage("Thank you for using Help Tools, have a nice day. <('')")

except arcpy.ExecuteError:
	msgs = arcpy.GetMessages(2)
	arcpy.AddError(msgs)
	
except:
    arcpy.AddError("Operation failed. Your feature class was not created.") 
