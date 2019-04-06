# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 13:45:35 2019

@author: Gaurav-PC
"""

#import necessary libraries
import unittest
import configparser
import os
import sentiment_analysis_gcp as sent
from google.cloud import storage

#This class performs the testing for twitter sentiment analysis.
#It contains test functionalities for - fetching the tweets,
#getting the sentiment score and uploading into GS
class TestSentimentAnalysisGCP(unittest.TestCase):
    #define intial variables
    ClassIsSetup = False
    
    #load the configurations file which contains key-values for the script
    CONFIG = configparser.ConfigParser()
    CONFIG.read("test_sentiment_analysis.config")
    
    #Twitter credentials assigned from configuration file
    ACC_TOKEN = str(CONFIG.get('TWEETER', 'ACC_TOKEN'))
    ACC_SECRET = str(CONFIG.get('TWEETER', 'ACC_SECRET'))
    CONS_KEY = str(CONFIG.get('TWEETER', 'CONS_KEY'))
    CONS_SECRET = str(CONFIG.get('TWEETER', 'CONS_SECRET'))

    #The setup and setupClass functions are used to perform the intial setup i.e. fetching the tweets.
    def setUp(self):
        if not self.ClassIsSetup:
            print("****Initializing testing enviornment****")
            self.setupClass()
            self.__class__.ClassIsSetup = True
    
    #This function used to limit the initialization i.e. fetching the tweets
    #only once and not before each test function. 
    #This helps in effectively utilizing the system resources.
    def setupClass(self):
        print("****In setup..****")
        unittest.TestCase.setUp(self)
        
        sent.num_days = 4
        global search_results_tweets
        
        #get the list of tweets from the main script
        search_results_tweets = list(sent.search_tweets('sports',int(self.CONFIG.get('GENERAL', 'NUM_TWEETS'))))
        
        #set the gcp credential to the env variables
        global gcp_credentials_path
        gcp_credentials_path = str(self.CONFIG.get('GCP', 'GCP_CRED_PATH'))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_credentials_path
        print(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
    
    #This function tests whether the object has been uploaded to
    #GS bucket or not.
    def test_bucket_object(self):
        ret_val=False
        
        #establish the connection to GS
        storage_client = storage.Client.from_service_account_json(str(self.CONFIG.get('GCP', 'GCP_CRED_PATH')))
        bucket = storage_client.get_bucket(str(self.CONFIG.get('GENERAL', 'GS_BUCKET')))
            
        #Get the list of the objects
        blobs = bucket.list_blobs()
        
        #check to see if desired object is present in the GS or not
        for blob in blobs:
            if str(self.CONFIG.get('GCP', 'UPLOADED_OBJ_NAME')) == str(blob.name):
                ret_val=True
        
        self.assertEqual(ret_val,True)
        
    #This function tests whether the sentiment score returned from the 
    #GCP NLP service is between -1.0 and 1.0 or not.
    def test_score(self):
        withInRange = False
        for tweet in search_results_tweets:
            #Clean tweets
            clean_tweet = sent.clean_tweets(tweet.text.encode('utf-8'))
            #Get Sentiment score
            sentiment_score = sent.get_sentiment_score(clean_tweet)
            
            #check is the score with in the range or not
            if -1.0 <= sentiment_score <= 1.0:
                withInRange = True
            else:
                withInRange = False
        
        self.assertEqual(withInRange,True)
    
    #This function tests whether the number of tweets returned from twitter is
    #as per desired count or not.
    def test_tweetsCount(self):
        ret_cnt = 0
        for tweet in search_results_tweets:
            ret_cnt += 1
        
        self.assertEqual(ret_cnt, int(self.CONFIG.get('GENERAL', 'NUM_TWEETS')))
        
#main method
if __name__ == '__main__':
    unittest.main()