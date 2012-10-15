#!/usr/bin/env python

# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <filip@j03.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp
# ----------------------------------------------------------------------------

from base64 import urlsafe_b64encode
from os.path import join as joinpath
import pickle
import sys
from copy import deepcopy
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.template import add_to_builtins

try:
    # Python 2.5
    from hashlib import sha1
except ImportError:
    # Python 2.4
    from sha import sha as sha1

add_to_builtins('django_hashedmediaplus.tags')

HASHEDMEDIA_HASHFUN = getattr(settings, "HASHEDMEDIA_HASHFUN", sha1)
HASHEDMEDIA_DIGESTLENGTH = getattr(settings, "HASHEDMEDIA_DIGESTLENGTH", 9999)
HASHEDMEDIA_ROOT = getattr(settings, 'HASHEDMEDIA_ROOT', settings.MEDIA_ROOT)

HASHEDMEDIA_MANIFEST = getattr(settings, "HASHEDMEDIA_MANIFEST", "manifest.txt")
HASHEDMEDIA_MANIFEST_PATH = joinpath(HASHEDMEDIA_ROOT, HASHEDMEDIA_MANIFEST)

HASHEDMEDIA_CACHEKEY = getattr(settings, "HASHEDMEDIA_CACHEKEY", "django_hashedmedia")

HASHEDMEDIA_DICT_KEY = 'HASHEDMEDIA_DICT'


def digest(content):
    return urlsafe_b64encode(HASHEDMEDIA_HASHFUN(content).digest()[:HASHEDMEDIA_DIGESTLENGTH]).strip("=")


class HashfileRegistry(object):
    """Stores a registry of hashfile entries."""
    
    def __init__(self):
        """Constructor"""
        self.mapfile = HASHEDMEDIA_MANIFEST_PATH
        self.mapdata = {}
    
    def hash_and_register(self, filename_to_hash, filename_to_register=None):
        """Creates a relationship between:
        
        A - The filename you will refer to in your templates (original file)
        B - The new "hashed" filename, which results based on the contents of A
        """
        hashedfile = hashfile(filename_to_hash, no_cache=True, actualfile=filename_to_register)
        if filename_to_register:
            self.mapdata[filename_to_register] = hashedfile
        else:
            self.mapdata[filename_to_hash] = hashedfile
        return hashedfile
     
    def pprint(self):
        """Prints the mapfile"""
        from pprint import pprint
        pprint(self.mapdata)
     
    def save(self):
        """Saves the pickled mapfile to disk"""
        try:
            fhandle = open(self.mapfile, 'w')
        except IOError, msg:
            sys.exit("Can't pickle to mapfile %s: %s" % (self.mapfile, msg) )
        
        # Scrub the MEDIA_ROOT from the pickled data for portability
        
        cleandata = {}
        for key, val in self.mapdata.iteritems():
            newkey = key.replace(settings.MEDIA_ROOT, '').replace(settings.MEDIA_ROOT, '')
            cleandata[newkey] = val

        pickle.dump(cleandata, fhandle)
        fhandle.close()
        cache.delete(HASHEDMEDIA_CACHEKEY)
        if hasattr(settings, HASHEDMEDIA_DICT_KEY):
            settings.__delattr__(HASHEDMEDIA_DICT_KEY)

        print "\nWrote updated manifest file: %s\n" % self.mapfile
        
        return 
    
    def load(self):
        """Loads the pickled mapfile from disk"""
        try:
            fhandle = open(self.mapfile, 'r')
        except IOError, msg:
            sys.exit("Can't pickle to mapfile %s: %s" % (self.mapfile, msg) )
        data = pickle.load(fhandle)
        fhandle.close()
        
        # Reconstitute the MEDIA_ROOT from the pickled data (reverse save() )
        resdata = {}
        for key, val in data.iteritems():
            key = joinpath(settings.MEDIA_ROOT, key)
            resdata[key] = val
        
        return resdata


def hashfile(filename, no_cache=False, actualfile=None):
    if hasattr(settings, HASHEDMEDIA_DICT_KEY) and settings.HASHEDMEDIA_DICT:
        fromcache = getattr(settings, HASHEDMEDIA_DICT_KEY)
    else:
        fromcache = cache.get(HASHEDMEDIA_CACHEKEY)

    # If the pickled data is not already in the cache, 
    # load it from the picklejar and cache it now. 
    if not fromcache and not no_cache:
        fromcache = HashfileRegistry().load()
        cache.set(HASHEDMEDIA_CACHEKEY, fromcache)

    # Make sure we stow in settings so we stop hammering the cache server
    if not hasattr(settings, HASHEDMEDIA_DICT_KEY):
        setattr(settings, HASHEDMEDIA_DICT_KEY, fromcache)
        
    # When called from a tag, we want to return the hashfile or fail loudly.
    if fromcache and not no_cache:
        foundmap = fromcache.get(filename)
        if not foundmap:
            raise Exception, "No hashedmedia mapping for file %s" % filename
        return foundmap
    
    # Otherwise, we are generating a hash.
    extension = filename.split(".")[-1]
    
    # When using a temporary intermedia file, create the digest from that file
    # instead of the requested filename.
    if not actualfile:
        actualfile = filename
      
    hashed_filename = "%s.%s" % ( digest( open(actualfile).read() ), extension)
    return hashed_filename
    

    
