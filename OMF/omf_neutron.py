'''
Maintainer: ADAPT

Author: Paul Bruno

Description:

  - Encapsulates native openstack neutron client

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

class NeutronClient (object):

  def __init__ (self, _class, **kwargs):
    '''
    Initialize NeutronClient instance

    INPUTS:
   
      OMFClient class - instance of OMFClient

      DICT - pointer to keyword argument list

    RETURN:

      NeutronClient instance
    '''

    if (not _class) or (not isinstance(_class, omfbase.OMFCLIENT_CLASS)):
      sys.stderr.write('{0} {1}\n'.format(1511, ec.get(1511)))
      sys.exit(151)


    self.new_floating_ip_wait = 120 #in test takes ~ 4 seconds
    ''' INT wait time seconds when creating new floating ip addr '''

    self.pause = 2
    ''' INT pause while loop waiting for new floating ipaddr '''

    self.parent = _class
    ''' INSTANCE set parent to instance of OMFClient '''

    self.name_filter = None
    ''' STRING generic namefilter '''

    self.status_filter = None
    ''' STRING status filter '''

    self.debug = self.parent.debug
    ''' BOOL set debug level based on parent '''

    try:
      from neutronclient.v2_0 import client
      import neutronclient.v2_0 
    except:
      raise omfbase.OMFImport(2008)

    self.neutronclient = neutronclient.v2_0 # use for native neutron methods not wrapped in this class
    '''set passthru to native openstack neutron v2 module for methods not in Client()'''

    try:
   
      _user, _password, _project = _class.init_client_meta(_class, kwargs)

      neutron = client.Client(username=_user, password=_password,tenant_name=_project, auth_url=_class.host)

      if not isinstance(neutron, neutronclient.v2_0.client.Client):
        _class.log_and_exit('Initialize Neutron client failed', 2000)

      _class.log_info('Created new {0}: {1}'.format(__name__, type(neutron)))

      self.client = neutron

    except Exception as e:
      _class.log_and_exit(e, 2000)

  ''' private methods '''
  def _networks(self):
    
    obj = []
    nlist = None
    _stderr = sys.stderr
    f = open('trash','w')
    sys.stderr = f

    try:
      nlist = self.client.list_networks()
    except Exception as e:
      sys.stderr = _stderr
      f.close
      self.parent.log_and_exit(e, 2002)

    sys.stderr = _stderr
    f.close

    for k,nets in nlist.items():
      for n in nets:
        if (self.name_filter):
          if (n.name == self.name_filter):
            obj.append(n)
        else:
          obj.append(n)

    return obj 

  ''' public methods '''
  def get_networks(self, namefilter=None):
    '''
    Returns a list of Openstack Networks

    INPUTS:

      * STRING namefilter - optional network name filter

    RETURN:

      LIST openstack networks
    '''
    if(namefilter):
      self.name_filter = namefilter

    runningtime, obj = omfbase.trace(self._networks)
    self.parent.log_and_print_info('Networks query took: {0}'.format(runningtime))

    return obj 
