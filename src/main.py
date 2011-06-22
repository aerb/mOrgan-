'''
Created on Jun 18, 2011

@author: Adam
'''
import sys
import string
import re
import traceback
import math
import fileinput
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.m4a import M4A
from mutagen.easymp4 import EasyMP4
from mutagen.flac import FLAC
from mutagen.asf import ASF 
from mutagen.oggvorbis import OggVorbis

import send2trash

import os
from os import listdir
from os.path import join

output_path = "conflict_report.m3u"
log_path = "debugging.log"

o_file = open(output_path,'w')
log_file = open(log_path,'w')
music_root_dir = 'C:\Users\Adam\Documents\\test_dir'
#music_root_dir = "C:\Users\Adam\Music"

morgan_library = {}

quiet = True
strip_the = True

punc_regex = re.compile('[%s]' % re.escape(string.punctuation))
the_regex = re.compile('\Athe ')
and_regex = re.compile('\&')
dash_regex = re.compile('(?<=[A-Za-z0-9])\-(?=[A-Za-z0-9])')
space_regex = re.compile('[ \t]+')

def delete_stuff(really_delete):
    for line in fileinput.input(output_path):
        if "#>" in line:
            print line[10:]
            if really_delete:
                send2trash.send2trash(line[10:])

def find_musics(path):
    for i in listdir(path):
        if os.path.isdir(join(path, i)):
            find_musics(join(path, i))
        else:
            try:
                are_you_musics(join(path, i))
            except mutagen.id3.ID3NoHeaderError:
                log_file.write("ID3NoHeaderError on: %s\n\n" % join(path, i))
            except KeyError:
                log_file.write("Key Error on: %s\n\n" % join(path, i))
                traceback.print_exc(file=log_file)
            except IOError:
                log_file.write("IO Error on: %s\n\n" % join(path, i))
            except:
                log_file.write("Unexpected error: %s\n" % join(path, i))
                log_file.write("%s\n" % str(sys.exc_info()))
                traceback.print_exc(file=log_file)
                log_file.write("\n")

            
def normalize_track_data(art,alb,name):
    art = normalize_strings(art)
    art = the_regex.sub('',art)
    alb = normalize_strings(alb)
    name = normalize_strings(name)
    return art,alb,name
            
def normalize_strings(s):
    s = string.lower(s)             #convert to lower
    s = dash_regex.sub(' ',s)       #replace all joining dashes with space
    s = and_regex.sub(' and ',s)    #replace & with and
    s = punc_regex.sub('',s)        #strip all puncuation
    s = space_regex.sub('',s)       #remove redundant whitepsace (2+ spaces in row) 
    return s
            
def are_you_musics(item):
    
    basename, ext = os.path.splitext(item)
    
    if ".m4a" == ext:
        f = M4A(item)
        artist,album,title = normalize_track_data(f['\xa9ART'],
                                                  f['\xa9alb'],
                                                  f['\xa9nam'])
    elif ".mp3" in item:
        f = EasyID3(item)
        artist,album,title = normalize_track_data(f['artist'][0],
                                                  f['album'][0],
                                                  f['title'][0])            
    elif ".mp4" == ext or ".m4p" == ext:
        f = EasyMP4(item)
        artist,album,title = normalize_track_data(f['artist'][0],
                                                  f['album'][0],
                                                  f['title'][0])
    elif ".flac" == ext:
        f = FLAC(item)
        artist,album,title = normalize_track_data(f['artist'][0],
                                                  f['album'][0],
                                                  f['title'][0])
    elif ".wma" == ext or ".wmv" == ext:
        f = ASF(item)
        artist,album,title = normalize_track_data(str(f['WM/AlbumArtist'][0]),
                                                  str(f['WM/AlbumTitle'][0]),
                                                  str(f['Title'][0]))
    elif ".ogg" == ext:
        f = OggVorbis(item)
        artist,album,title = normalize_track_data(f['artist'][0],
                                                  f['album'][0],
                                                  f['title'][0])
    else:
        return

    if artist not in morgan_library:
        morgan_library[artist] = {}
        print "Indexing artist: " , artist
    if  album not in morgan_library[artist]:
        morgan_library[artist][album] = {}
    if title not in morgan_library[artist][album]:
        morgan_library[artist][album][title] = item
        if not quiet:
            log_file.write("%s : %s : %s\n" % (artist, album, title))
    else:
        if evaluate_length(morgan_library[artist][album][title], item):
            evaluate_conflicting_items(morgan_library[artist][album][title], item)

def evaluate_length(item1,item2):
    f1 = mutagen.File(item1)
    f2 = mutagen.File(item2)
    return 5 > math.fabs(f1.info.length - f2.info.length)

def evaluate_conflicting_items(item1, item2):
    f1 = mutagen.File(item1)
    f2 = mutagen.File(item2)
    
    o_file.write("# Conlict Found:\n")
    o_file.write(item1 + '\n')
    o_file.write(item2 + '\n')
    
    resolved = None
    
    try:
        o_file.write("# 1) length: %d, 2) length: %d\n" % (f1.info.length, f2.info.length))
        resolved = evaluate_by_sample_rate(item1, item2)
        if resolved == None:
            resolved = evaluate_by_bit_rate(item1,item2)
        else:
            evaluate_by_bit_rate(item1,item2)
            
        if resolved == None:
            resolved = evaluate_by_size(item1,item2)
        else:
            evaluate_by_size(item1,item2)
    except:
        pass
    
    if resolved != None:
        o_file.write("#> Delete \"%s\"\n" % str(resolved))
    else:
        o_file.write("# No best found. Randomly picking ...\n")
        o_file.write("#> Delete \"%s\"\n" % item2)
     
    o_file.write('\n')

def evaluate_by_bit_rate(item1,item2):
    f1 = mutagen.File(item1)
    f2 = mutagen.File(item2)
    
    o_file.write("# 1) bitrate: %d, 2) bitrate: %d\n" % (f1.info.bitrate, f2.info.bitrate))
    
    if f1.info.bitrate > f2.info.bitrate:
        return item2
    elif f1.info.bitrate < f2.info.bitrate:
        return item1
    else :
        return None

def evaluate_by_size(item1,item2):
    f1 = os.path.getsize(item1)
    f2 = os.path.getsize(item2)
    
    o_file.write("# 1) size: %d, 2) size: %d\n" % (f1, f2))
    
    if f1 > f2:
        return item2
    elif f1 < f2:
        return item1
    else:
        return None

def evaluate_by_sample_rate(item1, item2):
    f1 = mutagen.File(item1)
    f2 = mutagen.File(item2)
    
    o_file.write("# 1) sample_rate: %d, 2) sample_rate: %d\n" % (f1.info.sample_rate, f2.info.sample_rate))
    
    if f1.info.sample_rate > f2.info.sample_rate:
        return item2
    elif f1.info.sample_rate < f2.info.sample_rate:
        return item1
    else:
        return None
                
find_musics(music_root_dir)
o_file.close()
log_file.close()