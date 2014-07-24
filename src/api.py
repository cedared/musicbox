#!/usr/bin/env python
#encoding: UTF-8

'''
网易云音乐 Api
'''

import re
import json
import requests
import hashlib
import md5
import urllib2
import os
from os.path import basename
import urlparse

home = os.path.expanduser("~")


# list去重
def uniq(arr):
    arr2 = list(set(arr))
    arr2.sort(key=arr.index)
    return arr2

default_timeout = 10
base_url = 'http://music.163.com/'
api_endpoint = '{0}api/'.format(base_url)

def download(url, localFileName = None):
    localName = basename(urlparse.urlsplit(url)[2])
    req = urllib2.Request(url)
    r = urllib2.urlopen(req)
    if r.info().has_key('Content-Disposition'):
        # If the response has Content-Disposition, we take file name from it
        localName = r.info()['Content-Disposition'].split('filename=')[1]
        if localName[0] == '"' or localName[0] == "'":
            localName = localName[1:-1]
    elif r.url != url:
        # if we were redirected, the real file name we take from the final URL
        localName = basename(urlparse.urlsplit(url)[2])
    if localFileName:
        # we can force to save the file as specified name
        localName = localFileName
    f = open(home + "/netease-musicbox/"+localName, 'wb')
    f.write(r.read())
    f.close()


class NetEase:
    def __init__(self):
        self.header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'
        }
        self.cookies = {
            'appver': '1.5.2'
        }

    def httpRequest(self, method, action, query=None, urlencoded=None, callback=None, timeout=None):
        if(method == 'GET'):
            url = action if (query == None) else (action + '?' + query)
            connection = requests.get(url, headers=self.header, timeout=default_timeout)

        elif(method == 'POST'):
            connection = requests.post(
                action,
                data=query,
                headers=self.header,
                timeout=default_timeout
            )

        connection.encoding = "UTF-8"
        connection = json.loads(connection.text)
        return connection

    # 登录
    def login(self, username, password, login_type):
        if login_type == 'passport':
            action = '{0}login/'.format(api_endpoint)
            data = {
                'username': username,
                'password': hashlib.md5( password ).hexdigest(),
                'rememberLogin': 'true'
            }

        elif login_type == 'cellphone':
            action = '{0}login/cellphone/'.format(api_endpoint)
            data = {
                'phone': username,
                'password': hashlib.md5( password ).hexdigest(),
                'rememberLogin': 'true'
            }

        try:
            return self.httpRequest('POST', action, data)
        except:
            return {'code': 501}

    # 用户歌单
    def user_playlist(self, uid, offset=0, limit=100):
        action = '{0}user/playlist/?offset={1}&limit={2}&uid={3}'.format(api_endpoint, offset, limit, uid)
        try:
            data = self.httpRequest('GET', action)
            return data['playlist']
        except:
            return []

    # 搜索单曲(1)，歌手(100)，专辑(10)，歌单(1000)，用户(1002) *(type)*
    def search(self, s, stype=1, offset=0, total='true', limit=60):
        action = '{0}search/get/web'.format(api_endpoint)
        data = {
            's': s,
            'type': stype,
            'offset': offset,
            'total': total,
            'limit': 60
        }
        return self.httpRequest('POST', action, data)

    # 新碟上架 http://music.163.com/#/discover/album/
    def new_albums(self, offset=0, limit=50):
        action = '{0}album/new?area=ALL&offset={1}&total=true&limit={2}'.format(api_endpoint, offset, limit)
        try:
            data = self.httpRequest('GET', action)
            return data['albums']
        except:
            return []

    # 歌单（网友精选碟） hot||new http://music.163.com/#/discover/playlist/
    def top_playlists(self, category='全部', order='hot', offset=0, limit=50):
        total = 'true' if offset else 'false'
        action = '{0}playlist/list?cat={1}&order={2}&offset={3}&total={4}&limit={5}'.format(api_endpoint, category, order, offset, total, limit)
        try:
            data = self.httpRequest('GET', action)
            return data['playlists']
        except:
            return []

    # 歌单详情
    def playlist_detail(self, playlist_id):
        action = '{0}playlist/detail?id={1}'.format(api_endpoint, playlist_id)
        try:
            data = self.httpRequest('GET', action)
            return data['result']['tracks']
        except:
            return []

    # 热门歌手 http://music.163.com/#/discover/artist/
    def top_artists(self, offset=0, limit=100):
        action = '{0}artist/top?offset={1}&total=false&limit={2}'.format(api_endpoint, offset, limit)
        try:
            data = self.httpRequest('GET', action)
            return data['artists']
        except:
            return []

    # 热门单曲 http://music.163.com/#/discover/toplist 50
    def top_songlist(self, offset=0, limit=100):
        action = '{0}discover/toplist'.format(base_url)
        try:
            connection = requests.get(action, headers=self.header, timeout=default_timeout)
            connection.encoding = 'UTF-8'
            songids = re.findall(r'/song\?id=(\d+)', connection.text)
            if songids == []:
                return []
            # 去重
            songids = uniq(songids)
            return self.songs_detail(songids)
        except:
            return []

    # 歌手单曲
    def artists(self, artist_id):
        action = '{0}artist/{1}'.format(api_endpoint, artist_id)
        try:
            data = self.httpRequest('GET', action)
            return data['hotSongs']
        except:
            return []

    # album id --> song id set
    def album(self, album_id):
        action = '{0}album/{1}'.format(api_endpoint, album_id)
        try:
            data = self.httpRequest('GET', action)
            return data['album']['songs']
        except:
            return []

    # song ids --> song urls ( details )
    def songs_detail(self, ids, offset=0):
        tmpids = ids[offset:]
        tmpids = tmpids[0:100]
        tmpids = map(str, tmpids)
        tmpids = ','.join(tmpids)
        action = '{0}song/detail?ids=[{1}]'.format(api_endpoint, tmpids)
        try:
            data = self.httpRequest('GET', action)
            return data['songs']
        except:
            return []

    # song id --> song url ( details )
    def song_detail(self, music_id):
        action = "{0}song/detail/?id={1}&ids=[{1}]".format(api_endpoint, music_id)
        try:
            data = self.httpRequest('GET', action)
            return data['songs']
        except:
            return []


    # 今日最热（0）, 本周最热（10），历史最热（20），最新节目（30）
    def djchannels(self, stype=0, offset=0, limit=50):
        action = '{0}discover/djchannel?type={1}&offset={2}&limit={3}'.format(base_url, stype, offset, limit)
        try:
            connection = requests.get(action, headers=self.header, timeout=default_timeout)
            connection.encoding = 'UTF-8'
            channelids = re.findall(r'/dj\?id=(\d+)', connection.text)
            channelids = uniq(channelids)
            return self.channel_detail(channelids)
        except:
            return []

    # DJchannel ( id, channel_name ) ids --> song urls ( details )
    # 将 channels 整理为 songs 类型
    def channel_detail(self, channelids, offset=0):
        channels = []
        for i in range(0, len(channelids)):
            action = '{0}dj/program/detail?id={1}'.format(api_endpoint, channelids[i])
            try:
                data = self.httpRequest('GET', action)
                channel = self.dig_info(data['program']['mainSong'], 'channels')
                channels.append(channel)
            except:
                continue
        return channels

    def encrypted_id(self, dfsId):
        dfsId =  str(dfsId)
        byte1 = bytearray('3go8&$8*3*3h0k(2)2')
        byte2 = bytearray(dfsId)
        byte1_len = len(byte1)
        for i in xrange(len(byte2)):
            byte2[i] = byte2[i]^byte1[i%byte1_len]
        m = md5.new()
        m.update(byte2)
        result = m.digest().encode('base64')[:-1]
        result = result.replace('/', '_')
        result = result.replace('+', '-')
        return result
        
   

    def make_url(self, dfsId):
        encId = self.encrypted_id(dfsId)
        mp3_url = "http://m1.music.126.net/%s/%s.mp3" % (encId, dfsId)
        return mp3_url

    def mp3_quality(self, song):
        defualtMusic = {'mp3_url': song['mp3Url'], 'bitrate': ''}
        try:
            hMusic = song.get('hMusic')
            hMusic['mp3_url'] = self.make_url(hMusic.get('dfsId'))
            hMusic['bitrate'] = str(hMusic.get('bitrate', 0)/1000) + 'kps'
        except:
            hMusic = defualtMusic

        try:
            mMusic = song.get('mMusic')
            mMusic['mp3_url'] = self.make_url(mMusic.get('dfsId'))
            mMusic['bitrate'] = str(mMusic.get('bitrate', 0)/1000) + 'kps'
        except:
            hMusic = defualtMusic

        try:
            lMusic = song.get('lMusic')
            lMusic['mp3_url'] = self.make_url(lMusic.get('dfsId'))
            lMusic['bitrate'] = str(lMusic.get('bitrate', 0)/1000) + 'kps'
        except:
            hMusic = defualtMusic

        try:
            bMusic = song.get('bMusic')
            bMusic['mp3_url'] = self.make_url(bMusic.get('dfsId'))
            bMusic['bitrate'] = str(bMusic.get('bitrate', 0)/1000) + 'kps'
        except:
            hMusic = defualtMusic

        # quility decrease
        return [hMusic, bMusic, defualtMusic, mMusic, lMusic]

    def dig_info(self, data ,dig_type):
        temp = []
        if dig_type == 'songs':
            for i in range(0, len(data) ):
                song_info = {
                    'song_id': data[i]['id'],
                    'artist': [],
                    'song_name': data[i]['name'],
                    'album_name': data[i]['album']['name'],
                    'cover_url': data[i]['album']['blurPicUrl'],
                    'mp3': self.mp3_quality(data[i])
                }
                if 'artist' in data[i]:
                    song_info['artist'] = data[i]['artist']
                elif 'artists' in data[i]:
                    for j in range(0, len(data[i]['artists']) ):
                        song_info['artist'].append( data[i]['artists'][j]['name'] )
                    song_info['artist'] = ', '.join( song_info['artist'] )
                else:
                    song_info['artist'] = '未知艺术家'

                temp.append(song_info)

        elif dig_type == 'artists':
            temp = []
            for i in range(0, len(data) ):
                artists_info = {
                    'artist_id': data[i]['id'],
                    'artists_name': data[i]['name'],
                    'alias': ''.join(data[i]['alias'])
                }
                temp.append(artists_info)

            return temp

        elif dig_type == 'albums':
            for i in range(0, len(data) ):
                albums_info = {
                    'album_id': data[i]['id'],
                    'albums_name': data[i]['name'],
                    'artists_name': data[i]['artist']['name']
                }
                temp.append(albums_info)

        elif dig_type == 'playlists':
            for i in range(0, len(data) ):
                playlists_info = {
                    'playlist_id': data[i]['id'],
                    'playlists_name': data[i]['name'],
                    'creator_name': data[i]['creator']['nickname']
                }
                temp.append(playlists_info)


        elif dig_type == 'channels':
            channel_info = {
                'song_id': data['id'],
                'song_name': data['name'],
                'artist': data['artists'][0]['name'],
                'album_name': 'DJ节目',
                'mp3': self.mp3_quality(data)
                }
            temp = channel_info

        return temp
