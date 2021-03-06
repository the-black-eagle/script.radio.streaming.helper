#!/usr/bin/python
# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  (C) Black_eagle 2016 - 2018
#
#  WINDOW PROPERTIES SET BY THIS SCRIPT
#
#  srh.Artist -             contains the name of the artist
#  srh.Track -              contains the track name
#  srh.TrackInfo -          track information as scraped from either TADB or last.fm (if any found)
#  srh.Stationname -        name of radio station playing
#  srh.Logopath -           path to logo if found, else empty string
#  srh.Artist.Thumb -       thumb of the current artist
#  srh.Artist.Banner -      banner of the current artist
#  srh.Album -              track the album is off if the addon can find a match (note that this may not be accurate as we just match the first album we find with that track on)
#  srh.Year -               the year 'srh.Album' is from if the addon can find a match
#  srh.MBIDS -              Mbid(s) of the current artist(s)
#  srh.AlbumCover -         Path to local album cover if found (takes precedence), url to online cover if one exists, else artist thumb if available, otherwise empty string
#  srh.RecordLabel -        Name of label the album was released on if available
#  srh.AlbumDescription -   Description of album from tadb if one exists
#  srh.AlbumReview -        Album review from tadb if one exists
#
#  streaming-radio-helper-running - true when script running
#
# ** All window properties are set for the MusicVisualisation window (12006) **

import xbmc

import xbmcvfs

import xbmcaddon

import xbmcgui

import urllib

import urllib2

import sys

import re

from resources.lib.audiodb import audiodbinfo as settings

from resources.lib.utils import *

import pickle

import datetime

if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json

from threading import Timer

def do_count_notifications(counts):

    dialog_text = 'Added %s artists this run, %s tracks with new info [CR] Cache holds %s tracks ' % (counts['new_artists'], counts['new_track_info'], counts['no_of_tracks'])
    xbmcgui.Dialog().notification(
        'Radio Streaming Helper',
        dialog_text,
        xbmcgui.NOTIFICATION_INFO,
        5000)
    dialog_text = dialog_text.replace('[CR] ', '')
    log(dialog_text, xbmc.LOGNOTICE)

    return



def script_exit(counts):
    """Clears all the window properties and stops the timer used for auto-saving the data"""

    WINDOW.clearProperty("streaming-radio-helper-running")
    WINDOW.clearProperty("srh.Artist")
    WINDOW.clearProperty("srh.Track")
    WINDOW.clearProperty("srh.TrackInfo")
    WINDOW.clearProperty("srh.Logopath")
    WINDOW.clearProperty("srh.Album")
    WINDOW.clearProperty("srh.Year")
    WINDOW.clearProperty("srh.Artist.Thumb")
    WINDOW.clearProperty("srh.Artist.Banner")
    WINDOW.clearProperty("srh.MBIDS")
    WINDOW.clearProperty("srh.Musicpath")
    WINDOW.clearProperty("srh.AlbumCover")
    WINDOW.clearProperty("srh.RecordLabel")
    WINDOW.clearProperty("srh.RealAlbumThumb")
    WINDOW.clearProperty("srh.realCDArt")
    WINDOW.clearProperty("srh.AlbumDescription")
    WINDOW.clearProperty("srh.AlbumReview")
    rt.stop()
    do_count_notifications(counts)
    log("Script Stopped", xbmc.LOGNOTICE)
    exit()

def no_track():
    """Sets the appropriate window properties when we have no track to display"""

    WINDOW.setProperty("srh.Artist", "")
    WINDOW.setProperty("srh.Track", "")
    WINDOW.setProperty("srh.TrackInfo", "")
    WINDOW.setProperty("srh.Logopath", "")
    WINDOW.setProperty("srh.Album", "")
    WINDOW.setProperty("srh.Year", "")
    WINDOW.setProperty("srh.Artist.Thumb", "")
    WINDOW.setProperty("srh.Artist.Banner", "")
    WINDOW.setProperty("srh.MBIDS", "")
    WINDOW.setProperty("srh.Musicpath", "")
    WINDOW.setProperty("srh.AlbumCover","")
    WINDOW.setProperty("srh.RecordLabel","")
    WINDOW.setProperty("srh.RealAlbumThumb","")
    WINDOW.setProperty("srh.realCDArt", "")
    WINDOW.setProperty("srh.AlbumDescription","")
    WINDOW.setProperty("srh.AlbumReview","")
    return False, False


def get_info(local_logo, testpath, searchartist, artist, multi_artist, already_checked, checked_all_artists):

    RealAlbumThumb = None
    AlbumDescription = None
    AlbumReview = None
    RealCDArt = None
    local_logo = False
    albumtitle = None
    trackinfo = None
    theyear = None
    cdArt = None
    if multi_artist:
        orig_artist = artist
    log("Checked all artists is %s" %checked_all_artists, xbmc.LOGDEBUG)
    if xbmcvfs.exists(testpath):     # See if there is a logo in the music directory
        local_logo = True
        log("Logo in Music Directory : Path is %s" %
            testpath, xbmc.LOGDEBUG)
    else:
        local_logo = False


    if onlinelookup == "true":
        mbid = get_mbid(searchartist, track, dict6, dict3, counts)
    else:
        mbid = None
    if checked_all_artists is True:
        logopath, ArtistThumb, ArtistBanner = get_cached_info(mbid, testpath, local_logo, searchartist, dict4, dict5)
    else:
        if tadb == "true":
            artist, logopath, ArtistThumb, ArtistBanner = search_tadb( local_logo, mbid, searchartist, dict4, dict5, checked_all_artists)
        else:
            logopath = ""
            ArtistThumb = ""
            ArtistBanner = ""
    log("artist thumb - %s" % ArtistThumb, xbmc.LOGDEBUG)
    log("artist banner - %s" % ArtistBanner, xbmc.LOGDEBUG)
    if local_logo:
        logopath = testpath
    if logopath:  # We have a logo to display
        WINDOW.setProperty("srh.Logopath", logopath)
    elif not logopath and not multi_artist:  # No logos to display
        WINDOW.setProperty("srh.Logopath", "")
        log("No logo in cache directory", xbmc.LOGDEBUG)
    if ArtistThumb:
        WINDOW.setProperty("srh.Artist.Thumb", ArtistThumb)
    if ArtistBanner:
        WINDOW.setProperty("srh.Artist.Banner", ArtistBanner)
    WINDOW.setProperty("srh.Musicpath", BaseString)

    if checked_all_artists is True:
        already_checked, albumtitle, theyear, trackinfo = get_remaining_cache(artist, track, dict1, dict2, dict7)

    if not already_checked:
        log("Not checked the album and year data yet for this artist", xbmc.LOGDEBUG)
        already_checked, albumtitle, theyear, trackinfo = get_year(
            artist, track, dict1, dict2, dict3, dict7, already_checked, counts)

    if albumtitle and not multi_artist:
        # set if single artist and got album
        WINDOW.setProperty("srh.Album", albumtitle)
        log("Single artist - Window property srh.Album set", xbmc.LOGDEBUG)
    elif albumtitle and multi_artist and (WINDOW.getProperty("srh.Album") == ""):
        WINDOW.setProperty("srh.Album", albumtitle)

        log("Multi artist - srh.Album was empty - now set to %s" %
            albumtitle, xbmc.LOGDEBUG)
    elif not albumtitle and (not multi_artist):
        # clear if no title and not multi artist
        WINDOW.setProperty("srh.Album", "")
        log("No album title for single artist", xbmc.LOGDEBUG)
    elif not albumtitle and multi_artist:
        log("Not changing album cover for multi-artist", xbmc.LOGDEBUG)
    log("Album set to [%s]" % albumtitle, xbmc.LOGDEBUG)
    if albumtitle:
        RealAlbumThumb, RealCDArt, AlbumDescription, AlbumReview = get_album_data(artist, track, albumtitle, dict8, dict9, dict10, dict11, dict12, RealCDArt, RealAlbumThumb, AlbumDescription, AlbumReview)
    if RealCDArt:
        WINDOW.setProperty("srh.RealCDArt", RealCDArt)
        log("Real CDArt", xbmc.LOGDEBUG)
    if trackinfo:
        trackinfo = trackinfo + '\n'
        WINDOW.setProperty(
            "srh.TrackInfo",
            trackinfo.encode('utf-8'))
    else:
        WINDOW.setProperty("srh.TrackInfo", "")
    if AlbumDescription:
        WINDOW.setProperty("srh.AlbumDescription", AlbumDescription.encode( 'utf-8' ))
    if AlbumReview:
        WINDOW.setProperty("srh.AlbumReview", AlbumReview.encode( 'uft-8' ))
    if theyear and theyear != '0' and (not multi_artist):
        WINDOW.setProperty("srh.Year", theyear)
#            data_out_year = theyear
    elif theyear and multi_artist and(WINDOW.getProperty("srh.Year") == ""):
        WINDOW.setProperty("srh.Year", theyear)
    elif (not theyear or (theyear == 0)) and (not multi_artist):
        WINDOW.setProperty("srh.Year", "")
    if (albumtitle) and (theyear):
        log("Album & year details found : %s, %s" %
            (albumtitle, theyear), xbmc.LOGDEBUG)
    elif (albumtitle) and not (theyear):
        log("Found album %s but no year" %
            albumtitle, xbmc.LOGDEBUG)
    else:
        log("No album or year details found", xbmc.LOGDEBUG)
    type_of_cover, _pathToAlbumCover, cdArt = get_local_cover(BaseString, artist, track, albumtitle)
    log("Realalbum thumb is %s" % RealAlbumThumb, xbmc.LOGDEBUG)
    if type_of_cover == 1:
        WINDOW.setProperty("srh.AlbumCover", _pathToAlbumCover) # use local cover if available
        log("Local cover", xbmc.LOGDEBUG)
    elif (type_of_cover != 1) and RealAlbumThumb is not None:
        WINDOW.setProperty("srh.AlbumCover", RealAlbumThumb) # use tadb cover if available and no local cover
        log("tadb cover", xbmc.LOGDEBUG)
    elif type_of_cover == 2:
        WINDOW.setProperty("srh.AlbumCover", _pathToAlbumCover) # fallback to artist thumb if available
        log("Artist thumb", xbmc.LOGDEBUG)
    if cdArt:
        WINDOW.setProperty( "srh.RealCDArt", cdArt )  # override online art with local art if available

    if multi_artist:
        WINDOW.setProperty("srh.Artist", orig_artist.encode('utf-8'))
    else:
        WINDOW.setProperty("srh.Artist", artist.encode('utf-8'))
    if track:
        WINDOW.setProperty("srh.Track", track.encode('utf-8'))
    else:
        WINDOW.setProperty("srh.Track", "No track info available")
    return already_checked


try:
    WINDOW = xbmcgui.Window(12006)
    if WINDOW.getProperty("streaming-radio-helper-running") == "true":
        log("Script already running - Not starting a new instance", xbmc.LOGNOTICE)
        exit(0)
    if not xbmc.getCondVisibility("Player.IsInternetStream"):
        log("Not playing an internet stream - quitting", xbmc.LOGNOTICE)
        exit(0)
    if BaseString == "":
        addon.openSettings(addonname)
    WINDOW.setProperty("streaming-radio-helper-running", "true")
    language = xbmc.getLanguage(xbmc.ISO_639_1).upper()
    log("Version %s started" % addonversion, xbmc.LOGNOTICE)
    log("----------Settings-------------------------", xbmc.LOGNOTICE)
    log("Use fanart.tv : %s" % fanart, xbmc.LOGNOTICE)
    log("use tadb : %s" % tadb, xbmc.LOGNOTICE)
    for key in replacelist:
        log("Changing %s to %s" %
            (key, replacelist[key]), xbmc.LOGNOTICE)
    if luma:
        log("Lookup details for featured artists", xbmc.LOGNOTICE)
    else:
        log("Not looking up details for featured artists", xbmc.LOGNOTICE)
    log("Language is set to %s" % language, xbmc.LOGNOTICE)
    log("----------Settings-------------------------", xbmc.LOGNOTICE)
    log("Setting up addon", xbmc.LOGNOTICE)
    artistlist = load_artist_subs()
    already_checked = False
    log("aready_checked is set to [%s] " % str(already_checked))
    if xbmcvfs.exists(logostring + "data.pickle"):
        dict1, dict2, dict3, dict4, dict5, dict6, dict7, dict8, dict9, dict10, dict11, dict12 = load_pickle()
    my_size = len(dict1)
    log("Cache contains %d tracks" % my_size, xbmc.LOGNOTICE)
    counts['orig_no_of_tracks'] = my_size
    counts['new_artists'] = 0
    counts['new_track_info'] = 0
    counts['no_of_tracks'] = 0
    cut_off_date = todays_date - time_diff
    log("Cached data obtained before before %s will be refreshed if details are missing" %
        (cut_off_date.strftime("%d-%m-%Y")), xbmc.LOGNOTICE)
    rt = RepeatedTimer(900, save_pickle, dict1, dict2,
                       dict3, dict4, dict5, dict6, dict7, dict8, dict9, dict10, dict11, dict12, counts)


    # Main Loop
    while (not xbmc.abortRequested):
        if xbmc.getCondVisibility("Player.IsInternetStream"):
            if lastfm_first_time == 1:
                ct = datetime.datetime.now().time().second
                if lastfm_delay == ct:
                    current_track = get_lastfm_info(lastfm_username)
                    lastfm_delay = set_timer(5)
            else:
                current_track = xbmc.getInfoLabel("Player.Title")
                json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "xbmc.GetInfoLabels", "params":{"labels": ["player.Filename"]}, "id": 1}' )
                file_playing = _json.loads(json_query).get(
                    'result').get('player.Filename')
            try:
                current_track = current_track.decode('utf-8')
            except BaseException:  # can't decode track
                pass  # continue with track as is
            if not file_playing:
                file_playing = current_track
            if firstpass == 0:
                firstpass = 1
                log("File playing is %s" % file_playing, xbmc.LOGDEBUG)
                log("Track playing is [%s]" %
                    current_track, xbmc.LOGDEBUG)
                station, station_list = check_station(file_playing)
                log("Station name was : %s - changed to %s" %
                    (station_list, station), xbmc.LOGDEBUG)
                WINDOW.setProperty("srh.Stationname", station)
            if use_lastfm_setting.get(station) == 'true':
                lastfm_username = lastfm_usernames.get(station)
                use_lastfm = True
            else:
                use_lastfm = False
            if use_lastfm:
                if lastfm_first_time == 0:
                    lastfm_delay = set_timer(5)
                    lastfm_first_time = 1
                    current_track = get_lastfm_info(lastfm_username)
            if "T - Rex" in current_track:
                current_track = current_track.replace(
                    "T - Rex", "T. Rex") # fix artist name for tadb (even though 'T - Rex' is technically correct)
            if " - " in current_track:
                try:
                    x = slice_string(current_track, ' - ', 1)
                    artist = current_track[x + 3:]
                    track = current_track[:x]
                    artist = artist.strip()
                    # Make sure there are no extra spaces in the artist name as
                    # this causes issues
                    artist = " ".join(artist.split())

                    pos = slice_string(track, replace1, 1)
                    if pos != -1:
                        track = track[:pos]
                    else:
                        pos = slice_string(track, replace2, 1)
                        if pos != -1:
                            track = track[:pos]
                        else:
                            pos = slice_string(track, replace3, 1)
                            if pos != -1:
                                track = track[:pos]
                    track = track.strip()
                    if (swaplist.get(station) == "true") and (use_lastfm == False):
                        temp1 = track
                        track = artist
                        artist = temp1
                except Exception as e:
                    log("[Exception %s] while trying to slice current_track %s" % (
                        str(e), current_track), xbmc.LOGDEBUG)
                #if (artist.upper() == "ELO") or (artist.upper() ==
                                                 #"E.L.O") or (artist.upper() == "E.L.O."):
                    #artist = "Electric Light Orchestra"
                try:
                    artist = next(v for k, v in artistlist.items()
                                  if k == (artist))
                except StopIteration:
                    pass
                if was_playing != track:
                    # clear all window properties on track change
                    checked_all_artists, already_checked = no_track()
                    searchartists = []
                    station, station_list = check_station(file_playing)
                    WINDOW.setProperty("srh.Stationname", station)
                    log("Track changed to %s by %s" %
                        (track, artist), xbmc.LOGDEBUG)
                    log("Playing station : %s" % station, xbmc.LOGDEBUG)
                    logopath = ''
                    testpath = BaseString + artist + "/logo.png"
                    testpath = xbmc.validatePath(testpath)

                    mbid_json_data = {}
                    if not any(matches in artist for matches in featured_artist_match):
                        try:

                            url = 'https://musicbrainz.org/ws/2/artist/?query=artist:%s&fmt=json' % urllib.quote(artist.encode('utf-8'))

                            log( "Initial lookup on mbrainz for artist [%s]" % artist)
                            response = load_url(url)                            # see if this is a valid artist before we try splitting the string
                            mbid_json_data = _json.loads(response)              # if we get a match, keep the current artist as is - else try and split to individual artists
                            if mbid_json_data['artists'][0]['score'] < 80 :
                                searchartist = split_artists(artist)
                            else:
                                searchartist = artist
                        except:
                            searchartist = split_artists(artist)
                    else:
                        searchartist = split_artists(artist)

                    log("Searchartist is %s" % searchartist)
                    x = searchartist.find('~')
                    log("searchartist.find('~') result was %s" % str(x))
                    if x != -1:
                        searchartists = searchartist.split('~')
                    else:
                        searchartists.append(searchartist)
                    num_artists = len(searchartists)
                    if num_artists > 1 and luma:
                        multi_artist = True
                    else:
                        multi_artist = False
                    mbids = ""
                    first_time = True
                    artist_index = 0
                    already_checked = get_info(local_logo,
                        testpath,
                        searchartists[artist_index].strip(),
                        artist,
                        multi_artist,
                        already_checked,
                        checked_all_artists)
                    for z in range(0, len(searchartists)):
                        if searchartists[z] in dict6:
                            log("Setting mbid for artist %s to %s" %
                                (searchartists[z], dict6[searchartists[z]]))
                            if first_time:
                                mbids = mbids + dict6[searchartists[z]]
                                first_time = False
                            else:
                                mbids = mbids + "," + \
                                    dict6[searchartists[z]]
                    if mbids:
                        WINDOW.setProperty('srh.MBIDS', mbids)
                    else:
                        WINDOW.setProperty('srh.MBIDS', mbid)
                    was_playing = track
                    log("Was playing is set to [%s]" % was_playing)
                    et = set_timer(delay)
                    if multi_artist:
                        log("et is [%d]" % (et))
                if multi_artist:
                    cs = datetime.datetime.now().time().second
                    if cs == et:
                        log("Lookup next artist")
                        artist_index += 1
                        if artist_index == num_artists:
                            artist_index = 0
                            checked_all_artists = True
                        already_checked = get_info(local_logo,
                            testpath,
                            searchartists[artist_index].strip(),
                            artist,
                            multi_artist,
                            already_checked,
                            checked_all_artists)
                        et = set_timer(delay)
                        log("et is now [%d]" % et)
            else:
                checked_all_artists, already_checked = no_track()
            xbmc.sleep(1000)
        else:
            log("Not an internet stream", xbmc.LOGDEBUG)
        if (xbmc.Player().isPlayingAudio() == False) or (not xbmc.getCondVisibility("Player.IsInternetStream")):
            log("Not playing audio or not an internet stream")
            save_pickle(dict1, dict2, dict3, dict4, dict5, dict6, dict7, dict8, dict9, dict10, dict11, dict12, counts)
            script_exit(counts)

except Exception as e:
    log("Radio Streaming Helper has encountered an error in the main loop and needs to close - %s" %
        str(e), xbmc.LOGERROR)
    xbmcgui.Dialog().notification(
        "Radio Streaming Helper",
        'A fatal error has occured. Please check the Kodi Log',
        xbmcgui.NOTIFICATION_INFO,
        5000)
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)), xbmc.LOGERROR)
    save_pickle(dict1, dict2, dict3, dict4, dict5, dict6, dict7, dict8 , dict9, dict10, dict11, dict12, counts)

    script_exit(counts)
