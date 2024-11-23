# Funcion para obtener video IDs para una playlist.

def get_all_video_ids_from_playlists(youtube, playlist_ids):
    all_videos = []  # Initialize a single list to hold all video IDs

    for playlist_id in playlist_ids:
        next_page_token = None

        # Fetch videos from the current playlist
        while True:
            playlist_request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token)
            playlist_response = playlist_request.execute()

            for item in playlist_response['items']:
                video_id = item['contentDetails']['videoId']
                published_at = item['contentDetails']['videoPublishedAt']

                all_videos.append({
                    'VideoID': video_id,
                    'VideopublishedAt': published_at
                })


            next_page_token = playlist_response.get('nextPageToken')

            if next_page_token is None:
                break

    return all_videos

# funcion para obtener titulo del video para un Video ID.

def get_video_title_from_id(youtube ,video_id):
  request = youtube.videos().list(
        part="snippet",
        id= video_id
    )
  response = request.execute()
  # Extract and return the video title
  return response['items'][0]['snippet']['title']


  # Function to get replies for a specific comment
def get_replies(youtube, parent_id, video_id):  # Added video_id as an argument
    replies = []
    next_page_token = None

    while True:
        reply_request = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            textFormat="plainText",
            maxResults=100,
            pageToken=next_page_token
        )
        reply_response = reply_request.execute()

        for item in reply_response['items']:
            comment = item['snippet']
            replies.append({
                'TopCommentID': parent_id,
                'Timestamp': comment['publishedAt'],
                'Username': comment['authorDisplayName'],
                'VideoID': video_id,
                'Comment': comment['textDisplay'],
                'CommentDate': comment['updatedAt'] if 'updatedAt' in comment else comment['publishedAt'],
                'LikeCount': comment['likeCount'],
                'IsReply': 'True' # Diferenciar replies de comentarios

            })

        next_page_token = reply_response.get('nextPageToken')
        if not next_page_token:
            break

    return replies

# Function to get all comments (including replies) for a single video
def get_comments_for_video(youtube, video_id):
    all_comments = []
    next_page_token = None

    while True:
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            pageToken=next_page_token,
            textFormat="plainText",
            maxResults=100
        )
        comment_response = comment_request.execute()

        for item in comment_response['items']:
            top_comment_id = item['snippet']['topLevelComment']['id']
            top_comment = item['snippet']['topLevelComment']['snippet']

            all_comments.append({
                'TopCommentID': top_comment_id,
                'Timestamp': top_comment['publishedAt'],
                'Username': top_comment['authorDisplayName'],
                'VideoID': video_id,  # Directly using video_id from function parameter
                'Comment': top_comment['textDisplay'],
                'CommentDate': top_comment['updatedAt'] if 'updatedAt' in top_comment else top_comment['publishedAt'],
                'LikeCount': top_comment['likeCount'],
                'IsReply': 'False'
            })

            # Fetch replies if there are any
            if item['snippet']['totalReplyCount'] > 0:
                all_comments.extend(get_replies(youtube, item['snippet']['topLevelComment']['id'], video_id))

        next_page_token = comment_response.get('nextPageToken')
        if not next_page_token:
            break

    return all_comments


def get_video_ids_and_titles_from_channel(channel_name, api_key):

    import requests
    # URL para buscar el canal por nombre
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&q={channel_name}&type=channel&part=id"

    response = requests.get(url)
    data = response.json()

    # Verificar si se obtuvo un canal
    if data['items']:
        channel_id = data['items'][0]['id']['channelId']
    else:
        return None

    # URL para obtener la lista de videos del canal (incluyendo el snippet para obtener el título)
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=id,snippet&order=date&maxResults=50"
    videos = []

    while url:
        response = requests.get(url)
        data = response.json()

        # Extraer los IDs y títulos de los videos
        for item in data.get('items', []):
            if item['id']['kind'] == 'youtube#video':
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                videos.append({'VideoID': video_id, 'title': video_title})

        # Verificar si hay más resultados
        next_page_token = data.get('nextPageToken')
        if next_page_token:
            url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=id,snippet&order=date&maxResults=50&pageToken={next_page_token}"
        else:
            url = None

    return videos


def busqueda_youtube(max_results, busqueda, api_key):
  
  import requests

  url = "https://www.googleapis.com/youtube/v3/search"

  params = {'part': 'snippet',
                    'maxResults': int(max_results),
                    'q': str(busqueda),
                    'type': 'video',
                    'key': str(api_key), # Asegúrate de usar tu propia API key
                    'relevanceLanguage': 'es'}
  # Realizar la solicitud GET
  response = requests.get(url, params=params)
                
  # Verificar si la solicitud fue exitosa
  if response.status_code == 200:
    # Parsear la respuesta JSON
    results = response.json()
    video_titles_list = []
    video_ids_list = []
                    
    # Iterar sobre los títulos de los videos encontrados
    for item in results['items']:
      video_titles_list.append(item['snippet']['title'])
      video_ids_list.append(item['id']['videoId'])
    return video_titles_list, video_ids_list
  
  else:
    None, None



def extract_comments_from_reddit_post(reddit_instance, post_url):
    # Get the submission object
    submission = reddit_instance.submission(url=post_url)

    # Replace more comments
    submission.comments.replace_more(limit=0)  # Load all comments

    title =  submission.title
    content = submission.selftext

    # Prepare lists for comment information
    comment_ids = []
    parent_ids = []
    authors = []
    bodies = []
    is_reply = []
    scores = []

    # Define a function to extract comments recursively
    def extract_comments(comment_list, parent_id=None):
        for comment in comment_list:
            comment_ids.append(comment.id)  # Get comment ID
            parent_ids.append(parent_id if parent_id else "Submission")  # Get parent ID
            authors.append(comment.author.name if comment.author else "Unknown")
            bodies.append(comment.body)
            is_reply.append(True if parent_id else False)  # Mark as reply if it has a parent
            scores.append(comment.score)  # Get the score of the comment

            # Recursively process replies
            if comment.replies:
                extract_comments(comment.replies, comment.id)

    # Collect all comments and their replies
    extract_comments(submission.comments)

    # Return the lists
    return title , content ,comment_ids, parent_ids, authors, bodies, is_reply, scores



# Function to search posts using a keyword, filtering out external links
def get_last_reddit_posts(reddit, keyword, limit=100):
    posts = []
    
    # Use Reddit's search functionality
    for submission in reddit.subreddit('all').search(keyword, sort='new', limit=limit):
        # Filter out external links by checking if it's a self-post or a reddit link
        if submission.is_self or 'reddit.com' in submission.url:
            posts.append({
                'title': submission.title,
                'subreddit': submission.subreddit.display_name,
                'score': submission.score,
                'url': submission.url,
                'created_date': submission.created_utc  # Convert timestamp to date
            })
    
    return posts