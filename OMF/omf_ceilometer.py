'''
Maintainer: ADAPT

Author: Paul Bruno

Description:

  - Encapsulates native openstack ceilometer client

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

class CeiloClient (object):

  def __init__ (self, _class, **kwargs):
    ''' 
    Initialize CeiloClient instance

    INPUTS:
   
      OMFClient class - instance of OMFClient

      DICT - pointer to keyword argument list

    RETURN:

      CeiloClient instance
 
    '''
    if (not _class) or (not isinstance(_class, omfbase.OMFCLIENT_CLASS)):
      sys.stderr.write('{0} {1}\n'.format(1511, ec.get(1511)))
      sys.exit(151)

    self.parent = _class
    ''' set parent to instance of OMFClient '''

    self._name_filter = None
    ''' generic name filter '''

    self._status_filter = None
    ''' generic status filter '''

    self._metric_filter = None
    ''' metric filter '''

    self.debug = self.parent.debug
    ''' set debug level to the parent level '''

    try:
      import ceilometerclient
      from ceilometerclient import client
      from ceilometerclient.common import utils
    except:
      raise omfbase.OMFImport(2103)

    self.ceilometerclient = ceilometerclient
    '''set passthru to native openstack ceilometer module for method not in Client()'''

    try:

      _user, _password, _project = _class.init_client_meta(_class, kwargs)

      self.project = _project

      ''' NON LAMBDA WAY OF CREATING THE CLIENT '''
      keystone = {}
      keystone['os_username'] = _user
      keystone['os_password'] = _password
      keystone['os_auth_url'] = _class.host
      keystone['os_tenant_name'] = _project

      ceilo = client.get_client(2, **keystone)

      self.client = ceilo

      if not isinstance(ceilo, ceilometerclient.v2.client.Client):
        _class.log_and_exit('Invalid Ceilometer client.', 2100)

      _class.log_info('Created new {0}: {1}'.format(__name__, type(self.client)))

    except Exception as e:
      _class.log_and_exit(e, 2100)


  ''' private methods '''
  def _metrics(self):
    '''
    Filters should be set in the class before calling this internal method

    Available filters:

      self._name_filter
      self._metric_filter

    '''     
    obj = []
    mlist = None
    try:
      mlist = self.client.meters.list()
    except Exception as e:
      self.parent.log_and_exit(e, 2101)

    sid = None
 
    if (self._name_filter):
      try:
        sid = self.parent.nova_client._map_human_to_id('server', self._name_filter, self.parent.nova_client.client.servers.list())
      except Exception as e:
        self.parent.log_and_exit(e, 1604)

    for m in mlist:

      if (self._metric_filter) or (self._name_filter):
        if (self._metric_filter):
          if (m.name == self._metric_filter):
            if (sid):
              if (sid in m.resource_id):
                obj.append(m) #match name filter, add metric
                return obj
            else:
              obj.append(m) #no name filter, add metric
              continue
          else:
            continue
        elif (sid):
          if (sid in m.resource_id):
            obj.append(m) #match name filter, add metric
        else:
          #shouldn't ever get here!
          obj.append(m)

      else: #no filters
        obj.append(m)

    return obj 

  ''' public methods '''

  def get_metrics(self, namefilter=None, metric=None):
    '''
    Look up ceilometer metric

    INPUT:
    
      STRING namefilter - openstack instance server name to filter on

      STRING metric - specify a single metric to get

    RETURN:

      LIST of openstack metric objects
    ''' 
    if (namefilter):
      if (self.debug):
        self.parent.log_and_print_info('Setting namefilter to {0}'.format(namefilter))
      self._name_filter = namefilter

    if (metric):
      if (self.debug):
        self.parent.log_and_print_info('Setting metric filter to {0}'.format(metric))
      self._metric_filter = metric

    runningtime, obj = omfbase.trace(self._metrics)
    self.parent.log_and_print_info('Metrics query took: {0}'.format(runningtime))

    return obj 

