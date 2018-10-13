import tweepy
import src.tool as tool
import requests
from bs4 import BeautifulSoup
from datetime import datetime
#from datetime import timedelta
#import time

from src.config.settings import data

def login():
	# Set API twitter
	auth = tweepy.OAuthHandler(consumer_key = data['TWITTER']['AUTH']['CONSUMER_KEY'], 
							   consumer_secret = data['TWITTER']['AUTH']['CONSUMER_SECRET'])
	auth.set_access_token(key = data['TWITTER']['AUTH']['ACCESS_TOKEN_KEY'], 
						  secret = data['TWITTER']['AUTH']['ACCESS_TOKEN_SECRET'])
	api = tweepy.API(auth)
	return api

def get_target(api, name):
	try:
		target = api.get_user(name)
		return target
	except:
		# Target unreachable
		return None

def get_tweet(api, target, since_id=None, created_since=None, exclude_retweets=True, only_retweets=False):
	tweets = []
	if since_id:
		cursor = tweepy.Cursor(api.user_timeline, user_id=target.id, since_id=since_id, exclude_replies=True)
	else:
		cursor = tweepy.Cursor(api.user_timeline, user_id=target.id, exclude_replies=True)
	
	print('Searching since {} | max : {}'.format(since_id, str(created_since)))
	
	for status in cursor.items():
		print('Status found : {}\nText: {}'.format(str(status.created_at), status.text))
		if not since_id:
			try:
				if status.created_at < created_since:
					break
			except:
				print('Forgot created_since=xxxxxx')
				break
		if exclude_retweets:
			if 'RT @' in status.text:
				continue
		if only_retweets:
			if not hasattr(status, 'retweeted_status') and not hasattr(status, 'quoted_status'):
				continue
				
		tweets.append(status)
	
	if tweets:
		tweets.reverse()
		
	try:
		return tweets, tweets[-1].id
	except:
		# No status found
		return tweets, since_id
	
def get_tags(tweet):
	link = 'https://twitter.com/{}/status/{}'.format(tweet.user.screen_name, tweet.id_str)
	rq = requests.get(link)
	soup = BeautifulSoup(rq.content, 'html.parser')
	content = soup.find_all('div')
	tags = []
	for node in content:
		if 'data-tweet-id' in node.attrs and 'data-tagged' in node.attrs and node['data-screen-name'] == tweet.user.screen_name:
			tag_list = node['data-tagged']
			tags += tag_list.split()
	tags = list(set(tags))
	return tags

def get_fav(api, target, tweet_id):
	fav = []
	cursor = tweepy.Cursor(api.favorites, user_id=target.id, since_id=tweet_id-1, max_id=tweet_id+1)
	
	for status in cursor.items():
		fav.append(status.id)
		
	return fav