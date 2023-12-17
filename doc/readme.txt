QUICK START GUIDE:
1. Open settings.ini file in the config folder.
2. Edit the driver name to match the name on ACC Results Companion. 
	-If you have many different names, you can separate them with a comma (no whitespace).
	-The name(s) should include the short name in parentheses.
3. Edit the data_dir to match the folder where you store the data from ACC Results Companion.
4. Edit the out_dir to match where you want the analysis files to be saved.
5. Leave the other parameters unchanged for now.
	-A description of the settings is given below.
6. Export a session from ACC Results Companion as CSV in Variable (Formatted) format in the data_dir folder.
	-To export from ACC Results Companion, choose a session, right click on one of the session laps and choose "Export as CSV".
7. Export the same session in Fixed format in the same folder.
	-The name of the fixed format file must be otherwise the same as the Variable format file with "_fixed" at the end .
		-e.g. "Race123.csv" (Variable format) and "Race123_fixed.csv".
8. Launch the application with the "ACC Analyzer" shortcut or "analyzer.exe" executable.
9. Input the Variable format data file name (without .csv).
10. Input the title of the analysis.
11. Input additional parameters (you can leave them empty for now, just press enter to continue).
	-A list of additional parameters is given below.
12. Wait for the analysis to complete. If it is succesful, a PDF file will be saved to out_dir and opened automatically.
13. You can run another analysis or close the console window by pressing enter.


SETTINGS:
-driver:
	-Name of the driver to analyze, including the short name in parentheses.
	-You can have multiple driver names here, separate them with a comma (no whitespace).
	-The name(s) should match the one(s) on ACC Results Companion.
	-Capitalization does not matter.
-data_dir:
	-Directory the application searches for session data.
	-Save your .csv files from ACC Results Companion here.
out_dir:
	-Directory where the analysis files are saved.
outlier_margin:
	-This controls how easily laps are excluded from the analysis.
	-With lower values, laps are excluded more easily.
	-Increase this if you find that too many laps are beind excluded.
	-You can also input this as an additional parameter (see below).
	-If the session weather was variable, a higher value may be needed.
	-For static optimum conditions, a fairly low value can be used.
	-It's recommended to generally keep this between 0.005 and 0.04
comparison_lap_count:
	-It's recommended to keep this at 3 unless you know what you're doing.
comparison_lap_add_margin
	-It's recommended to keep this at 0.1 unless you know what you're doing.
fit_degree:
	-The degree of the fitted curve for the lap and sector times.
	-Should usually be kept at 2.
	-3 or even 4 can be ok in some cases
	-You can also input this as an additional parameter (see below).
plot_dpi:
	-Resolution of the plot images in dots per inch.
	-Higher values increase analysis time and file size.
	-300 is the recommended value.


ADDITIONAL PARAMETERS:
-Can be used to perform the analysis with non-default parametes (these override the default settings)
-To use multiple additional parameters, separate them with a comma
	-e.g. om=0.2,fd=3,sr,lta=3-26
-Outlier margin: 
	-usage: om=...
	-e.g. om=0.2
-Fit degree: 
	-usage: fd=...
	-e.g. fd=3
-Skip race analysis: 
	-Leaves out the race analysis part.
	-Intended for analyzing practice sessions.
	-Usage: sr
-Laps to analyze: 
	-Can be used to analyze only certain laps (intervals).
	-Multiple lap intervals can be separated with a semicolon.
	-usage: lta=...
		-e.g. lta=3-26;55-79;101-150
