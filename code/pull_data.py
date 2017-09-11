
import tweepy
import pandas as pd
### Better is to add this info
### to a text file and pull it in

access_info = pd.read_csv('./access_info/access_info.txt')

# Client details
client_twitter_handle = access_info.get_values()[0,0]
client_consumer_key = access_info.get_values()[0,1]
client_consumer_secret = access_info.get_values()[0,2]
client_access_token_key = access_info.get_values()[0,3]
client_access_token_secret = access_info.get_values()[0,4]


auth = tweepy.OAuthHandler(client_consumer_key, client_consumer_secret)
auth.set_access_token(client_access_token_key, client_access_token_secret)
api = tweepy.API(auth)

api.followers()



