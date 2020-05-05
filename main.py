import os
import re
from tweepy import Cursor
from tweepy import API
from tweepy import OAuthHandler
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# function to get the authentication with the given credentials
def get_twitter_authentication():
    try:
        # getting values(credentials) from environment variables
        # here I have used environment variables to store my credentials
        consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
        consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]
    except KeyError:
        print("Something went wrong while authenticating...")
    # authenticating for API request
    # I have used OAuth 2 authentications since I only need read-only access to public information
    auth = OAuthHandler(consumer_key, consumer_secret)
    return auth

# function to get the Twitter API client
def get_twitter_client():
    # get authentication
    auth = get_twitter_authentication()
    # create Twitter API
    client = API(auth)
    return client

# function to get the twitter data 
def get_twitter_data(search_query, number_of_tweets, geocode, date_before):
    # get Twitter API
    api = get_twitter_client()
    # object to hold all the tweets
    tweet_objects = []
    # Search for a specific keyword and iterate through the results
    for tweet in Cursor(
        api.search,
        q=search_query,
        count=number_of_tweets,
        geocode=geocode,
        result_type="recent",
        until=date_before,
    ).items():
        # csvWriter.writerow([tweet.id, tweet.created_at, tweet.text, tweet.truncated, tweet.user.id, tweet.user.location, tweet.user.verified, tweet.user.follors_count, ])
        tweet_objects.append(tweet)
    return tweet_objects

# function to convert the list of objects to a pandas dataframe
def get_converted_dataframe(tweet_objects):
    df = pd.DataFrame()
    prev_attr = "tweet"
    for tweet in tweet_objects:
        df_row = pd.DataFrame()
        df_row = add_to_df(tweet, prev_attr + "_", df_row)
        df = pd.concat([df, df_row], ignore_index=True, sort=False)
    return df

# function that append value into the dataframe recursively
def add_to_df(obj, pre_attr, df_row):
    for attr, value in obj.items():
        if type(value) is object:
            df_row = add_to_df(value, attr + "_", df_row)
        elif type(value) is str:
            print(value)
        else:
            df_row[pre_attr + attr] = value
    return df_row

# function to preprocess the given tweet data
def clean_tweets(tweet_text):
    tweet_text = tweet_text.lower() # normalizing
    tweet_text = remove_noise(tweet_text) # removing noise
    tweet_text = word_tokenize(tweet_text) # tokening the text
    return tweet_text

def remove_noise(tweet_text):
    tweet_text = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', tweet_text)
    tweet_text = re.sub('@[^\s]+', 'AT_USER', tweet_text)
    tweet_text = re.sub(r'#([^\s]+)', r'\1', tweet_text)
    return tweet_text

if __name__ == "__main__":
    # define arguments to pass
    search_query = "curfew"
    number_of_tweets = 100
    geocode = "7.8731,80.7718,224km"  # latitude:7.8731, longitude:80.7718, radius:224km
    date_before = "2020-05-01"
    # get twitter data
    tweet_objects = get_twitter_data(
        search_query, number_of_tweets, geocode, date_before
    )

    # get a pandas dataframe from the Twitter data
    df = get_converted_dataframe(tweet_objects)

    # save the dataframe in an excel sheet
    writer = pd.ExcelWriter('tweets.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Twitter data')
    writer.save

    # handle missing values
    df = df.fillna("undefined") # fill missing values

    # extracting id and the text field from the data frame
    df_text = df[['tweet_id', 'tweet_text']]

    # Clean textual data
    df_text['tweet_text'] = df_text['tweet_text'].applymap(lambda x: clean_tweets(x))

    
    