# Twitter Sentiment Analysis on Google Cloud Platform (GCP)
# Highlights
This project performs near real time twitter sentiment analysis on Google Cloud Platform. It accepts a keyword parameter (or none) as input. Then displays a graphical representation of the sentiment of incoming tweets, updated in near real-time. It also allows to filter the tweets based on the keyword and include only those tweets containing the keyword. It continues to update automatically as new tweets arrive, until the application is closed.

The output contains 2 charts.
1. "Since Start" - displays the live trend based on the # of days back from current date from which the application was started.
2. "Last Run" - displays the live trend for the last x seconds (configurable).

Here is the sample of the output charts generated: -

![alt text](https://github.com/gchandn3413/Sentiment_Analysis_GCP/blob/master/Application_output.png)

# Design
It works with python 3.7.x. It primarly consists of calling twitter api to fetch real time tweets and utilizing GCP features for sentiment score and storage. Below is the design: -

![alt text](https://github.com/gchandn3413/Sentiment_Analysis_GCP/blob/master/Application_design.png)

# Limitations
1. Twitter API has limitation on the number of tweets search for. To avoid any twitter errors on the number of tweets looked for, I am looking for 15 tweets in an interval of 30 secs. Both these numbers are configurable, however, the combination of fetching 15 tweets in an interval of 30 secs works well.
2. This application is near real-time in nature.

# Auto Deployment
This repo contains deployment_twitter_analysis.sh which can be executed in any Linux based compute engine to auto deploy the application. Below is the command - 

sh deployment_twitter_analysis.sh

# Execution
To execute the application, below is the command. It takes 3 arguments with below options - 
-k -- Search Keyword
-d -- Number of days back from today for starting the sentiment analysis
-i -- Path of the GCP service credential json file

nohup python3 sentiment_analysis_gcp.py -d 4 -i /home/gaurav_chandna02/sentiment_analysis_gcp/cred.json -k india >> out.log &
