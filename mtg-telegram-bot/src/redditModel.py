﻿import config
import praw

def log_to_reddit():
    """Log to reddit API and return a subreddit object"""
    
    reddit = praw.Reddit(client_id=config.reddit_client_id,
                         client_secret=config.reddit_client_secret,
                         password=config.reddit_password,
                         user_agent=config.reddit_user_agent,
                         username=config.reddit_username)
    
    return reddit