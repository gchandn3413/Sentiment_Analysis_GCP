#!/bin/bash

#install/update packages
sudo apt-get update -f -y --force-yes
sudo apt install python3-pip -f -y --force-yes
sudo apt-get install vim -f -y --force-yes
sudo apt-get install git -f -y --force-yes
#sudo apt install tcl-dev tk-dev python-tk python3-tk

#install python libraries
pip3 install tweepy
pip3 install google-cloud-language
pip3 install google-cloud-storage
pip3 install configparser
pip3 install matplotlib
pip3 install nltk

gs_bucket_name="sentiment_analysis_gaurav"

cd ~
if [ ! -d "temp_git_checkout" ]; then
  mkdir temp_git_checkout
fi

if [ ! -d "sentiment_analysis_deployment" ]; then
  mkdir sentiment_analysis_deployment
fi


cd temp_git_checkout
git clone https://github.com/gchandn3413/Sentiment_Analysis_GCP.git

cd ~/sentiment_analysis_deployment
cp ~/temp_git_checkout/Sentiment_Analysis_GCP/* .

gsutil cp index.html gs://$gs_bucket_name