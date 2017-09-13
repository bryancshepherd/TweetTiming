# Tweepy docs: http://docs.tweepy.org/en/v3.5.0/auth_tutorial.html
import tweepy
import pandas as pd
import datetime
import dateutil
import time
### Better is to add this info
### to a text file and pull it in

def calc_wait_time(rl_dict, access_point):
    res_time = datetime.datetime.fromtimestamp(rl_dict[access_point + 'res'])
    current_time = datetime.datetime.now()
    seconds_until_reset = (res_time - current_time).seconds + 10
    print('Pausing {0} seconds due to the '
          '{1} rate limit at {2}'.format(seconds_until_reset,
                                         access_point,
                                         str(current_time)))
    return seconds_until_reset

def rate_limit_check():
    data = api.rate_limit_status()

    user_timeline_remaining = data['resources']['statuses'] \
                                  ['/statuses/user_timeline'] \
                                  ['remaining']

    followers_list_remaining = data['resources']['followers'] \
                                   ['/followers/list']['remaining']

    rate_limit_remaining = data['resources']['application'] \
                               ['/application/rate_limit_status']['remaining']

    verify_credentials_remaining = data['resources']['account'] \
                                       ['/account/verify_credentials'] \
                                       ['remaining']

    user_timeline_reset = data['resources']['statuses'] \
                              ['/statuses/user_timeline'] \
                              ['reset']

    followers_list_reset = data['resources']['followers'] \
                               ['/followers/list']['reset']

    rate_limit_reset = data['resources']['application'] \
                           ['/application/rate_limit_status']['reset']

    verify_credentials_reset = data['resources']['account'] \
                                   ['/account/verify_credentials'] \
                                   ['reset']

    return {'utrem': user_timeline_remaining,
            'ftrem': followers_list_remaining,
            'rlrem': rate_limit_remaining,
            'vcrem': verify_credentials_remaining,
            'utres': user_timeline_reset,
            'ftres': followers_list_reset,
            'rlres': rate_limit_reset,
            'vcres': verify_credentials_reset}

def process_statuses(statuses):
    '''
    Get information about each status into
    an easier to work with format

    :param statuses: A list of status objects from the
    Twitter API
    :return: A list of data elements
    '''
    status_list = []
    for status in statuses:

        # There is no indicator for whether a tweet is
        # a retweet. We just have to check whether
        # 'retweeted_status' is in the object
        try:
            status.retweeted_status
            is_retweet = True
        except:
            is_retweet = False

        status_list.append([me.screen_name, follower.screen_name,
                            status.text, is_retweet, status.created_at])

    return status_list

def get_users_tweets(user_obj, lookback_length):
    '''
    Get a list of the relevant user's Twitter statues

    :param user_obj: a user object returned from the Twitter API
    :param lookback_period: how far to lookback in days
    :return: a list of the users Twitter statuses for the duration of the
    lookback period
    '''

    lookback_start = datetime.datetime.today() - \
                     dateutil.relativedelta.relativedelta(days=lookback_length)

    single_user_tweets_list = []
    last_tweet_date = datetime.datetime.now()
    last_tweet_id = None
    # This is a little confusing, but if the
    # date of the last tweet pulled is more
    # recent than the beginning of the lookback
    # period, we want to keep pulling tweets
    while last_tweet_date > lookback_start:

        if rlc['utrem']<5:
            time.sleep(calc_wait_time(rlc, 'ut'))
            rlc = rate_limit_check()

        temp_statuses = api.user_timeline(user_obj.id,
                                          max_id=last_tweet_id,
                                          count=200)

        rlc['utrem'] -= 1

        num_of_statuses = len(temp_statuses)
        last_tweet_date = temp_statuses[num_of_statuses - 1].created_at
        last_tweet_id = temp_statuses[num_of_statuses - 1].id

        print('Processing {0} tweets for {1}'.format(num_of_statuses,
                                                     user_obj.screen_name))

    single_user_tweets_list.append(process_statuses(temp_statuses))

    return single_user_tweets_list


# def get_followers(user_obj):
#     '''
#     Get a list of the relevant user's Twitter statues
#
#     :param user_obj: a user object returned from the Twitter API
#     :param lookback_period: how far to lookback in days
#     :return: a list of the users Twitter followers
#     '''
#
#     single_user_tweets_list = []
#     last_tweet_date = datetime.datetime.now()
#     last_tweet_id = None
#     # This is a little confusing, but if the
#     # date of the last tweet pulled is more
#     # recent than the beginning of the lookback
#     # period, we want to keep pulling tweets
#     while last_tweet_date > lookback_start:
#
#         if rlc['utrem'] < 5:
#             time.sleep(calc_wait_time(rlc, 'ut'))
#             rlc = rate_limit_check()
#
#         temp_statuses = api.user_timeline(user_obj.id,
#                                           max_id=last_tweet_id,
#                                           count=200)
#
#         rlc['utrem'] -= 1
#
#         num_of_statuses = len(temp_statuses)
#         last_tweet_date = temp_statuses[num_of_statuses - 1].created_at
#         last_tweet_id = temp_statuses[num_of_statuses - 1].id
#
#         print('Processing {0} tweets for {1}'.format(num_of_statuses,
#                                                      user_obj.screen_name))
#
#     single_user_tweets_list.append(process_statuses(temp_statuses))
#
#     return single_user_tweets_list

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

me = api.me()
me.followers_count

all_tweets_list = []
rlc = rate_limit_check()

followers = api.followers(count=me.followers_count)

for follower in followers[0:10]:

    all_tweets_list.append(get_users_tweets(follower))


# Create a dataframe to hold the data
all_tweets = pd.DataFrame(all_tweets_list, columns=['root_user', 'follower',
                                                    'tweet','is_retweet',
                                                    'tweet_time'])

# It's easiest just to handle them here:
all_tweets = all_tweets.drop_duplicates