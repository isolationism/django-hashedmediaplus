#!/usr/bin/env python

# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <filip@j03.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp
# ----------------------------------------------------------------------------
# ... And <kevin@weblivion.com> rewrote it. You can still buy either of us
# a beer, though.

from django.conf import settings
from django.core.management.base import BaseCommand
from django_hashedmediaplus import hashfile, HashfileRegistry
from os import listdir, mkdir
from copy import deepcopy
from os.path import join as joinpath, exists, isdir, abspath
from os import unlink
from shutil import copy2
import re
from pprint import pprint

HASHEDMEDIA_ROOT = getattr(settings, 'HASHEDMEDIA_ROOT', settings.MEDIA_ROOT)


def _findmatch(root, itermatch, root_level=True):
    """Attempts to find files to hash; requires that the file be contained
    within the itermatch iterable"""
    
    # Strip the MEDIA_ROOT from the itermatch iterable
    if root_level:
        iterlist = []
        for fpath in itermatch:
            iterlist.append( joinpath(settings.MEDIA_ROOT, fpath) )
    else:
        iterlist = itermatch
    
    # Look through directories and return matches
    for item in [ joinpath(root, x) for x in listdir(root) ]:
        if isdir(item):
            for subitem in _findmatch(item, iterlist, False):
                if subitem in iterlist:
                    yield subitem
        else:
            if item in iterlist:
                yield item


def _substitute_links(filepath, bin_filemap):
    """Loads the file at filepath and attempts to locate references to files
    in bin_filemap. Where refs. are found, we perform substitution and return
    the new temporary file object; if no refs are found we return the original
    filepath unmolested."""
    
    # Load the file's contents
    try:
        fhandle = open(filepath, 'r')
    except IOError, msg:
        sys.exit("Error opening %s: %s" % filepath, msg) 
    filecontents = fhandle.read()
    fhandle.close()
    dirtybuffer = False
    
    # Are there any URLs in the file?
    re_cssurl = re.compile("url\([^)]+\)", re.DOTALL)
    found_urls = re_cssurl.findall(filecontents)
    
    if found_urls:
        # One or more images is present; replace all known binary URLs
        for found_url in set( found_urls ):
            # Strip out nasty quotemarks around filenames (shame!)
            found_url = found_url.strip('\'"')
            
            fpath_rel = found_url.replace('url(', '').rstrip(' )').lstrip('./')
            fpath_abs = joinpath(settings.MEDIA_ROOT, fpath_rel)
            replace_url = bin_filemap.get(fpath_abs, None)
            
            if replace_url:
                dirtybuffer = True
                re_foundurl = re.compile( r"../%s" % (fpath_rel) )
                replace_filename = bin_filemap.get(fpath_abs)
                replace_string = "url(%s)" % (replace_filename)
                filecontents = re_foundurl.sub(replace_url, filecontents)
            
    # If the buffer is dirty write out a new temporary file and return it
    if dirtybuffer:
        from tempfile import mkstemp
        suffix = ".%s" % filepath.split('.')[-1]
        (wfd, wpath) = mkstemp(text=True, suffix=suffix)
        whandle = open(wpath, 'w')               
        whandle.write(filecontents)
        whandle.close()
        return wpath
        
    # Nothing found, return the original file
    else:
        return filepath


class Command(BaseCommand):
    
    def handle(self, *args, **kwargs):
        """Creates hashfiles from source files."""
        
        # Step 1: Get the necessary settings in order to proceed
        wipeold = getattr(settings, 'HASHEDMEDIA_WIPEOLD', False)
        try:
            bin_list = settings.HASHEDMEDIA_BINARY
            txt_list = settings.HASHEDMEDIA_TEXT
            
        except AttributeError, msg:
            import sys
            sys.exit("You must define HASHEDMEDIA_BINARY and HASHEDMEDIA_TEXT in \
                your settings.py file; otherwise there's nothing to hash.")
    
        hreg = HashfileRegistry()
    
        # Step 2: Map original binary paths to hashed file names
        bin_filemap = {}
        bin_paths = _findmatch(settings.MEDIA_ROOT, bin_list)
        
        for binfile in bin_paths:
            bin_filemap[binfile] = hreg.hash_and_register(binfile)
            
        # Step 3: Handle text files, seeking out dependencies and substituting 
        #         filenames for them using the bin_filemap dictionary
        txt_filemap = {}
        txt_paths = _findmatch(settings.MEDIA_ROOT, txt_list)
        for txtfile in txt_paths:
            newtxtfile = _substitute_links(txtfile, bin_filemap)
            txt_filemap[newtxtfile] = hreg.hash_and_register(newtxtfile, txtfile)
    
        # Process all files at once.
        all_filemap = deepcopy(bin_filemap)
        all_filemap.update(txt_filemap)
        
        # Create the hashedmedia root directory if it doesn't exist
        if not exists(HASHEDMEDIA_ROOT):
            mkdir(HASHEDMEDIA_ROOT)
            
        # Wipe out old hashedmedia files if requested
        if wipeold:
            def wipefiles(root):
                """Recursively wipes files from a directory"""
                filelist = listdir(root)
                for filename in filelist:
                    if filename == ".svn":
                        continue
                    if isdir(filename):
                        wipefiles(filename)
                    else:
                        try:
                            unlink( joinpath(root, filename) )
                        except OSError:
                            pass
            wipefiles(HASHEDMEDIA_ROOT)
            
        # Perform the file copy now.
        for oldfile, newfile in all_filemap.iteritems():
            oldpath = abspath(oldfile)
            newpath = abspath( joinpath(HASHEDMEDIA_ROOT, newfile) )
            copy2(oldpath, newpath)
        
        # Pickle the hash to disk now.
        hreg.save()

        # Done.
        return

