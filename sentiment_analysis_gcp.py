# -*- coding: utf-8 -*-
"""
@author: Gaurav-PC
"""
#The purpose of this script is to facilitate near real-time twitter sentiment analysis using 
#Google cloud platform services. It takes 2 mandatory and 1 option arugments. 2 mandatory arguments
#include - (a) # of days back from current date from which #the twitter sentiment analysis
#should be performed. (b) location of the json file which contains the credentials to hit Twitter
#service. 1 optional argument is the keyword (if the tweets need to be filtered)

#import necessary libraries
import re
import time
import configparser
import os
from argparse import ArgumentParser
from threading import Thread
from datetime import datetime, timedelta
import tweepy
import matplotlib.pyplot as plt
from nltk.tokenize import WordPunctTokenizer
from google.cloud import storage
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

#load the configurations file which contains key-values for the script
CONFIG = configparser.ConfigParser()
CONFIG.read("sentiment_analysis.config")
    
#Twitter credentials assigned from configuration file
ACC_TOKEN = str(CONFIG.get('TWEETER', 'ACC_TOKEN'))
ACC_SECRET = str(CONFIG.get('TWEETER', 'ACC_SECRET'))
CONS_KEY = str(CONFIG.get('TWEETER', 'CONS_KEY'))
CONS_SECRET = str(CONFIG.get('TWEETER', 'CONS_SECRET'))

#Mixed = 0.0, 0.0> and >=0.3 is positive, 0.0>and <0.3 neutral , <0.0 is negative

#initialize vars
NUM_POSITIVE = 0
NUM_NEGATIVE = 0
NUM_MIXED = 0
NUM_NEUTRAL = 0

#This functions returns an api object from Twitter upon verifying credentials provided.
#It takes 4 arguments - ACC_TOKEN, ACC_SECRET, CONS_KEY, CONS_SECRET.
def authentication(cons_key, cons_secret, acc_token, acc_secret):
    auth = tweepy.OAuthHandler(cons_key, cons_secret)
    auth.set_access_token(acc_token, acc_secret)
    api = tweepy.API(auth)
    return api

#This function performs the search tweets by connection to the twitter api 
#based on the keyword provided or None.
#It takes 2 arguments - # of days back from current date from which the twitter sentiment analysis
#should be performed and the search keyword
def search_tweets(keyword, total_tweets):
    today_datetime = datetime.today().now()
    yesterday_datetime = today_datetime - timedelta(days=num_days)
    yesterday_date = yesterday_datetime.strftime('%Y-%m-%d')
    
	#authenticate
    api = authentication(CONS_KEY, CONS_SECRET, ACC_TOKEN, ACC_SECRET)
    
    if keyword:
        print("Keyword: " + keyword)
        search_result = tweepy.Cursor(api.search, q=keyword, since=yesterday_date, result_type='recent', lang='en').items(total_tweets)
    else:
        print("Keyword: " + keyword)
        search_result = tweepy.Cursor(api.user_timeline, id=str(CONFIG.get('GENERAL', 'TWEETER_ID')), since=yesterday_date, result_type='recent').items(total_tweets)

    return search_result

#This funtion cleans the tweets returned from Twitter. It removes junk characters, special symbols
#, numbers and lower case. It takes only one argument i.e. the tweet and returns a cleaned tweet.
def clean_tweets(tweet):
    user_removed = re.sub(r'@[A-Za-z0-9]+', '', tweet.decode('utf-8'))
    link_removed = re.sub('https?://[A-Za-z0-9./]+', '', user_removed)
    number_removed = re.sub('[^a-zA-Z]', ' ', link_removed)
    lower_case_tweet = number_removed.lower()
    tok = WordPunctTokenizer()
    words = tok.tokenize(lower_case_tweet)
    clean_tweet = (' '.join(words)).strip()
    return clean_tweet

#This function takes a tweet, constructs a document and identifies the sentiment score by calling
#GCP Sentiment analysis API. IT returns sentiment score. The score can range btw -1.0 to 1.0.
def get_sentiment_score(tweet):
    client = language.LanguageServiceClient()
    document = types.Document(content=tweet, type=enums.Document.Type.PLAIN_TEXT)
	#Call GCP Sentiment Analysis API
    sentiment_score = client.analyze_sentiment(document=document).document_sentiment.score
    return sentiment_score

#This functions plots 2 pie charts, one representing the tweets category since the start 
#of the application and another representing the last run. It also uploads the pie charts to
#Google Storage bucket.
#The tweets are categorized in 4 category based on the following score -
#Mixed = 0.0, 0.0> and >=0.3 is positive, 0.0>and <0.3 neutral , <0.0 is negative
def plot_chart(local_num_positive, local_num_mixed, local_num_neutral, local_num_negative):
    labels = 'positive', 'mixed', 'netural', 'negative'
    colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']
    explode = (0.1, 0, 0, 0)  # explode 1st slice
    sizes_overall = [NUM_POSITIVE, NUM_MIXED, NUM_NEUTRAL, NUM_NEGATIVE]
    sizes_lst_run = [local_num_positive, local_num_mixed, local_num_neutral, local_num_negative]

    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.set_title('Since Start')
    ax1.pie(sizes_overall, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140, radius=1.0)

    ax2.set_title('Last Run')
    ax2.pie(sizes_lst_run, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140, radius=.6)

    plt.axis('equal')
    plt.savefig('sentiments_plot.png')
    plt.close(fig)
	#calling upload to Google Storage bucket
    uploaded_loc = upload_to_bucket('sentiments_plot.png', 'sentiments_plot.png', str(CONFIG.get('GENERAL', 'GS_BUCKET')))
    print("Uploaded to GS location: " + str(uploaded_loc))

#This function uploads the pie chart to the Google Storage Bucket and returns the public URL path_to_file.
#It takes 3 arguments - image name, path to the file and the bucket name
def upload_to_bucket(blob_name, path_to_file, bucket_name):
    storage_client = storage.Client.from_service_account_json(gcp_cred_loc)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
	#To avoid server level caching
    blob.cache_control = "no-cache, max-age=0"
    blob.upload_from_filename(path_to_file)
    #returns a public url
    return blob.public_url

#This is the worker class which assigns a thread to perform the following steps and then sleeps for
#a configurable amount of time. The run function is a forever running loop until killed explicitly
#Steps performed - (1) Get the real time tweets (2) Clean tweets (3) Get sentiment score by calling
# GCP API (4) Assign categories (5) plot chart (6) Upload to GS. 
class worker(Thread):
    def run(self):
        while True:
        #for x in range(1,2):
            local_num_negative = 0
            local_num_mixed = 0
            local_num_neutral = 0
            local_num_positive = 0
            try:
				#Get Tweets
                tweets = search_tweets(search_keyword, int(CONFIG.get('GENERAL', 'NUM_TWEETS')))
                for tweet in tweets:
					#Clean tweets
                    clean_tweet = clean_tweets(tweet.text.encode('utf-8'))
					#Get Sentiment score
                    sentiment_score = get_sentiment_score(clean_tweet)
					#Assign Categories
                    if sentiment_score < 0.0:
                        global NUM_NEGATIVE
                        NUM_NEGATIVE += 1
                        local_num_negative += 1
                    elif  sentiment_score == 0.0:
                        global NUM_MIXED
                        NUM_MIXED += 1
                        local_num_mixed += 1
                    elif sentiment_score > 0.0 and sentiment_score < 0.3:
                        global NUM_NEUTRAL
                        NUM_NEUTRAL += 1
                        local_num_neutral += 1
                    else:
                        global NUM_POSITIVE
                        NUM_POSITIVE += 1
                        local_num_positive += 1
            except tweepy.error.TweepError:
                time.sleep(60*15)
                continue
            
			#Plot chart
            plot_chart(local_num_positive, local_num_mixed, local_num_neutral, local_num_negative)
            print('Sleeping now------')
			#Sleeps
            time.sleep(int(CONFIG.get('GENERAL', 'SLEEP_INTERVAL')))
            print('Sleeping completed---------')
            print('Sentiments since start --- ')
            print(' NUM_NEGATIVE: {}\n NUM_MIXED: {}\n NUM_NEUTRAL: {}\n NUM_POSITIVE: {}\n'.format(NUM_NEGATIVE, NUM_MIXED, NUM_NEUTRAL, NUM_POSITIVE))

#This function starts the thread.
def perform_work():
    worker().start()

#This is the main driver function of the script. It takes 2 mandatory and 1 option arugments.
#2 mandatory arguments include - (a) # of days back from current date from 
# which #the twitter sentiment analysis #should be performed. 
#(b) location of the json file which contains the credentials to hit Twitter
#service. 1 optional argument is the keyword (if the tweets need to be filtered)
if __name__ == '__main__': 
    #Input agrs
    parser = ArgumentParser(usage='%(prog)s [options]')
    try:
        parser.add_argument("-k", "--search_keyword", help="Search Keyword", action="store", dest="search_keyword", required=False) 
        parser.add_argument("-d", "--num_days", help="Number of days back from today for starting the sentiment analysis", action="store", dest="num_days", required=True)
        parser.add_argument("-i", "--gcp_cred_loc", help="Path of the GCP service credential json file", action="store", dest="gcp_cred_loc", required=True)
        inpArgs = parser.parse_args()
    except Exception as e:
        parser.print_help()

    global search_keyword
    search_keyword = str(inpArgs.search_keyword)
    global num_days
    num_days = int(inpArgs.num_days)
    global gcp_cred_loc
    gcp_cred_loc = str(inpArgs.gcp_cred_loc)

    print('Search Keyword provided : ', search_keyword)
    print('Number of days back from today for starting the sentiment analysis : ', num_days)
    print('Path of the GCP service credential json file : ', gcp_cred_loc)
	
	#set the gcp credential to the env variables
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_cred_loc
    print(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
	
	#perform the work
    perform_work()