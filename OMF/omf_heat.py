'''
Author: Paul Bruno

Description:

  - Encapsulates native openstack heat client

  - Adds additional support for Operatonal API testing and Managment

'''

import os, sys, traceback, inspect
from sets import Set
import omfbase as omfbase
import time
from datetime import datetime, timedelta
from collections import defaultdict
from collections import namedtuple
import random

from omfcodes import ExitCodes
ec = ExitCodes()

class HeatClient (object):

  def __init__ (self, _class, **kwargs):
    ''' 
    Initialize HeatClient instance

    INPUTS:
   
      * OMFClient class - instance of OMFClient

      * DICT - pointer to keyword argument list

    RETURN:

      * HeatClient instance
 
    '''

    if (not _class) or (not isinstance(_class, omfbase.OMFCLIENT_CLASS)):
      sys.stderr.write('{0} {1}\n'.format(1511, ec.get(1511)))
      sys.exit(151)
     
    self.parent = _class
    ''' set parent to instance of OMFClient '''

    self._name_filter = None
    ''' generic name filter '''

    self._status_filter = None
    ''' status filter '''

    self.stackname = None
    ''' placeholder for new stack name '''

    self.wait_time = 2
    ''' default sleep time while waiting '''

    self.debug = self.parent.debug
    ''' set debug level from parent '''

    try:
      from heatclient.client import Client
      import heatclient
    except:
      raise omfbase.OMFImport(1906)

    self.heatclient = heatclient 
    '''set passthru to native openstack heat api for methods not in Client()'''
    try:

      _user, _password, _project = _class.init_client_meta(_class, kwargs)

      self.project = _project

      ksc = _class.keystone_client.client
      heat_endpoint = ksc.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')

      self.client = Client('1', heat_endpoint, token=ksc.auth_token)  

      if not isinstance(self.client, heatclient.v1.client.Client):
        _class.log_and_exit('Initialize Heat client failed', 1900)

      _class.log_info('Created new {0}: {1}'.format(__name__, type(self.client)))

    except Exception as e:
      self.parent.log_and_exit(e, 1900)

  ''' private methods '''

  def _stacks(self):

    obj = []
    slist = None
    stack_count = 0
    stacks = None
    _stacks = None

    import itertools

    try:
      slist = list(self.client.stacks.list())
      _stacks, stacks  = itertools.tee(self.client.stacks.list())
    except Exception as e:
      self.parent.log_and_exit(e, 1901)

    try:
      while True and (_stacks):
        self.parent.log_info('{0}'.format(_stacks.next()))
        stack_count+=1
    except StopIteration as e:
      if (self.debug):
        self.parent.log_and_print_info('iterating stacks, found {0}'.format(stack_count))
      else:
        self.parent.log_info('iterating stacks, found {0}'.format(stack_count))

    if (self._name_filter):
      for s in slist:
        if (s.stack_name == self._name_filter):
          obj.append(s)
    else:
      obj = slist

    return stack_count, stacks, obj 

  def _create_stack(self):

    slist = None

    mystack = {}
    mystack['tenant_id'] = self.project
    mystack['stack_name'] = self.stackname
    mystack['template'] = self.stackdata

    try:
      stack = self.client.stacks.create(**mystack)
    except Exception as e:
      self.parent.log_and_exit(e, 1902)

    return stack 


  ''' public methods '''
  def about_stacks():
    '''
    Random notes about _stacks() non-publish method

    THIS METHOD RETURNS BOTH THE NATIVE HEAT STACKS GENERATOR OBJ AS WELL
    AS A LIST ALONG WITH COUNT OF TOTAL STACKS

    RETURNS int COUNT, GENERATOR stacks, LIST stacks

    IF namefilter IS SET TO NOT NONE, THE LIST stacks RETURNED VALUE
    WILL HAVE THE FILTERED RESULT. THE GENERATOR OBJECT RETURNED IS NOT FILTERED.
    SOME EXPLANATION IS NEEDED HERE.

    THE CALLS TO stacks.list() RETURNS A PYTHON GENERATOR OBJECT WHICH IS AN INTERATOR
    THIS CAN ONLY BE ITERATED USING THE .next() METHOD
    IN THIS METHOD SINCE WE ARE RETURNING COUNT, GENERATOR AND LIST, WE NEED TO WALK
    THE GENERATOR TO GET COUNT.
    HOWEVER, GENERATORS CAN ONLY BE WALKED ONCE, SO IF WE ITERATE OVERIT, WHEN WE RETURN TO THE 
    CALLING FUNCTION, THE GENERATOR OBJECT IS NOT ITERABLE ANYMORE. IT RAISE StopIteration ON THE 
    FIRST CALL TO .next().
    SO WE USE itertools.tee() TO CREATE TWO IDENTICAL GENERATOR OBJECTS, ITERATE OVER ONE TO 
    GET THE COUNT, THEN RETURN THE OTHER GENERATOR OBJECT
    
    NOTE: 

    WHEN SETTING A NEW VARIABLE TO THE GENERATOR OBJECT, CREATES A REFERENCE, NOT AN EXACT COPY.
    SO itertools.tee() IS NEEDED.
    WE COULD JUST WALK THE LIST TO GET COUNT BY CASTING list(generator_object), BUT CASTING
    IS NOT ALWAYS THE BEST WAY TO GO.

    '''    
    return


  def get_stacks(self, namefilter=None):
    '''
    Basic lookup of stacks

    INPUTS:

      * STRING namefilter - OPTIONAL. stack name to lookup

    RETURN:

      INT count, LIST stacks, GENERATOR stacks
    ''' 
    if(namefilter):
      self._name_filter = namefilter

    count, stacks, obj = self._stacks()

    return count, stacks, obj

  def create_stack(self, name=None, stack=None):
    '''
    Create new stack wih Heat client

    INPUT:

      * STRING name - REQUIRED user specified name of stack to create

      * STRING stack - REQUIRED HOT template formatted string of stack data
    
    RETURN:

      * True - success (already verified so no need to do that in the caller)

      * False - failed to create stack
    '''
    newstack = None

    # COULD ADD CHECK FOR DUPLICATE STACK NAME, HOWEVER UNLIKE MANY OTHER OPENSTACK
    # COMPONENTS, THE HEAT STACK CREATE NATIVE WILL RETURN A MESSAGE 'STACK ALERADY EXISTS, SO NOT 
    # SURE WE NEED TO ADD THIS.
  

    if ((not name) or (not stack)):
      self.parent.log_and_exit('name and stack are required for {0}'.format(inspect.getframeinfo(inspect.currentframe())[2]), 1903)

    self.stackname = name 
    self.stackdata = stack

    runningtime, newstack = omfbase.trace(self._create_stack)
    self.parent.log_and_print_info('Create Stack took: {0}'.format(runningtime))

    # WAIT FOR READINESS
    waiting = True
    _start = datetime.now()

    self._name_filter = self.stackname

    sys.stdout.write('Waiting for STACK {0} to be ready'.format(self._name_filter))

    while (waiting):
      waiting = False
      try:
        count, stack_gen, stack_list = self._stacks()
        if (count): #at least 1 stack
          if (not stack_list[0].stack_status.upper() == 'CREATE_COMPLETE'):
            waiting = True
            sys.stdout.write('. ')
            sys.stdout.flush()
            time.sleep(self.wait_time)
          else:
            self.parent.log_and_print_info('New STACK {0} is ready.'.format(stack_list[0].stack_name))
            self.parent.log_and_print_info('Verify STACK took: {0}'.format(datetime.now() - _start))
      except Exception as e:
        self.parent.log_and_exit(e, 1904)    

    return newstack


