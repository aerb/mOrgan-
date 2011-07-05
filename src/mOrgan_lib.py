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
import shutil
import threading

import subprocess
from xml.etree.ElementTree import Element, dump, SubElement, ElementTree

from Tkinter import Tk
from tkFileDialog import askdirectory

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
xml_root = Element("root")

o_file = open(output_path,'w')
log_file = open(log_path,'w')
delete_path = 'delete_me'
music_root_dir = ''

conflict_count = 0
total_bytes = 0

quiet = True
strip_the = True

punc_regex = re.compile('[%s]' % re.escape(string.punctuation))
the_regex = re.compile('\Athe ')
and_regex = re.compile('\&')
dash_regex = re.compile('(?<=[A-Za-z0-9])\-(?=[A-Za-z0-9])')
space_regex = re.compile('[ \t]+')
to_delete_regex = re.compile('\"[^\"\r\n]*\"')

class mOrgan_lib(threading.Thread):
    
    def __init__(self,music_dir):
        threading.Thread.__init__(self)
        self.music_root_dir = music_dir
        self.morgan_library = {}
        
    
    def delete_stuff(self,really_delete):
        try:
            os.mkdir(delete_path)
        except OSError:
            pass
        
        for line in fileinput.input(output_path):
            if "#> Delete" in line:
                try:
                    found =  to_delete_regex.search(line)
                    src = found.group()
                    src = src.replace('\"','')
                except:
                    raise
                    
                print "deleting file:", src
                try:
                    if really_delete:
                        send2trash.send2trash(src)
                    else:                
                        shutil.move(src, join(delete_path,os.path.basename(src)))
                except:
                    print "Error: corrupt delete file."
                    traceback.print_exc(file=sys.stdout)   
    
    def find_musics(self,path):
        for i in listdir(path):
#            print join(path, i)
            if os.path.isdir(join(path, i)):
                self.find_musics(join(path, i))
            else:
                try:
                    self.are_you_musics(join(path, i))
                except mutagen.id3.ID3NoHeaderError:
                    log_file.write("ID3NoHeaderError on: %s\n\n" % join(path, i))
                except KeyError:
                    log_file.write("Key Error on: %s\n\n" % join(path, i))
                except IOError:
                    log_file.write("IO Error on: %s\n\n" % join(path, i))
                except:
                    to_write = sys.stdout
                    to_write.write("Unexpected error: %s\n" % join(path, i))
                    to_write.write("%s\n" % str(sys.exc_info()))
                    traceback.print_exc(file=to_write)
                    to_write.write("\n")
    
                
    def normalize_track_data(self,art,alb,name):
        art = self.normalize_strings(art)
        art = the_regex.sub('',art)
        alb = self.normalize_strings(alb)
        name = self.normalize_strings(name)
        return art,alb,name
                
    def normalize_strings(self,s):
        s = string.lower(s)             #convert to lower
        s = dash_regex.sub(' ',s)       #replace all joining dashes with space
        s = and_regex.sub(' and ',s)    #replace & with and
        s = punc_regex.sub('',s)        #strip all puncuation
        s = space_regex.sub('',s)       #remove redundant whitepsace (2+ spaces in row) 
        return s
    
                
    def are_you_musics(self,item):
        
        basename, ext = os.path.splitext(item)
        
        if ".m4a" == ext:
            f = M4A(item)
            artist,album,title = self.normalize_track_data(f['\xa9ART'],
                                                      f['\xa9alb'],
                                                      f['\xa9nam'])
        elif ".mp3" in item:
            f = EasyID3(item)
            artist,album,title = self.normalize_track_data(f['artist'][0],
                                                      f['album'][0],
                                                      f['title'][0])            
        elif ".mp4" == ext or ".m4p" == ext:
            f = EasyMP4(item)
            artist,album,title = self.normalize_track_data(f['artist'][0],
                                                      f['album'][0],
                                                      f['title'][0])
        elif ".flac" == ext:
            f = FLAC(item)
            artist,album,title = self.normalize_track_data(f['artist'][0],
                                                      f['album'][0],
                                                      f['title'][0])
        elif ".wma" == ext or ".wmv" == ext:
            f = ASF(item)
            artist,album,title = self.normalize_track_data(str(f['WM/AlbumArtist'][0]),
                                                      str(f['WM/AlbumTitle'][0]),
                                                      str(f['Title'][0]))
        elif ".ogg" == ext:
            f = OggVorbis(item)
            artist,album,title = self.normalize_track_data(f['artist'][0],
                                                      f['album'][0],
                                                      f['title'][0])
        else:
            return
    
        if artist not in self.morgan_library:
            self.morgan_library[artist] = {}
            print "Indexing artist: " , artist
        if  album not in self.morgan_library[artist]:
            self.morgan_library[artist][album] = {}
        if title not in self.morgan_library[artist][album]:
            self.morgan_library[artist][album][title] = item
            if not quiet:
                log_file.write("%s : %s : %s\n" % (artist, album, title))
        else:
            if self.evaluate_length(self.morgan_library[artist][album][title], item):
                self.evaluate_conflicting_items(self.morgan_library[artist][album][title], item)
    
    def evaluate_length(self,item1,item2):
        f1 = mutagen.File(item1)
        f2 = mutagen.File(item2)
        return 5 > math.fabs(f1.info.length - f2.info.length)
    
    def item_info(self,item,type):
        try:
            f = mutagen.File(item)
            if type is 'length':
                return f.info.length
            elif type is 'size':
                return os.path.getsize(item)
            elif type is 'bitrate':
                return f.info.bitrate
            elif type is 'sample_rate':
                return f.info.sample_rate
        except IOError:
            return None
                
    def item_info_s(self,item,type):
        return str(self.item_info(item,type))
    
    def evaluate_conflicting_items(self,item1, item2):
        global conflict_count
        global total_bytes
        
        conflict_count = conflict_count + 1
        
        xml_conflict = SubElement(xml_root, 'conflict')
        SubElement(xml_conflict, 'conflict_item',id = '1', location = item1, length = self.item_info_s(item1,'length'),size = self.item_info_s(item1,'size'),sample_rate=self.item_info_s(item1,'sample_rate'),bitrate=self.item_info_s(item1,'bitrate'))
        SubElement(xml_conflict, 'conflict_item',id = '2', location = item2, length = self.item_info_s(item2,'length'),size = self.item_info_s(item2,'size'),sample_rate=self.item_info_s(item2,'sample_rate'),bitrate=self.item_info_s(item2,'bitrate'))
        
        resolved = None
        resolved = self.evaluate_by_sample_rate(item1, item2)
        if resolved == None:
            resolved = self.evaluate_by_bit_rate(item1,item2)
        if resolved == None:
            resolved = self.evaluate_by_size(item1,item2)
        if resolved == None:
            resolved = self.evaluate_by_string_length(item1,item2)
        if resolved == None:
            resolved = item2
        
        xml_conflict.attrib['resolved']= resolved
        
        #TODO: Add define xml_conflict attributes for deletion 
        
        total_bytes = total_bytes + os.path.getsize(resolved)
    
    def evaluate_by_string_length(self,item1,item2):
        #silly, but if files identical delete one with longer string length
        #this will eliminate "Copy of song.mp3" vs. "song.mp3"
        
        if len(item1) > len(item2):
            return item1
        elif len(item1) < len(item2):
            return item2
        else:
            return None
    
    def evaluate_by_bit_rate(self,item1,item2):
        f1 = mutagen.File(item1)
        f2 = mutagen.File(item2)
        
        try:
            if f1.info.bitrate > f2.info.bitrate:
                return item2
            elif f1.info.bitrate < f2.info.bitrate:
                return item1
            else :
                return None
        except:
            return None
    
    def evaluate_by_size(self,item1,item2):
        f1 = os.path.getsize(item1)
        f2 = os.path.getsize(item2)
        try:
            
            if f1 > f2:
                return item2
            elif f1 < f2:
                return item1
            else:
                return None
        except:
            return None
    
    def evaluate_by_sample_rate(self,item1, item2):
        f1 = mutagen.File(item1)
        f2 = mutagen.File(item2)
        try:
    
            if f1.info.sample_rate > f2.info.sample_rate:
                return item2
            elif f1.info.sample_rate < f2.info.sample_rate:
                return item1
            else:
                return None
        except:
            return None
    
    
    def were_all_done_here(self):
        o_file.close()
        log_file.close()
    
    def open_playlist(self):
        if os.name == 'mac':
            subprocess.call(('open', output_path))
        elif os.name == 'nt':
            subprocess.call(('start', output_path), shell=True)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', output_path))
    
    def write_xml(self) :
        ElementTree(xml_root).write("conflicts.xml")
    
    def run(self):
        print 'lib ready'
        dir = self.music_root_dir
        self.find_musics(dir)
        self.write_xml()


#print 'hello'
#ml = mOrgan_lib('C:\Users\Adam\Music')
#ml.find_musics('C:\Users\Adam\Music')