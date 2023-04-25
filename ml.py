import time
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.metrics.pairwise import cosine_similarity

from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings('ignore')

def get_audio_features_artist_top_tracks(artist_list):
    artist_audio_features = {}
    for artist_name in artist_list:
        #print(artist_name)
        time.sleep(1)
        results = sp.search(q=artist_name, type='artist')
        artist_uri = results['artists']['items'][0]['uri']
        top_tracks = sp.artist_top_tracks(artist_uri)['tracks']
        track_uris = [track['uri'] for track in top_tracks]
        for i in range(0, len(track_uris), 50):
            batch = track_uris[i:i+50]
            artist_audio_features[artist_name] = sp.audio_features(batch)
        
    artist_audio_feats = {}
    keys = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence','time_signature','duration_ms','tempo']
    for artist_name, track_features in artist_audio_features.items():
        artist_track_feats = [] 
        for track_feat in track_features:
            artist_track_feats.append([track_feat.get(key) for key in keys])
            artist_audio_feats[artist_name] = np.mean(np.array(artist_track_feats),axis=0)
    return artist_audio_feats

# get audio features for recommended artists using every track 
def get_audio_features_artist_all_tracks(artist_list):    
    artist_audio_features = {}
    for artist_name in artist_list:
        time.sleep(1)
        results = sp.search(q=artist_name, type='artist')
        artist_uri = results['artists']['items'][0]['uri']
        albums = sp.artist_albums(artist_uri, album_type='album')
        album_uris = [album['uri'] for album in albums['items']]
        tracks = []
        for album_uri in album_uris:
            album_tracks = sp.album_tracks(album_uri)['items']
            tracks += album_tracks
        track_uris = [track['uri'] for track in tracks]
        for i in range(0, len(track_uris), 50):
            batch = track_uris[i:i+50]
            artist_audio_features[artist_name] = sp.audio_features(batch)
    
    artist_audio_feats = {}
    keys = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence','time_signature','duration_ms','tempo']
    for artist_name, track_features in artist_audio_features.items():
        artist_track_feats = [] 
        for track_feat in track_features:
            artist_track_feats.append([track_feat.get(key) for key in keys])
            artist_audio_feats[artist_name] = np.mean(np.array(artist_track_feats),axis=0)
    return artist_audio_feats

def get_cosim_artist_df(artist_name, df, n):
    ss = StandardScaler()
    df_scaled = ss.fit_transform(df)
    df = pd.DataFrame(data=df_scaled, index=df.index)
    
    artist_array = np.array(df.T[artist_name]).reshape(1,-1)
    dataset_array = df.drop(index=artist_name).values
    
    cosim_scores = cosine_similarity(artist_array, dataset_array).flatten()
    artist_names_array = df.drop(index=artist_name).index.values
    
    df_result = pd.DataFrame(
        data = {
            'artist'               : artist_names_array,
            'cosim_' + artist_name : cosim_scores,
                }
                            )
    
    df_result = df_result.sort_values(by='cosim_' + artist_name, ascending=False).head(n)    
    return df_result.reset_index(drop=True)

def get_artist_images(artist_list):
    """
    Given a list of artist names, retrieves their images from Spotify API and returns a list of image URLs.
    """
    image_list = []
    for artist_name in artist_list:
        time.sleep(1)
        results = sp.search(q=artist_name, type='artist')
        image_list.append(results['artists']['items'][0]['images'][0]['url']) 
        
    return image_list

def plot_artist_ranking(duh, image_list):
    import warnings
    warnings.filterwarnings('ignore')

    # Create a figure with subplots for each artist
    fig, axs = plt.subplots(len(duh)+1, 1, figsize=(50,50))
    
        # Load the image from the URL
    response = requests.get(image_list[-1])
    img = Image.open(BytesIO(response.content))

    # Plot the image
    axs[0].imshow(img)
    axs[0].axis('off')
    # Add the artist name and ranking as a title
    axs[0].set_title("COACHELLA\nHere are the artist\nmost similar to\n{}".format(duh.columns.values[1].split('_')[1]),
                     fontname='Luminari',
                     fontsize=50,
                     fontstyle='italic')
    #add background color
    # Beau blue: #bcd4e6
    # Cool purple: #c9a0dc
    # Cool White: #f5f5f5
    
    color ='#e3dac9'#'#fff5ee'
    axs[0].set_facecolor(color=color)
    fig.patch.set_facecolor(color)
    # Loop through each artist and plot their image and ranking
    for i, row in duh.iterrows():
        # Load the image from the URL
        response = requests.get(image_list[i])
        img = Image.open(BytesIO(response.content))

        # Plot the image
        axs[i+1].imshow(img)
        axs[i+1].axis('off')

        # Add the artist name and ranking as a title
        # 'Luminari'
        axs[i+1].set_title(f"{i+1}. {row['artist']}\nSimilarity: {row[duh.columns.values[1]]*100:.2f} %",
                         fontname='Luminari',
                         fontsize=30,
                         fontstyle='italic')
        
        # #add background color
        # color = '#cd5c95'#'#cd5c5c'
        # axs[i+1].set_facecolor(color=color)
        # fig.patch.set_facecolor(color)
    
    # Show the plot
    # plt.show()
    plt.savefig('duh.jpg')
    plt.savefig('static/images/duh.jpg')


coachella_lineup= [
    '$uicideboy$', 
    '¿Téo?',
    'Adam Beyer', 
    'AG Club',
    'ROSALÍA', 
    'Saba',
    'Yung Lean', 
    'YUNGBLUD', 
    'Yves Tumor'
]

# 'Dinner Party ft. Terrace Martin, Robert Glasper, Kamasi Washington'

client_id = '4b2e3e7dd1484e449ff07d844653058b'
client_secret = '806c8159857a4e6d86c79331b5d71672'

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

# test authentication by retrieving the name of the first featured playlist
playlists = sp.featured_playlists()
# print(playlists['playlists']['items'][0]['name'])

# retrieve audio features for user's music preferences



import os

def ml(meh, meeh):

    # playlist_uri = 'spotify:playlist:37i9dQZF1E378qNqzfcIE3' # replace with user's playlist URI
    playlist_uri = meeh
    playlist_tracks = sp.playlist_tracks(playlist_uri)['items']
    playlist_artist = [track['track']['artists'][0]['name'] for track in playlist_tracks]
    #user_audio_features = sp.audio_features(playlist_track_uris)
    favorite_artists  = list(set(playlist_artist))

    fest_artist_audio_feats = get_audio_features_artist_top_tracks(coachella_lineup)
    user_artist_audio_feats = get_audio_features_artist_top_tracks(favorite_artists)

    artists = [] 
    audio_vec = [] 
    for key, val in fest_artist_audio_feats.items():
            artists.append(key)
            audio_vec.append(val)
    for key, val in user_artist_audio_feats.items():
            artists.append(key)
            audio_vec.append(val)
    audio_vec = np.array(audio_vec)

    keys = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence','time_signature','duration_ms','tempo']
    df_artist = pd.DataFrame(audio_vec,index=artists,columns = keys)

    duh = get_cosim_artist_df(meh, df_artist, 5)
    artist_list = duh['artist']
    artist_list = artist_list.append(pd.Series(duh.columns.values[1].split('_')[1]))
    image_list =  get_artist_images(artist_list)

    plot_artist_ranking(duh, image_list)
    print("doneee")
    # os.system('mkdir {}'.format(meh))
    return 'fuck u'


if __name__ == '__main__':
    import sys
    ml(sys.argv[1], sys.argv[2])
