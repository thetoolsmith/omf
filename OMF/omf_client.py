'''
Maintainer: ADAPT

Author: Paul Bruno

OMF OpenStack Client session class. 

Pass an Instance of this class to the OMF child client classes.

Provides:

  - initialization of Openstack Native client objects

  - Pass thru to all native open methods

  - custom common methods, objects, variable and types

'''

import os, sys, traceback, inspect
from sets import Set 
from datetime import datetime, timedelta
import time
import omfbase as omfbase
import subprocess
from collections import defaultdict
from collections import namedtuple
from omfcodes import ExitCodes

ec = ExitCodes()

class OMFClient (object): 

  def __init__ (self, osenv=None, host=None, user=None, password=None, project=None, **kwargs):

    ''' 
    This uses default connection values if nothing is passed in. 
    However, these can also be overridden in the specific client classes that this instance is passed into.

    Required parameters:

      none
 
    Optional parameters:
   
      STRING osenv - openstack environment credentials to use. Must be configured as class in omfbase.py.

      STRING host - openstack host connection url.

      STRING user - valid openstack username for the openstack environment.

      STRING password - valid openstack username password for the openstack environment.

      STRING project - valid openstack tenant

      **kwargs - additional parameters
    
    '''

    self.creds = None
    '''credentials dictionary'''

    self.host = None
    '''openstack host authentication url'''

    self.user = None
    '''openstack authenticated user'''
 
    self.password = None
    '''openstack user name password'''

    self.project = None
    '''openstack tenant'''

    def _exit(_client, code, shortcode):
      print '\nFailed to load OMF {0}\n'.format(_client)
      for e in inspect.trace():
        print e[1], e[2], e[3], e[4]
      sys.stderr.write('\n{0} {1}\n'.format(code, ec.get(code)))      
      sys.exit(shortcode)

    if (osenv):
      if not osenv in omfbase.known_environments:
        print 'No matching known openstack environment found for {0}'.format(os_environment)
        sys.stderr.write('{0} {1}\n'.format(1501, ec.get(1501)))      
        sys.exit(150)

      self.creds = omfbase.credentials(osenv)

    try:
      
      if not host: 
        self.host = host = self.creds.host
      else:
        self.host = host
      if not user:
        self.user = user = self.creds.user
      else:
        self.user = user
      if not password:
        self.password = password = self.creds.password
      else: 
        self.password = password
      if not project:
        self.project = project = self.creds.project
      else:
        self.project = project

      self.domain = self.creds.domain

      ret = omfbase.check_client_args(locals())

      omfbase._log("Verified args...!")

      if (ret):
        print('Required client parameters needed, {0} are missing'.format(ret))
        sys.stderr.write('{0} {1}\n'.format(1501, ec.get(1501)))      
        sys.exit(150)

      self.log = str(__name__)

      self.debug = False
      '''set debug level'''

      _theclient = None
      for k,v in kwargs.items():
        if 'req_client' in k:
          _theclient = v
        if 'debug' in k:
          self.debug = v

    except Exception as e:
      self.log_and_exit(e, 1501)


    ''' KEYSTONE IS USED ALMOST ALWAYS, SO CREATE IT ALWAYS '''

    try:
      from omf_keystone import KeystoneClient
      self.keystone_client = KeystoneClient(self, version=2)
    except Exception as e:
      if isinstance(e, omfbase.OMFImport): 
        _exit('KeystoneClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
      else:
        _exit('KeyStoneClient', 2200, 220)
     
    if self.debug:
      self.log_and_print_info('created client object {0}'.format(type(self.keystone_client)))

    try:
      from omf_nova import NovaClient
      self.nova_client = NovaClient(self)
    except Exception as e:
      if isinstance(e, omfbase.OMFImport): 
        _exit('NovaClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
      else:
        _exit('NovaClient', 1600, 160)

    if self.debug:
      self.log_and_print_info('created client object {0}'.format(type(self.nova_client)))

    if (_theclient):
      if 'cinder' in _theclient.lower():
        try:
          from omf_cinder import CinderClient
          self.cinder_client = CinderClient(self)
        except Exception as e:
          if isinstance(e, omfbase.OMFImport): 
            _exit('CinderClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
          else:
            _exit('CinderClient', 1700, 170)

        if self.debug:
          self.log_and_print_info('created client object {0}'.format(type(self.cinder_client)))
 
      if 'heat' in _theclient.lower():
        try:
          from omf_heat import HeatClient
          self.heat_client = HeatClient(self)
        except Exception as e:
          if isinstance(e, omfbase.OMFImport): 
            _exit('HeatClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
          else:
            _exit('HeatClient', 1900, 190)

        if self.debug:
          self.log_and_print_info('created client object {0}'.format(type(self.heat_client)))

      if 'glance' in _theclient.lower():
        try:
          from omf_glance import GlanceClient
          self.glance_client = GlanceClient(self)
        except Exception as e:
          if isinstance(e, omfbase.OMFImport): 
            _exit('GlanceClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
          else:
            _exit('GlanceClient', 1800, 180)

        if self.debug:
          self.log_and_print_info('created client object {0}'.format(type(self.glance_client)))

      if 'neutron' in _theclient.lower():    
        try: 
          from omf_neutron import NeutronClient
          self.neutron_client = NeutronClient(self)
        except Exception as e:
          if isinstance(e, omfbase.OMFImport): 
            _exit('NeutronClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
          else:
            _exit('NeutronClient', 2000, 200)

        if self.debug:
          self.log_and_print_info('created client object {0}'.format(type(self.neutron_client)))

      if 'ceilo' in _theclient.lower():
        try:
          from omf_ceilometer import CeiloClient
          self.ceilo_client = CeiloClient(self)
        except Exception as e:
          if isinstance(e, omfbase.OMFImport): 
            _exit('CeiloClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
          else:
            _exit('CeiloClient', 2100, 210)

        if self.debug:
          self.log_and_print_info('created client object {0}'.format(type(self.ceilo_client)))

    else:  
      try:
        from omf_cinder import CinderClient
        self.cinder_client = CinderClient(self)
      except Exception as e:
        if isinstance(e, omfbase.OMFImport): 
          _exit('CinderClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
        else:
          _exit('CinderClient', 1700, 170)

      try:
        from omf_heat import HeatClient
        self.heat_client = HeatClient(self)
      except Exception as e:
        if isinstance(e, omfbase.OMFImport): 
          _exit('HeatClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
        else:
          _exit('HeatClient', 1900, 190)

      try:
        from omf_glance import GlanceClient
        self.glance_client = GlanceClient(self)
      except Exception as e:
        if isinstance(e, omfbase.OMFImport): 
          _exit('GlanceClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
        else:
          _exit('GlanceClient', 1800, 180)

      try: 
        from omf_neutron import NeutronClient
        self.neutron_client = NeutronClient(self)
      except Exception as e:
        if isinstance(e, omfbase.OMFImport): 
          _exit('NeutronClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
        else:
          _exit('NeutronClient', 2000, 200)

      try:
        from omf_ceilometer import CeiloClient
        self.ceilo_client = CeiloClient(self)
      except Exception as e:
        if isinstance(e, omfbase.OMFImport): 
          _exit('CeiloClient', int(str(e)), int('{0}{1}{2}'.format(str(e)[0], str(e)[1], str(e)[3])))
        else:
          _exit('CeiloClient', 2100, 210)

  ''' CLASS OFFERINGS '''

  location = os.getcwd()
  logfile = '{0}/{1}'.format(location,'OMFClient.log')

  
  def log_and_exit(self, e, code):
    '''
    Log exception | message string and exit with code

    INPUTS:

      STRING | BaseException e - string of message or exception

      INT | STRING code - exit code. MUST BE ONE OF omfcodes.py something >= 1500 OR THE EQUIVALANT DESCRIPTOR

      LINUX HAS LIMIT ON EXIT CODES OF 255, SO WE USE A 4 DIGIT CODE TO MAP 
      A SPECIFIC ERROR DESCRIPTOR.

      EACH OMF SUPPORTED OPENSTACK MODULE (nova, cinder, glance etc...) HAS AN 
      ALLOCATED RANGE OF 100 CODES.

      ONE OF THOSE 4 DIGIT CODES WILL BE PASSED INTO THIS FUNCTION AND THE CODE TO 
      DESCRIPTOR MAPPING AND ANY RELEVANT TEXT WILL BE PUT TO STDOUT.

      HOWEVER WITH THE 255 LIMIT, AND 1-128 RESERVED, WE WILL GRAB THE FIRST 3 DIGITS OF 
      THE OMF CODE PASSED IN AND USE THAT FOR THE EXIT CODE.
      THE MORE DETAILED 4 DIGIT CODE WILL BE SENT TO STDERR FOR EVALUATE BY THE CALLING
      PROCESS.

      EXAMPLE: 
      THERE'S AN EXCEPTION IN THE INITIALIZATION OF THE OMF NOVA CLIENT CLASS.
      
      THE __init__ METHOD IN THE NovaClient CLASS WILL SEND THE EXCEPTION AND THE EXIT CODE
      OF 1600 (NOVA ERRORS HAVE A RANGE 1600 TO 1699) TO THIS FUNCTION.
      
      THIS METHOD WILL PROCESS WHATEVER IT NEEDS TO SEND TO STDOUT. IT WILL SEND THE 
      FULL 1600 TO STDERR, AND EXIT THE PROCESS WITH 160

      IF THE NOVA ERROR IS DUPLICATE SERVER NAMES, THE CODE IS 1616, SO 161 WILL BE THE 
      EXIT CODE AND 1616 WILL GO TO STDERR.
    
      WITH EACH OS MODULE HAVING IT'S DEDICATED CONSTANT CODE RANGE, YOU COULD ALSO MAKE USE 
      OF THE 3 DIGIT EXIT CODE IN THE CALLING PROCESS TO LEARN WHAT 'CATEGORY' OR MODULE THE 
      ERROR IS RELATED TO, AND GRAB STDERR TO GET THE MORE SPECIFIC ERROR CODE WITH DESCRIPTOR. 

      IF THE CODE PASSED IN IS NOT FOUND, WE DEFAULT TO EXIT WITH 1500 
      IF THE DESCRIPTOR PASSED IN IS NOT FOUND, WE DEFAULT TO EXIT WITH 1599 
     
    RETURNS: none

    '''

    frame = inspect.currentframe()
    fromframe = inspect.getouterframes(frame, 2)

    cf = fromframe[1]
    print 'ERROR in {0}\nline={1}\nin {2}()'.format(cf[1], cf[2],cf[3])

    if (isinstance(e, BaseException)):    
      print e.message
      print e.__doc__
    else:
      print e

    # IF THE CODE PASSED IN IS NOT FOUND, WE DEFAULT TO EXIT WITH 1500 
    # IF THE DESCRIPTOR PASSED IN IS NOT FOUND, WE DEFAULT TO EXIT WITH 1599 

    descriptor = ec.get(code) 
    if descriptor == 'OMF_INVALID_EXIT_CODE':
      code = 1501

    f = open('{0}'.format(self.logfile), 'a')

    exc_type, exc_value, exc_traceback = sys.exc_info()
    if (self.debug):
      traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 3, file = sys.stdout)
    else:
      traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 3, file = f)  

    sys.stderr.write('{0} {1}\n'.format(code, ec.get(code)))

    if str(code).isdigit():
      sys.exit(int(str(code)[0]+str(code)[1]+str(code)[2]))
    else:
      sys.exit(int(str(ec.get(code))[0]+str(ec.get(code))[1]+str(ec.get(code))[2]))


  def log_exception(self, e):
    '''
    Log exception

    INPUTS

      BaseException e - exception

    RETURNS: none
    '''
    print e.message
    print e.__doc__
    print 'Exception caught: {0}'.format(type(e))
    f = open('{0}'.format(self.logfile), 'a')
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if (self.debug):
      traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 3, file = sys.stdout)
    else:
      traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 3, file = f)  

  def init_client_meta(self, _class, auth_inputs):
    '''
    Evaluates authorization inputs and set to instance variable

    INPUT:
 
      DICT auth_input 

    RETURN:
     
      user, password, project
    ''' 
    
    if 'user' in auth_inputs:
      _user = auth_inputs['user']
    else:
      _user = _class.user

    if 'password' in auth_inputs:
      _password = auth_inputs['password']
    else:
      _password = _class.password

    if 'project' in auth_inputs:
      _project = auth_inputs['project']
    else:
      _project = _class.project

    return _user, _password, _project

  def is_reachable(self, host):
    '''
    Attempt ping on host

    INPUT:

      STRING host - can be machine name or ipaddr

    RETURN:

      BOOL True | False

    '''
    output = []
    machinetype = None
    test = subprocess.Popen('echo $MACHTYPE', shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    machinetype, err = test.communicate()

    try:
      if 'apple' in machinetype.lower():
        mycmd = subprocess.Popen('ping -c 3 -W 5 {0}'.format(host), shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE )
      else:
        mycmd = subprocess.Popen('ping -c3 -w5 {0}'.format(host), shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE )

    except Exception as e:
      self.log_and_print_error(e)
      return False

    output, errout = mycmd.communicate()
    retcode = mycmd.returncode

    if self.debug:
      print 'errors:', errout
      print 'return:', retcode
      print 'output:', output
      
    if (output):
      self._log('ping stdout: {0}'.format(output))
    if (errout):
      self._log('ping stderr: {0}'.format(errout))
    if (retcode):  #failed
      return False

    return True

  def log_and_print_info(self, text=None):
    '''
    Log tagged INFO: information message to OMFClient.log and print to stdout

    INPUT:

      STRING text

    RETURN: none
    '''
    self._print(text)
    self._log(text, 'INFO')

  def log_and_print_warn(self, text=None):
    '''
    Log tagged WARN: warning message to OMFClient.log and print to stdout

    INPUT:

      STRING text

    RETURN: none
    '''
    self._print(text)
    self._log(text, 'WARN')

  def log_and_print_error(self, text=None):
    '''
    Log tagged ERROR: error message to OMFClient.log and print to stdout

    INPUT:

      STRING text

    RETURN: none
    '''
    self._print(text)
    self._log(text, 'ERROR')

  def _print (self, text=None):

    print '{0}'.format(str(text))

  def log_error (self, data=None):
    '''
    Log tagged ERROR: error message to OMFClient.log 

    INPUT:

      STRING text

    RETURN: none
    '''
    with open(self.logfile, 'a') as f:
      _log = '{0} ERROR: {1}\n'.format(str(datetime.now()), str(data))
      f.write(_log)

  def log_warn (self, data=None):
    '''
    Log tagged WARN: warning message to OMFClient.log 

    INPUT:

      STRING text

    RETURN: none
    '''
    with open(self.logfile, 'a') as f:
      _log = '{0} WARN: {1}\n'.format(str(datetime.now()), str(data))
      f.write(_log)

  def log_info (self, data=None):
    '''
    Log tagged INFO: information message to OMFClient.log 

    INPUT:

      STRING text

    RETURN: none
    '''
    with open(self.logfile, 'a') as f:
      _log = '{0} INFO: {1}\n'.format(str(datetime.now()), str(data))
      f.write(_log)

  def _log (self, data=None, state='info'):

    with open(self.logfile, 'a') as f:
      _log = '{0} {1}: {2}\n'.format(str(datetime.now()), state.upper(), str(data))
      f.write(_log)


