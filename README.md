# Twitter Sentiment Analysis on Google Cloud Platform (GCP)
# Highlights
This project performs near real time twitter sentiment analysis on Google Cloud Platform. It accepts a keyword parameter (or none) as input. Then displays a graphical representation of the sentiment of incoming tweets, updated in near real-time. It also allows to filter the tweets based on the keyword and include only those tweets containing the keyword. It continues to update automatically as new tweets arrive, until the application is closed.

Here is the sample of the output charts generated: -

![alt text](https://github.com/gchandn3413/Sentiment_Analysis_GCP/blob/master/Application_output.png)

# Design
It works with python 3.7.x. It primarly consists of calling twitter api to fetch real time tweets and utilizing GCP features for sentiment score and storage. Below is the design: -

![alt text](https://github.com/gchandn3413/Sentiment_Analysis_GCP/blob/master/Application_design.png)
