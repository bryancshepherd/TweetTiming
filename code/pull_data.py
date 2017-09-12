# Tweepy docs: http://docs.tweepy.org/en/v3.5.0/auth_tutorial.html
import tweepy
import pandas as pd
import datetime
import dateutil
### Better is to add this info
### to a text file and pull it in

access_info = pd.read_csv('./access_info/access_info.txt')

lookback_length = 7
lookback_start = datetime.datetime.today() - \
                 dateutil.relativedelta.relativedelta(days=lookback_length)

# Client details
client_twitter_handle = access_info.get_values()[0,0]
client_consumer_key = access_info.get_values()[0,1]
client_consumer_secret = access_info.get_values()[0,2]
client_access_token_key = access_info.get_values()[0,3]
client_access_token_secret = access_info.get_values()[0,4]


auth = tweepy.OAuthHandler(client_consumer_key, client_consumer_secret)
auth.set_access_token(client_access_token_key, client_access_token_secret)
api = tweepy.API(auth)

me = api.me()
me.followers_count

all_tweets_list = []

followers = api.followers(count=me.followers_count)

for follower in followers[0:10]:

    temp_statuses = api.user_timeline(follower.id, count=200)
    num_of_statuses = len(temp_statuses)
    last_tweet_date = temp_statuses[num_of_statuses-1].created_at
    last_tweet_id = temp_statuses[num_of_statuses-1].id

    print('Processing {0} tweets for {1}'.format(num_of_statuses,
                                                 follower.screen_name))

    for status in temp_statuses:

        # There is no indicator for whether a tweet is
        # a retweet. We just have to check whether
        # 'retweeted_status' is in the object
        try:
            status.retweeted_status
            is_retweet = True
        except:
            is_retweet = False

        all_tweets_list.append([me.screen_name, follower.screen_name,
                                status.text, is_retweet, status.created_at])

    # This is a little confusing, but if the
    # date of the last tweet pulled is more
    # recent than the beginning of the lookback
    # period, we want to keep pulling tweets
    while last_tweet_date > lookback_start:
        temp_statuses = api.user_timeline(follower.id,
                                          max_id=last_tweet_id,
                                          count=200)
        num_of_statuses = len(temp_statuses)
        last_tweet_date = temp_statuses[num_of_statuses - 1].created_at
        last_tweet_id = temp_statuses[num_of_statuses - 1].id

        print('Processing {0} tweets for {1}'.format(num_of_statuses,
                                                     follower.screen_name))

        for status in temp_statuses:

            # There is no indicator for whether a tweet is
            # a retweet. We just have to check whether
            # 'retweeted_status' is in the object
            try:
                status.retweeted_status
                is_retweet = True
            except:
                is_retweet = False

            all_tweets_list.append([me.screen_name, follower.screen_name,
                                    status.text, is_retweet, status.created_at])


# Create a dataframe to hold the data
all_tweets = pd.DataFrame(all_tweets_list, columns=['root_user', 'follower',
                                                    'tweet','is_retweet',
                                                    'tweet_time'])


all_tweets[all_tweets.follower == 'kearneymw']
# The process above results in some duplicate tweets.
# It's easiest just to handle them here:
all_tweets = all_tweets.drop_duplicates

data = api.rate_limit_status()

print (data['resources']['statuses']['/statuses/user_timeline']['remaining'])
print (data['resources']['followers']['/followers/list']['remaining'])
print (data['resources']['application']['/application/rate_limit_status']['remaining'])
print (data['resources']['account']['/account/verify_credentials']['remaining'])

print (data['resources']['statuses']['/statuses/user_timeline']['reset'])
print (data['resources']['followers']['/followers/list']['reset'])
print (data['resources']['application']['/application/rate_limit_status']['reset'])
print (data['resources']['account']['/account/verify_credentials']['reset'])

data['resources']['account']['/account/verify_credentials']['reset']

datetime.datetime.fromtimestamp(data['resources']['account']['/account/verify_credentials']['reset'])

print data['resources']['users']['/users/lookup']