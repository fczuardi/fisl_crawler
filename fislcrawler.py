# -*- coding: utf-8 -*-

# FISL Crawler: Crawl pages from FISL 11 Papers NG proposal platform
# and copy the data to a structured database.
#
# http://github.com/fczuardi/fisl_crawler
#
# Copyright (c) 2010, Fabricio Zuardi
# All rights reserved.
#  
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of the author nor the names of its contributors
#     may be used to endorse or promote products derived from this
#     software without specific prior written permission.
#  
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__ = ('Fabricio Zuardi', 'fabricio@fabricio.org', 'http://fabricio.org')
__license__ = "BSD"

import sys
import getopt
import re
import urllib
import urllib2
import csv
import htmlentitydefs
import simplejson as json

#CONSTANTS
BASE_PROPOSAL_URL = 'http://verdi.softwarelivre.org/papers_ng/activity/view'
OUTPUT_FORMATS = ['csv','json']

#GLOBAL FLAGS
verbose = None

first_id = 1
last_id = 5 #812

def usage():
  print """
FISL Crawler

Parameters:
  -h, --help:\t\tPrint this message.
  -s, --start:\t\tFrom id
  -e, --end:\t\tTo id
  -f, --format:\t\tThe output format. Available formats: %s
  -i, --indent:\t\tIf output format can be pretty printed(json for example) use the number of white spaces to use as indent level.
  -o, --output-file:\tSave the output to a given filename.
  -v, --verbose:\tPrint extra info while performing the tasks.
""" % (', '.join(OUTPUT_FORMATS))


def main():
  table = []
  results_format = 'csv'
  output_file = sys.stdout
  indent_level = None
  
  if(len(sys.argv) < 2):
    return usage()
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hs:e:vf:o:i:", ["help", "start=", "end=", "verbose", "format=", "output-file=", "indent="])
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    elif o in ("-s", "--start"):
      first_id = int(a)
    elif o in ("-e", "--end"):
      last_id = int(a)
    elif o in ("-v", "--verbose"):
      verbose = True
    elif o in ("-f", "--format"):
      results_format = a
    elif o in ("-o", "--output-file"):
      output_file = file( a, "wb" )
    elif o in ("-i", "--indent"):
      indent_level = int(a)
    else:
      assert False, "unhandled option"
  
  for i in range(first_id,last_id+1):
    log("Getting page %s" % i)
    content = get_page(i)
    if content:
      if extract_data(content,i):
        table.append(extract_data(content,i))
    else:
      print "No data."
  print_results(table,results_format,output_file, indent_level)
  output_file.close()

"""Load the contents of a web page. Returns False if error or the content if success.
"""
def get_page(page_id):
  url = "%s?id=%s" % (BASE_PROPOSAL_URL,page_id)
  log("Acessing %s\t" % url)
  try:
    f = urllib2.urlopen(url)
    content = f.read()
    log("Success.")
    return content;
  except urllib2.HTTPError, e:
    if e.code == 401:
      log('Not authorized.')
    elif e.code == 404:
      log('Page not found.')
    elif e.code == 503:
      log('Service unavailable.')
    else:
      log('Unknown error: ')
  except urllib2.URLError, e:
    log("Error %s" % e.reason)
  return False

def extract_data(html,id):
  html = decode_htmlentities(html).encode('utf8')
  entry_pattern = '<title>(.*?)</title>.*?<abstract>(.*?)</abstract>.*?<descr>(.*?)</descr>.*?<area id.*?<name>(.*?)</name>'
  matches = re.search(entry_pattern, html, re.S|re.M)
  if matches:
    return {
      'title'     : matches.group(1)
      ,'abstract' : matches.group(2)
      ,'proposal' : matches.group(3)
      ,'track'    : matches.group(4)
      ,'id'       : id
    }
  else :
    return None

def print_results(table, fmt, output_file, indent):
  log(table)
  if fmt == 'csv':
    keys = table[0].keys()
    #write header
    output_file.write("%s\n" % ','.join(keys))
    #write rows
    writer = csv.DictWriter(output_file, keys, quoting=csv.QUOTE_ALL)
    writer.writerows(table)
  elif fmt == 'json':
    output = json.dumps(table,indent=indent)
    output_file.write(output)
  else:
    print str(table)
  

from htmlentitydefs import name2codepoint as n2cp
import re

def decode_htmlentities(string):
    """
    Decode HTML entities–hex, decimal, or named–in a string
    @see http://snippets.dzone.com/posts/show/4569

    >>> u = u'E tu vivrai nel terrore - L&#x27;aldil&#xE0; (1981)'
    >>> print decode_htmlentities(u).encode('UTF-8')
    E tu vivrai nel terrore - L'aldilà (1981)
    >>> print decode_htmlentities("l&#39;eau")
    l'eau
    >>> print decode_htmlentities("foo &lt; bar")                
    foo < bar
    """
    def substitute_entity(match):
        ent = match.group(3)
        if match.group(1) == "#":
            # decoding by number
            if match.group(2) == '':
                # number is in decimal
                return unichr(int(ent))
            elif match.group(2) == 'x':
                # number is in hex
                return unichr(int('0x'+ent, 16))
        else:
            # they were using a name
            cp = n2cp.get(ent)
            if cp: return unichr(cp)
            else: return match.group()

    entity_re = re.compile(r'&(#?)(x?)(\w+);')
    return entity_re.subn(substitute_entity, string)[0]


def log(m):
  if verbose: print(m)
  
if __name__ == "__main__":
  main()