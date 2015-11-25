'''
Author: Paul Bruno

Description:

  - Encapsulates native openstack keystone client

  - Adds additional support for Operatonal API testing and Managment
'''
import os, sys, traceback
from sets import Set
import omfbase as omfbase
import time
from datetime import datetime, timedelta
from collections import defaultdict
from collections import namedtuple
import random

from omfcodes import ExitCodes
ec = ExitCodes()

class KeystoneClient (object):

  def __init__ (self, _class, **kwargs):
    ''' 
    Initialize KeystoneClient instance

    Creates a V2 and V3 authentication object

    INPUTS:
   
      * OMFClient class - instance of OMFClient

      * DICT - pointer to keyword argument list (version=2|3 is one primary option)

    RETURN:

      * KeystoneClient instance
 
    '''
    if (not _class) or (not isinstance(_class, omfbase.OMFCLIENT_CLASS)):
      sys.stderr.write('{0} {1}\n'.format(1511, ec.get(1511)))
      sys.exit(151)

    self.parent = _class
    ''' INSTANCE set parent to instance of OMFClient '''    

    self.name_filter = None
    ''' STRING generic namefilter '''

    self.status_filter = None
    ''' STRING generic status '''

    self.debug = self.parent.debug
    ''' BOOL set debug level based on parent '''

    try:
      from keystoneclient.auth.identity import v3
      import keystoneclient
      from keystoneclient.v2_0 import client
    except:
      raise omfbase.OMFImport(2202)

    self.keystoneclient = keystoneclient
    '''set passthru to native openstack keystone modeule for methods not in Client()'''

    try:

      _user, _password, _project = _class.init_client_meta(_class, kwargs)

      self.project = _project

      # create v2 client
      _v2 = client.Client(username=_user, password=_password, tenant_name=_project, auth_url=_class.host)

      if not isinstance(_v2, keystoneclient.v2_0.client.Client):
        _class.log_and_exit('Initialize Keystone v2 client failed', 700)

      _class.log_info('Created new {0}: {1}'.format(__name__, type(_v2)))

      # create v3 client
      auth = v3.Password(auth_url = _class.host,
                         username = _user,
                         password = _password,
                         project_id = _project)

      sess = keystoneclient.session.Session(auth=auth)

      _v3 = keystoneclient.v3.client.Client(session=sess, version=(2,))

      if not isinstance(_v3, keystoneclient.v3.client.Client):
        _class.log_and_exit('Initialize Keystone v3 client failed', 2200)

      _class.log_info('Created new {0}: {1}'.format(__name__, type(_v3)))

      self.client = _v2  #for default set to _v2, then parse incoming args 

      for k,v in kwargs.items():
        if 'version' in k:
          if v == 2:
            self.client = _v2
          elif v == 3:
            self.client = _v3
          else:
            None

    except Exception as e:
      _class.log_and_exit(e, 2200)

  ''' private methods '''


  ''' public methods '''


