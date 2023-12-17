# ACCAnalyzer
 
ACC Analyzer is an application that takes session data produced by ACC Results Companion and performs a session analysis.

## Features

- Overall race analysis
    - Position graph
    - Gap to car ahead graph
    - Laps driven by each driver
- Stint analysis for each stint
    - Laps driven in the stint
    - Lap time graph, average lap time, exclude laps above a threshold 
   	- Histogram of lap times 
   	- Starting/ending fuel
   	- Lap time standard deviation
   	- Same metrics for sector times
    - Excluded lap numbers
   	- Conditions: track grip, rain, tyre used
   	- Temperatures: ambient and track
- Saving the analysis to a PDF file
- Configurable settings
- Additional analysis parameters

## How to use

- Download the latest release.
- Extract the files.
- Follow the quick start guide found in the readme.txt file.

## Known issues & limitations

- The first lap gets removed if starting fuel is zero in the data.
- The analysis may fail if a stint only has an outlap or not enough quick laps.
- Starting fuel displayed is actually the amount of fuel after lap 1 (the actual starting value is not available).
- Splitting the laps into stints does not work on other drivers in the team (some data from other drivers is missing).
