'''
Author: Paul Bruno

Description:

  - Encapsulates native openstack Cinder client

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

''' Container for Volume object with basic details '''
global Volume
Volume = namedtuple('Volume', 'name, id, status, size, zone, created, description, instances')

''' Container for Volume object with full details '''
global VolumeFull
VolumeFull = namedtuple('VolumeFull', 'status, name, attachments, availability_zone, created_at, \
                                      description, volume_type, snapshot_id, source_volid, metadata, id, size')

class CinderClient (object):

  def __init__ (self, _class, **kwargs):
    ''' 
    Initialize CinderClient instance

    INPUTS:
   
      * OMFClient class - instance of OMFClient

      * DICT - pointer to keyword argument list

    RETURN:

      * CinderClient instance
 
    '''

    if (not _class) or (not isinstance(_class, omfbase.OMFCLIENT_CLASS)):
      sys.stderr.write('{0} {1}\n'.format(1511, ec.get(1511)))
      sys.exit(151)

    try:
      import cinderclient
      from cinderclient.client import Client
    except:
      raise omfbase.OMFImport(1709)

    self.parent = _class
    '''set parent to instance of OMFClient'''

    self.vol_size = 2
    ''' default volume size in GB'''

    self.vol_config = None
    '''volume config placeholder'''

    self._namefilter = None
    '''generic volume name filter'''

    self._statusfilter = None
    '''generic status filter'''

    self.debug = self.parent.debug
    '''set debug level to parent level'''

    self.cinderclient = cinderclient 
    '''set passthru to native cinder client for methods not in Client()'''

    try:

      _user, _password, _project = _class.init_client_meta(_class, kwargs)

      self.project = _project

      self.client = Client('2', _user, _password, _project, auth_url=_class.host)

      if not isinstance(self.client, cinderclient.v2.client.Client):
        _class.log_and_exit('Initialize Cinder client failed', 1700)

      _class.log_info('Created new {0}: {1}'.format(__name__, type(self.client)))

    except Exception as e:
      _class.log_and_exit(e, 1700)


  ''' private methods '''

  def _quotas(self):
    obj = None
    try:
      obj = self.client.quotas.get(self.project)
    except Exception as e:
      self.parent.log_and_exit(e, 1704)

    return obj

  def _volumes(self):

    obj = []
    vlist = None

    try:
      vlist = self.client.volumes.list()
    except Exception as e:
      self.parent.log_and_exit(e, 1705)

    if (self._namefilter):
      for v in vlist:
        if v.name.lower() == self._namefilter.lower():
          obj.append(v)

    elif (self._statusfilter):
      for v in vlist:
        if v.status.lower() == self._statusfilter.lower():
          obj.append(v)
    else:
      obj = vlist

    return obj

  def _create_volume(self):

    #TODO: wait loop around wolume create checking for new volume self.vol_config['name']
    obj = None
    try:
      obj = self.client.volumes.create(**self.vol_config)
    except Exception as e:
      self.parent.log_and_exit(e, 1706)

    waiting = True
    _start = datetime.now()
    sys.stdout.write('Waiting for volume to be ready')
    while (waiting):
      waiting = False
      try:
        vols = self._volumes()
        if (vols):
          for v in vols:
            if v.name.lower() == obj.name.lower():
              if (v.status.lower() != 'available'):
                waiting = True
                sys.stdout.write('. ')
                sys.stdout.flush()
                time.sleep(1)
              else:
                self.parent.log_and_print_info('\nNew Volume {0} is ready.'.format(obj.name))
            
      except Exception as e:
        self.parent.log_and_exit(e, 1701)

    return obj


  ''' public methods '''

  def get_available_volumes(self):
    '''
    Get volumes with available status. If there are no available volumes, one will be created, so this method should \
    always return a non empty LIST [] 

    INPUT:
 
      * none

    RETURN:

      * LIST  Openstack Volume objects
    '''
    self._statusfilter = 'Available'

    runningtime, obj = omfbase.trace(self._volumes)
    self.parent.log_and_print_info('Volumes query took: {0}'.format(runningtime))

    if (not obj):
      self.parent.log_and_print_info('Creating new volume as needed...')

      cfg = {}
      cfg['name'] = 'VOL_{0}'.format(str(random.getrandbits(24)))
      cfg['description'] = "added dynamically for scale"
      cfg['size'] = self.vol_size
 
      if(self.create_volume(cfg)):
        runningtime, obj = omfbase.trace(self._volumes)
        self.parent.log_and_print_info('Volumes create took: {0}'.format(runningtime))

    return obj

  def get_volumes_basic(self, namefilter=None):
    '''
    Basic volumes lookup 

    INPUT:
 
      * STRING namefilter - optional. filter by specific Volume name

    RETURN:

      * LIST Openstack Volume object
    '''
    if (namefilter):
      self._namefilter = namefilter

    runningtime, obj = omfbase.trace(self._volumes)
    self.parent.log_and_print_info('Volumes query took: {0}'.format(runningtime))

    return obj

  def get_volumes_info(self, namefilter=None):
    '''
    Detailed volume lookup

    INPUT:
 
      * STRING namefilter - optional. filter by specific Volume name

    RETURN:

      * NamedTuple VolumeFull 
    '''
    if (namefilter):
      self._namefilter = namefilter

    runningtime, obj = omfbase.trace(self._volumes)
    self.parent.log_and_print_info('Volumes query took: {0}'.format(runningtime))

    _volumes = []

    for v in obj:
      _vol = VolumeFull(status = v.status, name = v.name, attachments = v.attachments, availability_zone = v.availability_zone, created_at = v.created_at, description = v.description, volume_type = v.volume_type, snapshot_id = v.snapshot_id, source_volid = v.source_volid, metadata = v.metadata, id = v.id, size = v.size)

      _volumes.append(_vol)

    return _volumes


  def create_volume(self, config, force=False):
    '''
    Create a new volume regardless of number of available volumes

    INPUT:
 
      * DICT config - dictionary of required volume data. name required at minimum

      * BOOL force - optional. force re-create volume if it pre-exists. default False

    RETURN:
    
      * Instance Openstack Volume object
    '''  
    if (not config):
      self.parent.log_and_exit('You must specify a volume config dictionary type name when creating', 1703)

    if (not config['name']):
      self.parent.log_and_exit('You must specify a Volume name.', 1703)

    if (not config['size']):
      config['size'] = self.vol_size

    vol = self.get_volumes_basic()

    for v in vol:
      if v.name == config['name']:
        self.parent.log_error('Duplicate Volume name. Name must not exist in tenent')
        if (force):
          self.parent.log_and_print_info('You specified to force re-create volume {0}'.format(config['name']))
          d = v.delete()
        else:
          self.parent.log_and_exit('Volume name specified is in use: {0}'.format(config['name']), 1707)

    self.vol_config = config

    runningtime, obj = omfbase.trace(self._create_volume)
    self.parent.log_and_print_info('Create Volume took: {0}'.format(runningtime))

    return obj

  def get_quotas(self):
    '''
    Basic lookup of quotas

    INPUTS:
   
      * none

    RETURN:

      * Instance Openstack Quota object
    '''
    runningtime, obj = omfbase.trace(self._quotas)
    self.parent.log_and_print_info('Quota query took: {0}'.format(runningtime))

    return obj
