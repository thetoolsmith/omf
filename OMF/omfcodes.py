'''
Author: Paul Bruno

Description:

Mapping of Encapsulated opstack client class specific exit codes.

The purpose is to allow exit code event based post actions or triggers
from systems such as zabbix, rundeck etc....

HOW TO IMPLEMENT: 

  from omfcodes import ExitCodes
  ec = ExitCodes()

USE EXAMPLES:

  * print ec.codes  (get all codes available)

  * print ec.get(1500) (get specific code DESCRIPTOR from known int code)

  * print ec.get('OMF_NOVA_FAILED_CLIENT_INIT') (get specific EXIT CODE from known descriptor)

  * print ec.Omf.codes (get dictionary of all codes)

  * print ec.Nova.codes (get dictionary of client specific codes)

  * print ec.Cinder.codes (get dictionary of client specific codes)

  * print ec.get()  (gets all available codes)

  * print ec.get_defined() (gets all codes NOT undefined)

'''

class ExitCodes(object):

  ''' 
  Omf base class specific exit code table
  
  * Omf ......... 1500 - 1599 

  * Nova ........ 1600 - 1699 

  * Cinder ...... 1700 - 1799 

  * Glance ...... 1800 - 1899 

  * Heat ........ 1900 - 1999 

  * Neutron ..... 2000 - 2099 

  * Ceilometer .. 2100 - 2199 

  * Keystone .... 2200 - 2299
 
  '''
  class Omf(object):
    '''
    Base OMF class specific exit code table
    '''
    codes = dict.fromkeys(range(1500,1599), "undefined")
    codes[1500] = 'OMF_INVALID_EXIT_CODE'
    codes[1501] = 'OMF_OS_FAILED_CLIENT_INIT'
    codes[1502] = 'OMF_HOSTS_IN_BAD_STATE'
    codes[1503] = 'OMF_FAILED_HOST_EVACUATE'
    codes[1504] = 'OMF_CONFLICTING_PARAMETERS'
    codes[1505] = 'OMF_FAILED_HOSTS_DETECTED'
    codes[1506] = 'OMF_CATASTROPHIC_ALL_HOSTS_DOWN'
    codes[1507] = 'OMF_TOO_MANY_HOSTS_NEED_EVACUATION'
    codes[1508] = 'OMF_INVALID_PARAMETERS'
    codes[1509] = 'OMF_NO_FREE_VOLUMES'    
    codes[1510] = 'OMF_FAILED_CREDENTIALS'
    codes[1511] = 'OMF_FAILED_INVALID_OMFCLIENT_CLASS'
    codes[1599] = 'OMF_INVALID_EXIT_CODE_DESCRIPTOR'

  class Nova(object):
    ''' 
    Nova client class specific exit code table
    '''
    codes = dict.fromkeys(range(1600,1699), "undefined")
    codes[1600] = 'OMF_NOVA_FAILED_CLIENT_INIT'
    codes[1601] = 'OMF_NOVA_FAILED_HOST_LOOKUP' 
    codes[1602] = 'OMF_NOVA_FAILED_MAINTENCE_MODE'
    codes[1603] = 'OMF_NOVA_FAILED_FLAVORS_LIST'
    codes[1604] = 'OMF_NOVA_FAILED_SERVERS_LIST'
    codes[1605] = 'OMF_NOVA_FAILED_NETWORKS_LIST'
    codes[1606] = 'OMF_NOVA_FAILED_VOLUMES_LIST'
    codes[1607] = 'OMF_NOVA_FAILED_HYPERVISORS_LIST'
    codes[1608] = 'OMF_NOVA_FAILED_HYPERVISOR_SEARCH'
    codes[1609] = 'OMF_NOVA_FAILED_CREATE_INSTANCE'
    codes[1610] = 'OMF_NOVA_FAILED_ATTACHED_SERVER_VOLUME'
    codes[1611] = 'OMF_NOVA_FAILED_DELETE_SERVER'
    codes[1612] = 'OMF_NOVA_FAILED_CREATE_INSTANCE_INVALID_INPUT'
    codes[1613] = 'OMF_NOVA_FAILED_SERVER_MAP_HUMAN_TO_ID'
    codes[1614] = 'OMF_NOVA_FAILED_MISSING_HOSTNAME'
    codes[1615] = 'OMF_NOVA_FAILED_IMAGES_LIST'
    codes[1616] = 'OMF_NOVA_FAILED_DUPLICATE_SERVER_NAME'
    codes[1617] = 'OMF_NOVA_FAILED_IMAGE_DELETE'
    codes[1618] = 'OMF_NOVA_FAILED_LOAD_NATIVE_CLIENT_MODULE'
    codes[1619] = 'OMF_NOVA_FAILED_GET_ATTRIBUTE'

  class Cinder(object):
    ''' 
    Cinder client class specific exit code table
    '''
    codes = dict.fromkeys(range(1700,1799), "undefined")
    codes[1700] = 'OMF_CINDER_FAILED_CLIENT_INIT'
    codes[1701] = 'OMF_CINDER_FAILED_VOLUME_CHECK'
    codes[1702] = 'OMF_CINDER_FAILED_CREATE_VOLUME'
    codes[1703] = 'OMF_CINDER_FAILED_INVALID_VOLUME_PROPERTIES'
    codes[1704] = 'OMF_CINDER_FAILED_QUOTAS_GET'
    codes[1705] = 'OMF_CINDER_FAILED_VOLUMES_LIST'
    codes[1706] = 'OMF_CINDER_FAILED_VOLUME_CREATE'
    codes[1707] = 'OMF_CINDER_FAILED_VOLUME_CREATE_DUPLICATE_NAME'
    codes[1708] = 'OMF_CINDER_FAILED_VOLUME_MISSING_INFORMATION'
    codes[1709] = 'OMF_CINDER_FAILED_LOAD_NATIVE_CLIENT_MODULE'

  class Glance(object):
    ''' 
    Glance client class specific exit code table
    '''
    codes = dict.fromkeys(range(1800,1899), "undefined")
    codes[1800] = 'OMF_GLANCE_FAILED_CLIENT_INIT'
    codes[1801] = 'OMF_GLANCE_DUPLICATE_IMAGE_NAME'
    codes[1802] = 'OMF_GLANCE_FAILED_CREATE_MISSING_DATA'
    codes[1803] = 'OMF_GLANCE_FAILED_CREATE_IMAGE'
    codes[1804] = 'OMF_GLANCE_FAILED_UPDATE_IMAGE'
    codes[1805] = 'OMF_GLANCE_FAILED_CREATE_MISSING_NAME'
    codes[1806] = 'OMF_GLANCE_FAILED_IMAGES_LIST'
    codes[1807] = 'OMF_GLANCE_FAILED_COMMUNICATION_ERROR'
    codes[1808] = 'OMF_GLANCE_FAILED_LOAD_NATIVE_CLIENT_MODULE'

  class Heat(object):
    ''' 
    Heat client class specific exit code table
    '''
    codes = dict.fromkeys(range(1900,1999), "undefined")
    codes[1900] = 'OMF_HEAT_FAILED_CLIENT_INIT'
    codes[1901] = 'OMF_HEAT_FAILED_STACKS_LIST'
    codes[1902] = 'OMF_HEAT_FAILED_CREATE_STACK'
    codes[1903] = 'OMF_HEAT_MISSING_PARAMS'
    codes[1904] = 'OMF_HEAT_FAILED_VERIFY_NEW_STACK'
    codes[1905] = 'OMF_HEAT_FAILED_DELETE_STACK'
    codes[1906] = 'OMF_HEAT_FAILED_LOAD_NATIVE_CLIENT_MODULE'

  class Neutron(object):
    ''' 
    Neutron client class specific exit code table
    '''
    codes = dict.fromkeys(range(2000,2099), "undefined")
    codes[2000] = 'OMF_NEUTRON_FAILED_CLIENT_INIT'
    codes[2001] = 'OMF_NEUTRON_FAILED_TO_REACH_FLOATING_IP'
    codes[2002] = 'OMF_NEUTRON_FAILED_NETWORKS_LIST'
    codes[2003] = 'OMF_NEUTRON_FAILED_FLOATINGIP_LIST'
    codes[2004] = 'OMF_NEUTRON_FAILED_CREATE_FLOATINGIP'
    codes[2005] = 'OMF_NEUTRON_FAILED_DELETE_FLOATINGIP'
    codes[2006] = 'OMF_NEUTRON_FAILED_PORTS_LIST'
    codes[2007] = 'OMF_NEUTRON_NO_PORTS'
    codes[2008] = 'OMF_NEUTRON_FAILED_LOAD_NATIVE_CLIENT_MODULE'

  class Ceilometer(object):
    ''' 
    Ceilometer client class specific exit code table
    '''
    codes = dict.fromkeys(range(2100,2199), "undefined")
    codes[2100] = 'OMF_CEILOMETER_FAILED_CLIENT_INIT'
    codes[2101] = 'OMF_CEILOMETER_FAILED_METERS_LIST'
    codes[2102] = 'OMF_CEILOMETER_FAILED_NEW_SAMPLES_LIST'
    codes[2103] = 'OMF_CEILOMETER_FAILED_LOAD_NATIVE_CLIENT_MODULE'

  class Keystone(object):
    ''' 
    Keystone client class speific exit code table
    '''
    codes = dict.fromkeys(range(2200,2299), "undefined")
    codes[2200] = 'OMF_KEYSTONE_FAILED_CLIENT_INIT'
    codes[2201] = 'OMF_KEYSTONE_FAILED_USERS_LIST'
    codes[2202] = 'OMF_KEYSTONE_FAILED_LOAD_NATIVE_CLIENT_MODULE'

  _codes = Omf.codes.copy()
  _codes.update(Nova.codes)
  _codes.update(Cinder.codes)
  _codes.update(Glance.codes)
  _codes.update(Heat.codes)
  _codes.update(Neutron.codes)
  _codes.update(Ceilometer.codes)
  _codes.update(Keystone.codes)

  codes = _codes

  def _get(self, _type=None, code=None):

    if (_type):  
      if not code:
        return sys.modules[_type].codes 
      if str(code).isdigit():
        return sys.modules[_type].codes[code]
      else:
        return sys.modules[_type].codes.keys()[sys.modules[_type].codes.values().index(code)]
    else:
      if not code:
        return self.codes 
      if str(code).isdigit():
        try:
          return self.codes[code]
        except KeyError as e:
          print 'ERROR code not found {0}'.format(code)
          return self.codes[1500]
      else:
        try:
          return self.codes.keys()[self.codes.values().index(code)]
        except KeyError as e:
          print 'ERROR code not found {0}'.format(code)
          return self.codes[1500]

  def _get_defined(self, _type=None, code=None):

    ''' _type is not implemented yet. might not need it since you can lookup codes filtered on class '''
    if (_type):  
      if not code:
        c = {}
        for k,v in sys.modules[_type].codes.items():
          if v != "undefined":
            c[k] = v
        return c

      if str(code).isdigit():
        try:
          return sys.modules[_type].codes[code]
        except KeyError as e:
          print 'ERROR code not found {0}'.format(code)
          return self.codes[1500]
      else:
        try:
          return sys.modules[_type].codes.keys()[sys.modules[_type].codes.values().index(code)]
        except KeyError as e:
          print 'ERROR code not found {0}'.format(code)
          return self.codes[1500]
    else:
      if not code:
        c = {}
        for k,v in self.codes.items():
          if v != "undefined":
            c[k] = v
        return c 

      if str(code).isdigit():
        try:
          return self.codes[code]
        except KeyError as e:
          print 'ERROR code not found {0}'.format(code) 
          return self.codes[1500] 
      else:
        try:
          return self.codes.keys()[self.codes.values().index(code)]
        except KeyError as e:
          print 'ERROR code not found {0}'.format(code)
          return self.codes[1500]

  def get(self, code=None):
    '''
    Get Dictionary of all exit codes for all clients

    INPUT:

      * INT | STRING code - code can be either the INT error code or STRING descriptor. The reverse will be returned

    RETURN:

      * DICT codes - dictionary of exit codes and descriptors
    '''
    return self._get(code=code)

  def get_defined(self, code=None):
    '''
    Get Dictionary of all exit codes for all clients that are NOT undefined

    INPUT:

      * INT | STRING code - code can be either the INT error code or STRING descriptor. The reverse will be returned

    RETURN:

      * DICT codes - dictionary of exit codes and descriptors that are not undefined  
    '''
    return self._get_defined(code=code)

  
