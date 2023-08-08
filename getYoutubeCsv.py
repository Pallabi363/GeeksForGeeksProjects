import argparse
from googleapiclient.discovery import build as build_analytics
from apiclient.errors import HttpError 
from oauth2client.service_account import ServiceAccountCredentials
import csv
from datetime import datetime, timedelta


# Function to write data to CSV
def csv_writer(data, method, save_as, headers=None):
    with open(save_as, method, encoding='utf8') as csvfile:
        headers = headers or data[0].keys()
        writer = csv.DictWriter(csvfile, lineterminator='\n', fieldnames=headers)
        if method != 'a':
            writer.writeheader()
        writer.writerows(data)


# Function to fetch video IDs
def fetch_video_ids(youtube_api, channelId, after_date):
    video_ids = []
    next_page_token = None
    print("Connecting to Youtube API...")
    while True:
        response = youtube_api.search().list(
            part='id',
            channelId=channelId,
            maxResults=50,
            order='date',
            publishedAfter=after_date,
            type='video',
            pageToken=next_page_token
        ).execute()

        for item in response['items']:
            video_ids.append(item['id']['videoId'])

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break
    print("Youtube API Connected....")
    return video_ids


# Function to fetch video details
def fetch_video_details(youtube_api, video_ids):
    videos_data = []
    print("Fetching Video Details....")
    for video_id in video_ids:
        video_response = youtube_api.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        ).execute()
        videos_data.append(video_response)

    return videos_data


# Function to process video details and prepare rows
def process_video_details(videos_data):
    final_data = []

    keys_mapping = {
        'video_id': ['id'],
        'video_title': ['snippet', 'title'],
        'uploaded_date': ['snippet', 'publishedAt'],
        'no_views': ['statistics', 'viewCount'],
        'no_likes': ['statistics', 'likeCount'],
        'no_comments': ['statistics', 'commentCount'],
        'no_favourites': ['statistics', 'favoriteCount'],
        'duration': ['contentDetails', 'duration'],
        'video_url': lambda item: f"https://www.youtube.com/watch?v={item['id']}",
        'video_category': ['snippet', 'categoryId'],
        'video_description': ['snippet', 'description'],
        'video_tags': ['snippet', 'tags']
    }

    for video in videos_data:
        for item in video['items']:
            row = {}
            for key, path in keys_mapping.items():
                try:
                    if callable(path):
                        row[key] = path(item)
                    else:
                        data = item
                        for p in path:
                            data = data[p]
                        row[key] = data
                except KeyError:
                    row[key] = " "
            final_data.append(row)
    print("Data Exporting Started....")
    return final_data


# Main function to execute the workflow
def main(no_days):
    credentials_json_path = 'pallabi_youtube_sa_key.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json_path, ['https://www.googleapis.com/auth/youtube.readonly'])
    youtube_api = build_analytics('youtube', 'v3', credentials=credentials)
    channelId = 'UC0RhatS1pyxInC00YKjjBqQ'

    after_date = (datetime.now() - timedelta(days=no_days)).isoformat() + 'Z'
    
    video_ids = fetch_video_ids(youtube_api, channelId, after_date)
    videos_data = fetch_video_details(youtube_api, video_ids)
    final_data = process_video_details(videos_data)
    
    csv_writer(final_data, 'w', f'Geeks_For_Geeks_Youtube_Data_{no_days}_Days.csv')
    print("Data Exporting Completed....")

if __name__ == "__main__":
    #main(300)

    parser = argparse.ArgumentParser(description='Fetch YouTube Video Data')
    parser.add_argument('--no_days', type=int, default=200, help='Number of days to go back and fetch videos')
    args = parser.parse_args()
    main(args.no_days)

