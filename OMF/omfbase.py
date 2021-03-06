'''
Author: Paul Bruno

Provides:

  - defaults and utilities for managing Openstack
'''

import os, sys, traceback, inspect
from sets import Set 
from datetime import datetime, timedelta
import time
import argparse
import ast
import omf_client

known_environments = [env.strip() for env in open('../credentials/environments', 'r')]
'''The known Openstack environments to be supported'''

OMFCLIENT_CLASS = omf_client.OMFClient

class OMFImport(Exception):
  pass

class credentials(object):
  '''
  Basic credentials parser class'''

  def __init__(self, environment):

    def _out(m):
      print m
      sys.stderr.write('1510')
      sys.exit(151)

    if not environment in known_environments:
      _out('{0} is not a supported environment'.format(environment))

    creds = {i.strip().split("=")[0] : i.strip().split("=")[1] for i in open('../credentials/{0}'.format(environment), 'r')}

    try:
      self.host = creds['host']
      '''the openstack host url'''
    except:
      _out('Missing host in credentials file {0}'.format('../credentials/{0}'.format(environment)))
    try:
      self.user = creds['user']
      '''the openstack user account'''
    except:
      _out('Missing user in credentials file {0}'.format('../credentials/{0}'.format(environment)))
    try:
      self.password = creds['password']
      '''the openstack user password'''
    except:
      _out('Missing password in credentials file {0}'.format('../credentials/{0}'.format(environment)))
    try:
      self.project = creds['project']
      '''the openstack tenant'''
    except:
      _out('Missing project in credentials file {0}'.format('../credentials/{0}'.format(environment)))
    try:
      self.domain = creds['domain']
      '''the openstack domain'''
    except:
      _out('Missing domain in credentials file {0}'.format('../credentials/{0}'.format(environment)))


def dump_attributes(obj):
  '''
  Print a formatted list of attributes on python object

  INPUT:

    ANY python object

  RETURN:

   none
  '''
  ctr = 0

  print "\nObject Attributes:\n"
  while ctr < len(dir(obj)):
    print dir(obj)[ctr], '\t', type(dir(obj)[ctr])
    ctr+=1

  sys.exit(0)

def common_args():
  '''
  Builds ArgumentParser and fills with common arguments for all OS Clients

    debug - enable verbose logging and print
  
    user - valid openstack user name

    password - valid openstack user password
 
    host - valid openstack host connect url

    project - valid openstack tenant 
    
  INPUTS:

    none

  RETURN:
  
    ArgumentParser object

  '''
  parser = argparse.ArgumentParser()

  parser.add_argument(
    '--debug',
    help="toggle debug",
    action='store_true')

  parser.add_argument(
    '--user',
    help='Openstack user.',
    default=None)

  parser.add_argument(
    '--password',
    help='Openstack password.',
    default=None)

  parser.add_argument(
    '--host',
    help='Openstack auth_url.',
    default=None)

  parser.add_argument(
    '--project',
    help='Openstack tenant (project).',
    default=None)

  parser.add_argument(
    '--osenv',
    choices=known_environments,
    help='OpenStack Environment. Use instead of passing credentials in.',
    default=None)

  return parser


def check_client_args(*args):
  '''
  Iterates arguments passed to OMFClient class

  INPUT:
  
    DICT *args - key value pair of parameters

  RETURN:

    INT missing parameter count

  '''
  keys = args[0].keys()
  values = args[0].values()

  missing_param_ctr = 0

  if ( (not 'host' in keys) or (not values[keys.index('host')])):
    missing_param_ctr+=1

  if not 'user' in keys:
    missing_param_ctr+=1

  if not 'password' in keys:
    missing_param_ctr+=1

  if not 'project' in keys:
    missing_param_ctr+=1

  return missing_param_ctr


def _print (text=None):

  print '{0}'.format(str(text))

def _log (data=None, state='info'):

  # state options [INFO | WARNING | ERROR]
  with open("OMFOpenStack.log", 'a') as f:
    _log = '{0} {1}: {2}\n'.format(str(datetime.now()), state.upper(), str(data))
    f.write(_log)

#TODO: create a tracewrapper that can support multiple arguments to the function we are tracing
#This code below doesn't work right in that use case


def trace_wrapper(func):
  '''
  Wraps timing around input function

  INPUT:

    function

  RETURN:

    function (time delta, function return)

  '''
  def wrapper(*arg, **kw):
    t1 = time.time()
    res = func(*arg, **kw)
    t2 = time.time()

    return (t2 - t1), res

  return wrapper

@trace_wrapper
def trace(func, *args, **kwargs):

  '''
  Tracing function to time wrap function calls.

  Uses decorator trace_wrapper()

  INPUTS:

    FUNCTION func - valid function
 
    LIST args - list or function inputs

    DICT - keyword arg list
 
  RETURN:

    function (timedelta, object)

  '''
  return func(*args, **kwargs)

def print_pretty_columns(obj, columns):
  '''
  Print formatted columns.
  Get length of columns to determine how many columns
  
  INPUTS:
 
   LIST obj - generic list object to iterate

   LIST columns - ordered list of column names to show

  RETURN:

   None
  '''

  if not obj or not columns:
    return

  column_index = 0

  meta_column = [0 for x in range(len(columns))]

  pad = 2

  try:
    for x in obj:
      tctr = 0
      while tctr < len(columns):
        meta_column[tctr] = max(meta_column[tctr], len(unicode(getattr(x, columns[tctr]))))
        tctr+=1

    ''' at this point we have the max mength of each column in columns[] '''
    ctr = 0
    for x in obj:
      tctr = 0
      output = ''
      while tctr < len(columns):
        meta_column[tctr] = max(meta_column[tctr], len(unicode(getattr(x, columns[tctr]))))

        output = output + unicode(getattr(x, columns[tctr])).ljust(meta_column[tctr]+pad, ' ')
        tctr+=1

      print output

  except Exception as e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 3, file = sys.stdout)
    raise RuntimeError('{0}\n{1}'.format(e, type(e)))

  return

def print_pretty_dict(obj):
  '''
  Print formatted columns of key value pairs

  INPUT:

    DICT dictionary of key value pairs

  RETURN:

    None

  '''
  maxk, maxv, pad = 0, 0, 2
  
  try:
    for k,v in obj.items():
      maxk = max(maxk, len(k)) #always a str
      maxv = max(maxv, len(str(v))) #not always a str

    for k,v in obj.items():
      #print "%-*s %*s" % (maxk, k, maxv, v)   #one to print it
      print k.ljust(maxk+pad, ' '), str(v).ljust(maxv+pad, ' ') #another way
  except Exception as e:
    raise RuntimeError('{0}\n{1}'.format(e, type(e)))

  return
