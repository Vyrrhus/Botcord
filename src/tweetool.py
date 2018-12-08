import tweepy
import asyncio
import src.tool as tool
import requests
from bs4 import BeautifulSoup

async def login():
	# Set API twitter
	
	data = tool.get_data('src/config/twitter/auth.json')
	
	auth = tweepy.OAuthHandler(consumer_key = data['AUTH']['CONSUMER_KEY'], 
							   consumer_secret = data['AUTH']['CONSUMER_SECRET'])
	auth.set_access_token(key = data['AUTH']['ACCESS_TOKEN_KEY'], 
						  secret = data['AUTH']['ACCESS_TOKEN_SECRET'])
	api = tweepy.API(auth)
	return api

async def get_target(api, name):
	try:
		target = api.get_user(name)
		return target
	except:
		return None

async def get_tweet(api, target, since_id=None, created_since=None, exclude_retweets=True, only_retweets=False):
	tweets = []
	if since_id:
		cursor = tweepy.Cursor(api.user_timeline, user_id=target.id, since_id=since_id, exclude_replies=True, tweet_mode="extended")
	else:
		cursor = tweepy.Cursor(api.user_timeline, user_id=target.id, exclude_replies=True, tweet_mode="extended")
	
	for status in cursor.items():
		await asyncio.sleep(0)
		if not since_id:
			try:
				if status.created_at < created_since:
					break
			except:
				print('Forgot created_since=xxxxxx')
				break
		if exclude_retweets:
			if 'RT @' in status.full_text:
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
	
async def get_retweets(api, target, since_id, list_id=None):
	retweets, until_id = await get_tweet(api, target, since_id=since_id, exclude_retweets=False, only_retweets=True)
	if not list_id:
		return retweets, until_id
	
	matching_retweets = []
	for retweet in retweets:
		print(retweet.full_text)
		await asyncio.sleep(0)
		if hasattr(retweet, 'retweeted_status'):
			id_str = retweet.retweeted_status.id_str
		elif hasattr(retweet, 'quoted_status'):
			id_str = retweet.quoted_status.id_str
		else:
			continue
		if id_str in list_id:
			matching_retweets.append(id_str)
	
	return matching_retweets, until_id
	
async def get_tags(tweet):
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

async def get_fav(api, target, list_id):
	fav = []
	for tweet in list_id:
		await asyncio.sleep(0)
		cursor = tweepy.Cursor(api.favorites, user_id=target.id, since_id=int(tweet)-1, max_id=int(tweet)+1)
		for status in cursor.items():
			fav.append(status.id)
		
	return fav