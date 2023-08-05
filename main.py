import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cred
import json
from lyricsgenius import Genius
from difflib import SequenceMatcher

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cred.client_ID, client_secret= cred.client_SECRET, redirect_uri=cred.redirect_url))
genius = Genius(cred.genius_token)
genius.verbose = False
genius.remove_section_headers = True
def similar(a,b):
    return SequenceMatcher(None, a, b).ratio()
# Functions
def song_combs(playlist_id):
    """
    returns [combs...], [ids(all info)...], [(song, artist)...]
    """
    playlist = sp.playlist_items(playlist_id, None, 100, 0, None)
    id_list = [song['track']['id'] for song in playlist['items']]
    song_names = [(song['track']['name'], song['track']['artists'][0]['name']) for song in playlist['items']]
    combs = []
    for i in range(len(id_list)-1):
        for k in range(i+1,len(id_list)):
            combs.append((i, k))
    return combs, id_list, song_names
def song_combs_playlist(id1, id2):
    """
    returns [combs], ([id1list(all info)...], [id2list(all info)...]), ([(song1, artist1)...], [(song2, artist2)...])
    """
    playlist1 = sp.playlist_items(id1, None, 50, 0, None)
    playlist2 = sp.playlist_items(id2, None, 50, 0, None)
    id_list1 = [song['track']['id'] for song in playlist1['items']]
    id_list2 = [song['track']['id'] for song in playlist2['items']]
    id_list = (id_list1, id_list2)
    song_names1 = [(song['track']['name'], song['track']['artists'][0]['name']) for song in playlist1['items']]
    song_names2 = [(song['track']['name'], song['track']['artists'][0]['name']) for song in playlist2['items']]
    song_names = (song_names1, song_names2)
    combs = []
    if len(id_list1) >= len(id_list2):
        for i in range(len(id_list1)):
            for k in range(len(id_list2)):
                combs.append((i, k))
    else:
        for i in range(len(id_list2)):
            for k in range(len(id_list1)):
                combs.append((k, i))
    return combs, id_list, song_names
def wordplay_score(song1, song2, bank):
    """
    input ((name1, artist1), (name2, artist2))
    """
    # print(song1[0] + song1[1] + '|' + song2[0] + song2[1])
    if song1[0] not in bank:
        try:
            lyrics1 = (genius.search_song(song1[0], song1[1]).lyrics).lower()
        except:
            return 0, '', bank
        lyrics1 = lyrics1.replace(',', '')
        lyrics1 = lyrics1.split('\n')
        del lyrics1[0]
        del lyrics1[-1]
        bank[song1[0]] = lyrics1
    else:
        lyrics1 = bank[song1[0]]
    if song2[0] not in bank:
        try:
            lyrics2 = (genius.search_song(song2[0], song2[1]).lyrics).lower()
        except:
            return 0, '', bank
        lyrics2 = lyrics2.replace(',', '')
        lyrics2 = lyrics2.split('\n')
        del lyrics2[0]
        del lyrics2[-1]
        bank[song2[0]] = lyrics2
    else:
        lyrics2 = bank[song2[0]]

    for line in lyrics1:
        if similar(song2[0].lower(), line)>0.6:
            return 10*similar(song2[0].lower(), line), (song2[0], line), bank
    for line in lyrics2:
        if similar(song1[0].lower(), line)>0.6:
            return 10*similar(song1[0].lower(), line), (song1[0], line),bank
    return 0, '', bank
# print(similar('all i do is win', 'you used to call me on my'))

# print(wordplay_score(('Hotline Bling', 'Drake'), ('All I do is Win', 'DJ Khaled')))
def mix_score(song_1, song_2, bank, names, lyric_bank, wordplay=False):
    score = 0
    key1, mode1 = bank[song_1]['key'], bank[song_1]['mode']
    key2, mode2 = bank[song_2]['key'], bank[song_2]['mode']
    score += key_score(key1, key2, mode1, mode2)
    tempo1, tempo2 = bank[song_1]['tempo'], bank[song_2]['tempo']
    score += tempo_score(tempo1, tempo2)
    line = ''
    if wordplay:
        wp_score, line, lyric_bank = wordplay_score((names[song_1][0], names[song_1][1]), (names[song_2][0], names[song_2][1]), lyric_bank)
        score+= wp_score
    return score, line, lyric_bank
def mix_score_playlist(song_1, song_2, bank, names, wordplay=False):
    score = 0
    key1, mode1 = bank[0][song_1]['key'], bank[0][song_1]['mode']
    key2, mode2 = bank[1][song_2]['key'], bank[1][song_2]['mode']
    score += key_score(key1, key2, mode1, mode2)
    tempo1, tempo2 = bank[0][song_1]['tempo'], bank[1][song_2]['tempo']
    score += tempo_score(tempo1, tempo2)
    line = ''
    if wordplay:
        wp_score, line = wordplay_score((names[song_1][0], names[song_1][1]), (names[song_2][0], names[song_2][1]))
        score+= wp_score
    return score, line
key_map = {0:'C', 1:'Db', 2:'D', 3:'Eb', 4:'E', 5:'F', 6:'Gb', 7:'G', 8:'Ab', 9:'A', 10:'Bb', 11:'B'}
mode_map = {0: 'minor', 1: 'Major'}
def key_score(key1, key2, mode1, mode2):
    if mode1 == 0:
        key1+=9
    if mode2 == 0:
        key2+=9
    if key1 == key2 and mode1 == mode2:
        return 1
    elif key1 == key2:
        return 0.9
    elif (key1+7)%12 == key2:
        return 0.8
    elif (key2+7)%12 == key1:
        return 0.6
    else:
        return 0
def tempo_score(tempo1, tempo2):
    if abs(tempo1-tempo2) < 50:
        return (tempo1 - abs(tempo1-tempo2))/tempo1
    else:
        if tempo1<tempo2:
            return (tempo2-abs(2*tempo1-tempo2))/tempo2
        else:
            return (tempo1-abs(tempo1-2*tempo2))/tempo1   
def playlist_query(query):
    search_results = sp.search(query, 3, 0, 'playlist')
    # print(json.dumps(search_results, sort_keys=True, indent=4))
    for ind, result in enumerate(search_results['playlists']['items']):
        print(str(ind+1) + '. '+ result['name'] + ' --- ' + result['owner']['display_name'])
    print()
    while True:
        selected_playlist = input("Which playlist would you like to select: 1, 2, or 3? ")
        if selected_playlist in ('1', '2', '3'):
            result_id = search_results['playlists']['items'][int(selected_playlist)-1]['id']
            break
        else:
            print('Please enter a valid selection')
    return result_id
def track_query(query):
    search_results = sp.search(query, 3, 0, 'track')
    for ind, result in enumerate(search_results['tracks']['items']):
        print(str(ind+1) + '. ' + result['name'] + ' --- ' + result['artists'][0]['name'])
    print()
    while True:
        selected_track = input('Which song would you like to select: 1, 2, or 3? ')
        if selected_track in ('1', '2', '3'):
            result_id = search_results['tracks']['items'][int(selected_track)-1]['id']
            break
        else:
            print('Please enter a valid selection')
    return result_id
def mixes_in_playlist(wordplay = False):
    while True:
        query = input("Please enter the name of the playlist you want to mix: ")
        print()
        result = playlist_query(query)
        combs, song_bank, names = song_combs(result)
        song_bank = sp.audio_features(song_bank)
        lb = {}
        if wordplay:
           mix_scores = []
           for song1, song2 in combs:
                ms, l, lb = mix_score(song1, song2, song_bank, names, lb, True)
                mix_scores.append((ms, song1, song2, l))
        else:
            mix_scores = [(mix_score(song1, song2, song_bank, names, lb)[0],song1, song2) for song1, song2 in combs]
        mix_scores.sort(reverse = True)
        print()
        limit = input('How many mix recommendations would you like?: ')
        print()
        for index in range(int(limit)):
            print(names[mix_scores[index][1]][0] + ' by '+ names[mix_scores[index][1]][1] + ' ---> '+ names[mix_scores[index][2]][0] + ' by ' + names[mix_scores[index][2]][1])
            print('------------------')
            print('Details:')
            print('Key: ' + key_map[song_bank[mix_scores[index][1]]['key']] + ' | ' + 'Key: '+key_map[song_bank[mix_scores[index][2]]['key']])
            print('Mode: ' + mode_map[song_bank[mix_scores[index][1]]['mode']] + ' | '+'Mode: '+mode_map[song_bank[mix_scores[index][2]]['mode']])
            print('BPM: ' + str(int(song_bank[mix_scores[index][1]]['tempo'])) + ' | ' + 'BPM: '+str(int(song_bank[mix_scores[index][2]]['tempo'])))
            if mix_scores[index][0]>2:
                print('Matching Lyrics: '+ mix_scores[index][3][0] + mix_scores[index][3][1])
            print()
        count=1
        while True:
            load_more = input('Would you like to load more? (y, n): ')
            if load_more == 'y':
                for index in range(count*int(limit), (count+1)*int(limit)):
                    print(names[mix_scores[index][1]][0] + ' by '+ names[mix_scores[index][1]][1] + ' ---> '+ names[mix_scores[index][2]][0] + ' by ' + names[mix_scores[index][2]][1])
                    print('------------------')
                    print('Details:')
                    print('Key: ' + key_map[song_bank[mix_scores[index][1]]['key']] + ' | ' + 'Key: '+key_map[song_bank[mix_scores[index][2]]['key']])
                    print('Mode: ' + mode_map[song_bank[mix_scores[index][1]]['mode']] + ' | '+'Mode: '+mode_map[song_bank[mix_scores[index][2]]['mode']])
                    print('BPM: ' + str(int(song_bank[mix_scores[index][1]]['tempo'])) + ' | ' + 'BPM: '+str(int(song_bank[mix_scores[index][2]]['tempo'])))
                    if mix_scores[index][0]>2:
                        print('Matching Lyrics: '+ mix_scores[index][3][0] + mix_scores[index][3][1])
                    print()
            count+=1
            if load_more == 'n':
                break
        print()
        print('If you would like to continue, press any button')
        keep_going = input('If you would like to stop, press x: ')
        print()
        if keep_going == 'x':
            break

def mix_between_playlists(wordplay = False):
    while True:
        query1 = input('Please enter the name of the first playlist you want to mix: ')
        print()
        result1 = playlist_query(query1)
        query2 = input('Please enter the name of the second playlist you want to mix: ')
        result2 = playlist_query(query2)
        combs, song_bank, names = song_combs_playlist(result1, result2)
        song_bank = (sp.audio_features(song_bank[0]), sp.audio_features(song_bank[1]))
        if wordplay:
            mix_scores = []
            for song1, song2 in combs:
                mix_scores.append((mix_score_playlist(song1, song2, song_bank, names, True), song1, song2))     
        else:
            mix_scores = [(mix_score_playlist(song1, song2, song_bank, names),song1, song2) for song1, song2 in combs]
        mix_scores.sort(reverse = True)
        print()
        limit = input('How many mix recommendations would you like?: ')
        print()
        for index in range(int(limit)):
            print(names[0][mix_scores[index][1]][0] + ' by '+ names[0][mix_scores[index][1]][1] + ' ---> '+ names[1][mix_scores[index][2]][0] + ' by ' + names[1][mix_scores[index][2]][1])
            print('------------------')
            print('Details:')
            print('Key: ' + key_map[song_bank[0][mix_scores[index][1]]['key']] + ' | ' + 'Key: '+key_map[song_bank[1][mix_scores[index][2]]['key']])
            print('Mode: ' + mode_map[song_bank[0][mix_scores[index][1]]['mode']] + ' | '+'Mode: '+mode_map[song_bank[1][mix_scores[index][2]]['mode']])
            print('BPM: ' + str(int(song_bank[0][mix_scores[index][1]]['tempo'])) + ' | ' + 'BPM: '+str(int(song_bank[1][mix_scores[index][2]]['tempo'])))
            print()
        count=1
        while True:
            load_more = input('Would you like to load more? (y, n): ')
            if load_more == 'y':
                for index in range(count*int(limit), (count+1)*int(limit)):
                    print(names[0][mix_scores[index][1]][0] + ' by '+ names[0][mix_scores[index][1]][1] + ' ---> '+ names[1][mix_scores[index][2]][0] + ' by ' + names[1][mix_scores[index][2]][1])
                    print('------------------')
                    print('Details:')
                    print('Key: ' + key_map[song_bank[0][mix_scores[index][1]]['key']] + ' | ' + 'Key: '+key_map[song_bank[1][mix_scores[index][2]]['key']])
                    print('Mode: ' + mode_map[song_bank[0][mix_scores[index][1]]['mode']] + ' | '+'Mode: '+mode_map[song_bank[1][mix_scores[index][2]]['mode']])
                    print('BPM: ' + str(int(song_bank[0][mix_scores[index][1]]['tempo'])) + ' | ' + 'BPM: '+str(int(song_bank[1][mix_scores[index][2]]['tempo'])))
                    print()
            count+=1
            if load_more == 'n':
                break
        print()
        print('If you would like to continue, press any button')
        keep_going = input('If you would like to stop, press x: ')
        print()
        if keep_going == 'x':
            break
def song_match(wordplay = False):
    while True:
        song_query = input('Please enter the name of the song you want to find a match to: ')
        song_result = track_query(song_query)
        pl_query = input('Please enter the name of the playlist you want to use: ')
        pl_result= playlist_query(pl_query)
        song_features = sp.audio_features(song_result)
        bpm, key = (song_features['tempo'], song_features['key'])
        
print("Welcome to DJaid")
print()
print("1. Find mixes in a playlist")
print("2. Find mixes between 2 playlists")
print()
while True:
    service_selection = input("Select which service you would like: ")
    print()
    if service_selection == '1':
        while True:
            wp = input("Would you like to include wordplay? (y/n): ")
            if wp == 'y':
                mixes_in_playlist(True)
                break
            if wp == 'n':
                mixes_in_playlist()
                break
            else:
                print('Please enter a valid selection')
    if service_selection == '2':
        while True:
            wp = input("Would you like to include wordplay? (y/n): ")
            if wp == 'y':
                mix_between_playlists(True)
                break
            if wp == 'n':
                mix_between_playlists()
                break
            else:
                print('Please enter a valid selection')
    if service_selection == '3':
        while True:
            wp = input("Would you like to include wordplay? (y/n): ")
            if wp == 'y':
            if wp == 'n':
            else:
                print('Please enter a valid selection')

    else:
        print('Please enter a valid selection')







