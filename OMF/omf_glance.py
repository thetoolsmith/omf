'''
Author: Paul Bruno

Description:

  - Encapsulates native openstack Glance client

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
import urllib

from omfcodes import ExitCodes
ec = ExitCodes()
 
class GlanceClient (object):

  def __init__ (self, _class, **kwargs):

    ''' 
    Initialize GlanceClient instance

    INPUTS:
   
      OMFClient class - instance of OMFClient

      DICT - pointer to keyword argument list

    RETURN:

      GlanceClient instance
 
    '''
    if (not _class) or (not isinstance(_class, omfbase.OMFCLIENT_CLASS)):
      sys.stderr.write('{0} {1}\n'.format(1511, ec.get(1511)))
      sys.exit(151)

    self.parent = _class 
    ''' set parent to instance of OMFClient '''

    self._name_filter = None
    ''' generic namefilter '''

    self._status_filter = None
    ''' generic status filter '''

    self.debug = self.parent.debug
    ''' set debug level to parent level '''

    try:
      from glanceclient import Client
      import glanceclient
      import keystoneclient
    except:
      raise omfbase.OMFImport(1808)

    self.glanceclient = glanceclient 
    '''set passthru to native openstack glance client for other methods not in Client()'''
   
    try:

      _user, _password, _project = _class.init_client_meta(_class, kwargs)

      ks = _class.keystone_client.client
      glance_endpoint = ks.service_catalog.url_for(service_type='image',
                                                   endpoint_type='publicURL')

      # TODO: v2 glance client doesn't work to create image and get it to Active. It stays queued.

      glance = Client('1', endpoint=glance_endpoint, token=ks.auth_token)

      self.client = glance

      if not isinstance(glance, glanceclient.v1.client.Client):
        _class.log_and_exit('Initialize Glance client failed', 1800)

      if not isinstance(ks, keystoneclient.v2_0.client.Client ):
        _class.log_and_exit('Required Keystone client v2 invalid', 1800) 

    except Exception as e:
      self._class.log_and_exit(e, 1800)


    self.test_image = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img'
    '''default image for testing api'''

    self.image_name = None 
    ''' new image name placeholder '''

    self.image_data = None

    self.image_wait = 1 
    ''' default wait time when creating image '''

    self.disk_format = 'qcow2' 
    ''' default disk format '''

    self.container_format = 'bare' 
    '''default container format '''

    self.force_active = True 
    '''force waiting for active status'''

    self.properties = None 
    '''DICTIONARY, could set to {}'''


  ''' private methods '''
  def _find_image(self, name=None):

    if not name:
      return True

    result = False

    try: 
      if self.debug:
        self.parent.log_and_print_info('Getting images list for iteration')

      i = self.client.images.list()
      while True:
        newimage = i.next()
        if newimage.name.lower() == name:
          result = True
          self.parent.log_and_exit('Duplicate Image name already exists, try again!', 1801)
    except Exception as e:

      if isinstance(e, self.glanceclient.exc.CommunicationError):
        self.parent.log_and_exit('Failed communication error\n{0}'.format(e), 1807)

      elif isinstance(e, StopIteration):
        self.parent.log_and_print_info('End of iteration')
  
      else:
        self.log_and_exit(e, 1806) 
  
    return result


  def _create_image(self):

    obj = None
    newimage = None
    done = False

    if self.debug:
      self.parent.log_and_print_info('Attempting to create image {0}'.format(self.image_name))

    try:
      image = self.client.images.create(name=self.image_name, \
                                      disk_format=self.disk_format, \
                                      container_format=self.container_format)
    except Exception as e:
      self.parent.log_and_exit(e, 1803)

    try:
      image.update(data=self.image_data)   
    except Exception as e:
      self.parent.log_and_exit(e, 1804)

    if self.properties:
      try:
        image.update(properties=self.properties)
      except Exception as e:
        self.parent.log_and_exit(e, 1804)

    if self.force_active:
      # NEED TO VERIFY THE STATUS. WE GET A GENERATOR OBJECT, FILTER ON NAME, SHOULD BE ONLY 1 RETURNED
      done = False
      newimage = None
      try: 
        while not done:
          self.parent.log_and_print_info('\nverifying newimage status...')
          i = self.client.images.list(name=self.image_name)
          newimage = i.next()
          if newimage.status.lower() == 'active':
            self.parent.log_and_print_info('Done verify image...')
            done = True 

      except StopIteration:
        if isinstance(e, StopIteration):
          self.parent.log_and_print_info('End of iteration')
        else:
          self.log_and_exit(e, 1806) 

    return image   #this is not really used since we are threading in the create_instance() method that calls this
                   #however, it may be used if called from another caller not threading


  ''' public methods '''
  def get_images(self, namefilter=None):
    '''
    Basic image lookup (not implemented)
    '''
    None

  def create_image(self, name=None, url=None, \
                   file=None, data=None, force_active=True, \
                   properties=None, diskformat='qcow2', containerformat='bare'):

    '''
    Create an Openstack Image 

    NOTE: threading is used when creating the image

    INPUTS:

      * STRING name - name of image to create REQUIRED

      * STRING url - url to image file (optional)

      * STRING file - local image file (optional)

      * STRING data - raw binary image data (optional)

      * STRING diskformat - STRING valid openstack disk format, default qcow2 (optional)

      * STRING containerformat - valid openstack container format, default bare (optional)

      * DICT properties - key=value pairs of custom properties (optional)

      * NOTE: one of url, file or data is required

    RETURN:

      * Instance of Image Object 
    '''  

    if not name:
      self.parent.log_and_exit('Missing name of Image to create', 1805)
    else:
      self.image_name = name

    if (self._find_image(name=name)):
      self.parent.log_and_exit('Duplicate Image name already exists, try again!', 1801) 

    _data = None

    if not data:
      if (url):
        try:
          remote_file = urllib.urlopen(url)
        except Exception as e:
          self.parent.log_and_print_error('Failed to open url {0}'.format(url))

        _data = remote_file.read()
      if (file):
        _data = open(file,'rb')
    else:
      _data = data
  
    if not _data:
      self.parent.log_and_exit('Missing data, url, or file needed for image create', 1802)
    else:
      self.image_data = _data

    if properties:
      self.properties = properties

    if not force_active:
      self.force_active = False

    from multiprocessing import Process

    p = Process(target=self._create_image) 

    waiting = True
    _start = datetime.now()
    sys.stdout.write('Waiting for image to be ready\n')

    newimage = None
  
    p.start()

    while (waiting):
      waiting = False

      theimages = None

      try:
        theimages = self.parent.nova_client.client.images.list()
      except Exception as e:
        self.parent.log_and_exit(e, 1615)

      if (theimages):
        for i in theimages:
          if i.human_id.lower() == name.lower() and i.status.lower() == 'active':
            self.parent.log_and_print_info('New Image {0} is ready.'.format(i.human_id))
            self.parent.log_and_print_info('Create New Image took: {0}'.format(datetime.now() - _start))
            newimage = i
            break
          else:
            waiting = True
        sys.stdout.write('. ')
        sys.stdout.flush()
        time.sleep(1)
      else:
        self.log_and_exit('Failed to images.list()', 1615)

    sys.stdout.write('\n')

    return newimage


