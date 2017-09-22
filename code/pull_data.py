# Tweepy docs: http://docs.tweepy.org/en/v3.5.0/auth_tutorial.html
import tweepy
import pandas as pd
import datetime
import dateutil
import time
import matplotlib.pyplot as plt
import seaborn as sns


def calc_wait_time(rl_dict, access_point):
    """
    Calculate the amount of time to wait when we hit a rate limit
    :param rl_dict: a dictionary of the current rate limit statuses
    :param access_point: the API endpoint we're waiting on
    :return: the seconds until the relevant wait limit will reset
    """

    res_time = datetime.datetime.fromtimestamp(rl_dict[access_point + 'res'])
    current_time = datetime.datetime.now()
    seconds_until_reset = (res_time - current_time).seconds + 10
    print('Pausing {0} seconds due to the '
          '{1} rate limit at {2}'.format(seconds_until_reset,
                                         access_point,
                                         str(current_time)))
    return seconds_until_reset

def rate_limit_check():
    """
    Check and store rate limit statuses
    :return: a dictionary of the current rate limit statuses
    """

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
    """
    Get information about each status into
    an easier to work with format

    :param statuses: A list of status objects from the
    Twitter API
    :return: A list of data elements
    """

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

    return pd.DataFrame(status_list)

def get_users_tweets(user_obj,
                     lookback_length,
                     max_tweets_per_day,
                     rlc):
    """
    Get a list of the relevant user's Twitter statues

    :param user_obj: a user object returned from the Twitter API
    :param lookback_period: how far to lookback in days
    :param max_tweets_per_day: the maximum number of tweets to allow,
    on average, per day. After a user passes this amount no more
    statuses are pulled and their data is removed.
    from the data.
    :return: a list of the users Twitter statuses for the duration of the
    lookback period
    """

    lookback_start = datetime.datetime.today() - \
                     dateutil.relativedelta.relativedelta(days=lookback_length)

    single_user_tweets_df = pd.DataFrame()
    last_tweet_date = datetime.datetime.now()
    last_tweet_id = None
    max_number_of_statuses = lookback_length * max_tweets_per_day
    total_statused_pulled = 0
    # This is a little confusing, but if the
    # date of the last tweet pulled is more
    # recent than the beginning of the lookback
    # period, we want to keep pulling tweets
    while ((last_tweet_date > lookback_start) &
           (total_statused_pulled < max_number_of_statuses)):

        print('Pulling tweets for {0}'.format(user_obj.screen_name))

        if rlc['utrem']<5:
            rlc = rate_limit_check()
            time.sleep(calc_wait_time(rlc, 'ut'))

        temp_statuses = api.user_timeline(user_obj.id,
                                          max_id=last_tweet_id,
                                          count=200)

        rlc['utrem'] -= 1

        num_of_statuses = len(temp_statuses)

        total_statused_pulled += num_of_statuses

        # Get rid of data for users who tweet too much,
        # they are probably bots.
        if total_statused_pulled > max_number_of_statuses:
            single_user_tweets_df = pd.DataFrame()
            print('{0} exceeded the maximum number of '
                  'tweets. Deleting.'.format(user_obj.screen_name))
            break

        # There is an issue where some followers
        # end up with only one status that keeps repeating.
        # This is a stopgap.
        # To see it break (and maybe even fix it) get rid of this.
        if num_of_statuses<=2:
            print('Funky happened for {0}. '
                  'Deleting.'.format(user_obj.screen_name))
            single_user_tweets_df = pd.DataFrame()
            break

        last_tweet_date = temp_statuses[num_of_statuses - 1].created_at
        last_tweet_id = temp_statuses[num_of_statuses - 1].id

        print('Processing {0} tweets for {1}'.format(num_of_statuses,
                                                     user_obj.screen_name))

        single_user_tweets_df = pd.concat([single_user_tweets_df,
                                           process_statuses(temp_statuses)])

    # The process gets tweets that are older
    # than the target date for some followers.
    # Drop those here.
    single_user_tweets_df.iloc[:, 4] > lookback_start

    return single_user_tweets_df, rlc

def assign_numeric_day(x):
    """
    Assign a numeric value based on the day of the week. Useful for
    creating series to sort by.
    :param x:
    :return: numeric value based on the date
    """

    if x == 'Sunday':
        return 0
    elif x == 'Monday':
        return 1
    elif x == 'Tuesday':
        return 2
    elif x == 'Wednesday':
        return 3
    elif x == 'Thursday':
        return 4
    elif x == 'Friday':
        return 5
    elif x == 'Saturday':
        return 6

def prep_for_plotting(dataframe, value_var):
    """
    Reshape the data for heatmap plotting
    :param dataframe: the dataframe to be reshaped
    :param value_var: the column that contains cell values
    :return: reshaped data with weekdays as rows and hours as columns
    """
    reshaped_df = dataframe.pivot(index='weekday',
                                  columns='hour',
                                  values=value_var)
    reshaped_df['day_name'] = reshaped_df.index.values
    reshaped_df['numeric_day'] = reshaped_df.day_name.apply(
        assign_numeric_day)
    reshaped_df = reshaped_df.sort_values('numeric_day')
    del reshaped_df['numeric_day']
    del reshaped_df['day_name']

    return reshaped_df

# def get_followers(user_obj):
#     """
#     Get a list of the relevant user's Twitter statues
#
#     :param user_obj: a user object returned from the Twitter API
#     :param lookback_period: how far to lookback in days
#     :return: a list of the users Twitter followers
#     """
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

# Authentication details
# There are a number of ways to do this.
access_info = pd.read_csv('./access_info/access_info.txt')
twitter_handle = access_info.get_values()[0,0]
consumer_key = access_info.get_values()[0,1]
consumer_secret = access_info.get_values()[0,2]
access_token_key = access_info.get_values()[0,3]
access_token_secret = access_info.get_values()[0,4]

# Make connection
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)
api = tweepy.API(auth)

# Get the authenticated user's information
me = api.me()

# Let's just put everything in a dataframe, so create an
# empty dataframe to hold stuff.
all_tweets_df = pd.DataFrame()
rlc = rate_limit_check()

# Get the list of the authenticated users followers
# Right now max is 200, this will need to be
# updated to handle more followers.
followers = api.followers(count=me.followers_count)

# Loop through the followers list to get individual
# follower's timelines.
for follower in followers:

    try:
        data, rlc = get_users_tweets(follower, 28, 50, rlc)
    except:
        print('Fetching tweets for {0} '
              'didn\'t work, skipping'.format(follower.screen_name))
        continue

    all_tweets_df = pd.concat([all_tweets_df, data])


# Create a dataframe to hold the data
all_tweets_df.columns=['root_user', 'follower',
                       'tweet','is_retweet',
                       'tweet_time']

# This is temporary, can be deleted later
all_tweets_df_org = all_tweets_df
# all_tweets_df = all_tweets_df_org
all_tweets_df_org.to_pickle('./data/all_tweets_archive.pkl')
all_tweets_df = pd.read_pickle('./data/all_tweets_archive.pkl')

# It's easiest just to handle them here:
all_tweets_df.drop_duplicates(inplace=True)

all_tweets_df['weekday'] = all_tweets_df.tweet_time.dt.weekday_name
all_tweets_df['hour'] = all_tweets_df.tweet_time.dt.hour

all_tweets_df_by_hour = all_tweets_df\
                            .groupby(['weekday', 'hour'])\
                            .follower\
                            .count().reset_index()

# Two grouping/counting steps to
# get to the number of users per hour
users_by_hour = all_tweets_df\
                 .groupby(['weekday', 'hour', 'follower'])\
                 .tweet\
                 .count().reset_index()

users_by_hour = users_by_hour\
                 .groupby(['weekday', 'hour'])\
                 .follower.count()\
                 .reset_index()

# Two grouping/counting steps to
# get to the number of retweets per hour
retweets_by_hour = all_tweets_df\
                     .groupby(['weekday', 'hour', 'follower'])\
                     .is_retweet\
                     .sum().reset_index()

retweets_by_hour = retweets_by_hour\
                     .groupby(['weekday', 'hour'])\
                     .is_retweet\
                     .sum().reset_index()

sns.set()

# Draw a heatmap with the numeric values in each cell
df_to_plot = prep_for_plotting(all_tweets_df_by_hour, 'follower')
f, ax = plt.subplots(figsize=(9, 6))
sns.heatmap(df_to_plot, linewidths=.5, ax=ax)

df_to_plot = prep_for_plotting(all_tweets_df_by_hour, 'follower')
ax = sns.heatmap(df_to_plot, linewidths=.5)

df_to_plot = prep_for_plotting(users_by_hour, 'follower')
ax = sns.heatmap(df_to_plot, linewidths=.5, square=False)

df_to_plot = prep_for_plotting(retweets_by_hour, 'is_retweet')
ax = sns.heatmap(df_to_plot, linewidths=.5, square=False)

