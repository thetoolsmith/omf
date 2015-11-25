'''
Author: Paul Bruno

Description:

  - Encapsulates native openstack nova client

  - Adds additional support for Operatonal API testing and Managment

'''
import os, sys, traceback
from sets import Set 
import omfbase as omfbase
import time
from collections import defaultdict
from collections import namedtuple
from datetime import datetime, timedelta

from omfcodes import ExitCodes
ec = ExitCodes()

''' Container type for instance status'''
global Instance
Instance = namedtuple('Instance', 'host, name, uuid, status')

''' Container type for hypervisor/host status '''
global ComputeNode
ComputeNode = namedtuple('ComputeNode', 'hostname, id, network_up, api_up, status, has_nodes, servers')


class NovaClient (object):

  def __init__ (self, _class, **kwargs):

    '''
    Initialize NovaClient instance

    INPUTS:
   
      OMFClient class - instance of OMFClient

      DICT - pointer to keyword argument list

    RETURN:

      NovaClient instance
 
    '''

    if (not _class) or (not isinstance(_class, omfbase.OMFCLIENT_CLASS)):
      sys.stderr.write('{0} {1}\n'.format(1511, ec.get(1511)))
      sys.exit(151)


    self.parent = _class 
    ''' set parent to instance of OMFClient '''
 
    self._status_filter = None
    ''' generic status filter '''

    self._name_filter = None
    ''' generic name filter '''

    self.wait_time = 2 #seconds
    ''' default time to wait '''

    self.debug = self.parent.debug
    ''' set debug level to parent level '''

    try:
      from novaclient import client
      import novaclient
    except:
      raise omfbase.OMFImport(1618)

    self.novaclient = novaclient
    '''set passthru to native openstack nova module for methods not in Client()'''

    self.ComputeNode = ComputeNode
    '''placeholder ComputeNode container type'''

    try:

      _user, _password, _project = _class.init_client_meta(_class, kwargs)

      nova = client.Client('2', _user, _password, _project, _class.host)

      if not isinstance(nova, novaclient.v2.client.Client):
        _class.log_and_exit('Failed to initialize Nova client', 1600)

      _class.log_info('Created new {0} {1}'.format(__name__,type(nova)))

      self.client = nova #the actual client
  
    except Exception as e:
      _class.log_and_exit(e, 1600)

  ''' private methods '''

  def _flavors(self):
    obj = None
    try:
      obj = self.client.flavors.list()
    except Exception as e:
      self.parent.log_and_exit(e,1603)

    return obj 

  def _volumes(self):
    '''
    Openstack native volume list lookup

    INPUTS: none

    RETURN:
	
      LIST volumes

    '''
    obj = None
    try:
      obj = self.client.volumes.list()
    except Exception as e:
      self.parent.log_and_exit(e,1606)

    return obj

  def _hypervisors (self):

    obj = []

    slist = None

    try:
      slist = self.client.hypervisors.list()
    except Exception as e:
      self.parent.log_and_exit(e, 1607) 

    if (self._name_filter):
      for s in slist:
        if (s.hypervisor_hostname.lower() == self._name_filter):
          obj.append(s)
    else:
      obj = slist

    return obj

  def _search_hypervisors (self):

    obj = None
    try:
      obj = self.client.hypervisors.search(self.hvhost, self.sflag)[0]
    except Exception as e:
      self.parent.log_and_exit(e, 1608) 

    return obj

  # OPTIONALLY FILTERS ON SERVER NAME
  def _instances (self):

    obj = []
    slist = None

    try:
      slist = self.client.servers.list()
    except Exception as e:
      self.parent.log_and_exit(e, 1604)

    if (self._name_filter):
      for s in slist:
        if (s.name == self._name_filter):
          obj.append(s)
    else:
      obj = slist

    return obj 

  # OPTIONALLY FILTERS ON HOST NAME
  def _host_instances (self):
 
    obj = []
    slist = None

    try:
      slist = self.client.servers.list()
    except Exception as e:
      self.parent.log_and_exit(e, 1604)

    if (self._name_filter):
      for s in slist:
        try:
          if (getattr(s, 'OS-EXT-SRV-ATTR:hypervisor_hostname').lower() == self._name_filter):
            obj.append(s)
        except Exception as e:
          self.parent.log_and_exit(e, 1619)

    else:
      obj = slist

    return obj

  def _populate_compute_nodes(self):

    ''' 
    return ComputeNode data set with network and api status, and other host info

    '''
    compute_nodes = set([])

    self.parent.log_info('Filtering on host name: {0}'.format(self._name_filter))

    if (self._name_filter):  
      all_hosts = self.get_hypervisors(namefilter=self._name_filter)
    else:
     all_hosts = self.get_hypervisors()

    hosts_with_server = [] #so we can add the servers{} items

    for h in all_hosts:
      if self.debug:
        self.parent.log_and_print_info('Checking status of host {0}'.format(h.hypervisor_hostname))

      hosts_with_server.append(self.hv_search(hvhost=h.hypervisor_hostname, sflag=True))

    for h in hosts_with_server:

      _hasnodes = True
  
      f = {}
      try:
        if (h.servers):
          for s in h.servers:
            f[s['name']] = s['uuid']
      except:
        None

      try: 
        cnode = self.ComputeNode(hostname = h.hypervisor_hostname, \
                          id = h.id, \
                          network_up = self.parent.is_reachable(h.hypervisor_hostname), \
                          api_up = True if (h.state.lower() == 'up') else False, \
                          status = h.status, \
                          has_nodes = _hasnodes, \
                          servers = tuple(f))

        compute_nodes.add(cnode)
      except Exception as e:
        self.parent.log_and_print_error('{0} {1} for {2}'.format(type(e),e,h.hypervisor_hostname))

    return compute_nodes


  ''' public methods with traceing'''

  def get_flavors(self):
    '''
    Openstack native flavor list lookup

    INPUTS: none

    RETURN:
	
      LIST flavors

    '''
    runningtime, obj = omfbase.trace(self._flavors)
    self.parent.log_and_print_info('Flavors query took: {0}'.format(runningtime))

    return obj

  def map_human_to_id(self, oname,value, obj):
    '''
    Translates Openstack object property human_id to uuid

    INPUT:
    
      STRING oname - general object name (used for logging and print so could be any user specified)

      STRING value - human_id or display name value to match when iterating the object

      OBJECT obj - an openstack object LIST to iterate 

    RETURN:

      STRING - uuid
    
    '''
    ret = None
    for o in obj:
      if o.human_id.lower() == value.lower():
        ret = o.id
    if (not ret):
      self.parent.log_and_print_error('{0} specified does not exist. {1}'.format(oname, value))

    return ret

  def map_id_to_human(self, oname,value, obj):
    '''
    Translate Openstack uuid to readable human display name 
 
    INPUTS:

      STRING oname - object name as specified by user (logging only) but should be either id or resource_id

      STRING value - the id or resource_id value to map

      OBJECT obj - any object as returned form a native OS lookup (i.e. servers.list()), iterated over to find the match

    RETURN:

      STRING - human readable name

    '''
    ret = None
    for o in obj:
      if oname == 'resource_id':
        if o.id in value:
          ret = o.human_id
      else:
        if o.id == value:
          ret = o.human_id 
 
    if (not ret):
      self.parent.log_and_print_error('{0} specified does not exist. {1}'.format(oname, value))

    return ret


  # CREATED NEW SERVER INSTANCE AND WAIT FOR ACTIVE STATUS
  def create_instance(self, cfg=None, unique=False):

    '''
    Creates a new Openstack server instance and waits for Active status

    INPUTS:

      DICT cfg - dictionary of required properties when creating instances
                 STRINGS network, flavor, image, name

      BOOL unique - optional. specified to check for duplicate server names

    RETURN:

      INSTANCE novaclient.v2.servers.Server
      
    '''
    obj = None

    if (not cfg):
      return obj

    if not isinstance(cfg, dict) or (not cfg['name']) or (not cfg['image']) or (not cfg['flavor']) or (not cfg['network']):
     self.parent.log_and_exit('Invalid server inputs. name, image, flavor, network required.\n{0}'.format(cfg), 1612)

    if (unique):
      try:
        for s in self.client.servers.list():
          if s.name == cfg['name']:
            self.parent.log_and_exit('Duplicate Server name, you specified unique.', 1616)
      except Exception as e:
        self.parent.log_and_exit(e, 1604)

      self.parent.log_and_print_info('We are good to go, specified name not found!!!!')

    try:
      _network = self.map_human_to_id('network', cfg['network'], self.client.networks.list())
    except Exception as e:
      self.parent.log_and_exit(e, 1605)
    try:
      _flavor = self.map_human_to_id('flavor', cfg['flavor'], self.client.flavors.list())
    except Exception as e:
      self.parent.log_and_exit(e, 1603)
    try:
      _image = self.map_human_to_id('image', cfg['image'], self.client.images.list())
    except Exception as e:
      self.parent.log_and_exit(e, 1615)

    if (not _network) or (not _image) or (not _flavor):
      self.parent.log_and_exit('Failed to map human->id for one of image, flavor, network.\n{0}'.format(cfg), 1613)

    others = {}
    others['nics'] = [{'net-id': _network}]

    try:
      obj = self.client.servers.create(name=cfg['name'], flavor=_flavor, image=_image, **others)
    except Exception as e:
      self.parent.log_exception(e)

    if (not obj):
      self.parent.log_and_exit('Failed to create server {0}'.format(cfg['name']), 1609)

    self.parent.log_and_print_info('Created new server {0} id: {1} {2}'.format(cfg['name'], obj.id, obj.human_id))

    # WAIT FOR READINESS
    waiting = True
    _start = datetime.now()
    sys.stdout.write('Waiting for server to be ready')
    while (waiting):
      waiting = False
      try:
        _s = self.get_instance(namefilter=obj.name)
        if (_s):
          if (not _s[0].status.upper() == 'ACTIVE'):
            waiting = True
            sys.stdout.write('. ')
            sys.stdout.flush()
            time.sleep(1)
          else:
            self.parent.log_and_print_info('New Instance {0} is ready.'.format(obj.name))
            self.parent.log_and_print_info('Create New Instance took: {0}'.format(datetime.now() - _start))
      except Exception as e:
        self.parent.log_and_exit(e, 1609)

    return obj

  def attach_server_volume(self, server=None, volume_id=None, device='/dev/foo'):
    '''
    Attaches a Volume to a server instance and waits for verification

    INPUTS:

      STRING server - a human readable valid server name

      INT volume_id - Openstack uuid volume id
 
      STRING device - file share path to attach the volume to. Default /dev/foo

    RETURN:

      0 - success
      1 - failure
      
    '''
    if (not server) or (not volume_id):
      self.parent.log_and_exit('server, volume_id and device are required when attaching volume to server', 110)

    try:
      ret = self.client.volumes.create_server_volume(server_id=server.id, volume_id=volume_id, device=device)
    except Exception as e:
      self.parent.log_and_print_error(ec.get(1610))
      if (self.debug):
        print type(e)(e)
      return 1

    # RE-GET THE INSTANCE OBJECT AND CHECK IS ATTACHED
    _s = self.get_instance(namefilter=server.name)[0]
    waiting = True
    timer = self.wait_time
    is_attached = False
    while (waiting) and (timer):
      waiting = False
      try:
        if getattr(_s, 'os-extended-volumes:volumes_attached')[0].items()[0][1] != volume_id:
          waiting = True
          timer-=1
          time.sleep(1)
        else:
          is_attached = True
      except Exception as e:
        print type(e)(e)
        return 1
      
    if (is_attached):
      self.parent.log_and_print_info('Successfully attached volume {0} to server {1}'.format(volume_id, server.name))
      return 0
    else:
      self.parent.log_and_print_error('Failed to attach volume {0} to server {1}'.format(volume_id, server.name))
      return 1

  # RETURNS OS SERVER OBJECT
  def get_instance(self, namefilter=None):
    '''
    Look up instance or instances

    INPUT:	
     
      STRING namefilter - optional instance server name to lookup

    RETURN:
 
      LIST openstack Server objects
    '''
    if (namefilter):
      self._name_filter = namefilter

    runningtime, obj = omfbase.trace(self._instances)
    self.parent.log_info('Server query took: {0}'.format(runningtime))

    return obj

  def get_host_instances(self, namefilter=None):
    '''
    Look up instances on one or all OS hosts

    INPUT:	
     
      STRING namefilter - optional. Specify a specific hypervisor

    RETURN:
 
      LIST openstack Server objects
    '''
    if (namefilter):
      self._name_filter = namefilter

    runningtime, obj = omfbase.trace(self._host_instances)
    self.parent.log_and_print_info('Host server instance query took: {0}'.format(runningtime))

    return obj

  # RETURNS OS HOST OBJECT
  def get_hypervisors(self, namefilter=None):
    '''
    Get list of all or one hypervisor

    INPUT:	
     
      STRING namefilter - optional. Specify a specific hypervisor

    RETURN:
 
      LIST openstack hypervisor host name
    '''
    if (namefilter):
      self._name_filter = namefilter

    runningtime, obj = omfbase.trace(self._hypervisors)
    self.parent.log_and_print_info('Host query took: {0}'.format(runningtime))

    return obj


  def get_hypervisors_info(self, namefilter=None):
    '''
    Get list of details of all or one hypervisor

    INPUT:	
     
      STRING namefilter - optional. Specify a specific hypervisor

    RETURN:
 
      NamedTuple ComputeNode
    '''
    if (namefilter):
      self._name_filter = namefilter

    runningtime, obj = omfbase.trace(self._populate_compute_nodes)
    self.parent.log_and_print_info('Populate ComputeNode type took: {0}'.format(runningtime))

    return obj


  def hv_search(self, hvhost=None, sflag=False):
    '''
    Lookup hypervisor object

    INPUT:	
     
      STRING hvhost - optional. Specify a specific hypervisor

      BOOL sflag - optional return server property of hypervisor. default False

    RETURN:
 
      LIST openstack hypervisor object
    '''

    if not (hvhost):
      self.parent.log_and_exit('Hypervisor host required.', 114)

    self.sflag = sflag
    self.hvhost = hvhost
    runningtime, obj = omfbase.trace(self._search_hypervisors)
    self.parent.log_and_print_info('Hypervisor Search query took: {0}'.format(runningtime))

    return obj

  def get_instances_with_status(self, servers=None, namefilter=None):
    '''
    Get list of details of instance on all or one hypervisor

    INPUT:	
      
      LIST servers - set of openstack server instances
      
      STRING namefilter - optional. Specify a specific hypervisor

    RETURN:
 
      NamedTuple Instance
    '''
    dataset = set([])

    if (namefilter):
      self._name_filter = namefilter

    if (not servers):
      self.parent.log_and_exit('HypervisorServers object required', 1614)

    runningtime, obj = omfbase.trace(self._instances)
    self.parent.log_and_print_info('Instance query took: {0}'.format(runningtime))

    for s in servers:
      _uuid = s.items()[0][1]
      _node = s.items()[1][1]
      _status = None
      _host = None

      for i in obj:

        if (_node.lower() == getattr(i, 'OS-EXT-SRV-ATTR:instance_name').lower()):
          _status = i.status
          _host = getattr(i, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
          break
          #can also get status by getattr(i, 'OS-EXT-STS:vm_state') 

      _instance = Instance(host = _host, \
                           name = _node, \
                           uuid = _uuid, \
                           status = _status)

      dataset.add(_instance)

    return dataset
