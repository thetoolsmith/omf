'''
AUTHOR: PAUL BRUNO

command line utility to manage openstack using OMF

EXAMPLES:

  * omf-osmgr.py --help

  * omf-osmgr.py --osenv sandbox --checkhosts  (optionally add --filter hostname) (optionally add --evacuate) 

  * omf-osmgr.py --osenv sandbox --checkhostsapi  (optionally add --filter hostname) tests api of OS client only, no network check

  * omf-osmgr.py --osenv sandbox --checkclients  (no arg will check all. or pass nova|cinder|glance|heat|neutron|ceilometer|keystone)

  * omf-osmgr.py --osenv sandbox --checkvolumes  (optionally add --filter volumename)

  * omf-osmgr.py --osenv sandbox --checkmetrics  (optionally add --filter name=servername,metric=metricname or either) (optional --limitresults xx)

  * omf-osmgr.py --osenv sandbox --listmetrics  (optionally add --filter name=servername,metric=metricname or either) (optional --limiteresults xx)

  * omf-osmgr.py --osenv sandbox --createvolume "name=fub,size=4,description=testing_vol_create"

  * omf-osmgr.py --osenv sandbox --createvolume config=volcfg.json

  * omf-osmgr.py --osenv sandbox --createserver interactive

  * omf-osmgr.py --osenv sandbox --createserver name=svr1,image=91d02448-d439-40ec-9ea0-466ef9bfe770,flavor=3,network=newnet

  * omf-osmgr.py --osenv sandbox --test attachvolume

  * omf-osmgr.py --osenv sandbox --test createserver (optionally pass in --filter servername)

  * omf-osmgr.py --osenv sandbox --test createvolume

  * omf-osmgr.py --osenv sandbox --test createstack

  * omf-osmgr.py --osenv sandbox --test createimage

  * omf-osmgr.py --osenv sandbox --test addip 

  * omf-osmgr.py --osenv sandbox --show volumefull

  * omf-osmgr.py --osenv sandbox --show volumes

  * omf-osmgr.py --osenv sandbox --show images

  * omf-osmgr.py --osenv sandbox --show imagesfull

  * omf-osmgr.py --osenv sandbox --show stacks

  * omf-osmgr.py --osenv sandbox --show networks


EXAMPLE VOLUME JSON INPUT:

volcfg.json sample:
{ 
  'name': 'foo', 
  'size': 4, 
  'metadata': 
  {
    'foo': 'val1xxxxxx', 
    'bar': 'val2yyyy'
  } 
}

'''

import os, sys, time
import subprocess
import traceback
from collections import defaultdict
from collections import namedtuple
from datetime import datetime, timedelta
import ast
import random
import omfbase #utility class
from omfcodes import ExitCodes
import utils
import urllib

try:
  ec = ExitCodes()
except:
  raise ImportError('Failed to load omfcodes instance of ExitCodes')

nova_session = None
cinder_session = None
keystone_client = None
heat_client = None

__evacuating_node = None

try:
    from omf_client import OMFClient
except Exception:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 3, file = sys.stdout)
    raise RuntimeError("Failed to load OMFClient")

global os_client

os_client = None

def __ceiloclient():

  session = os_client.ceilo_client

  if (_args['debug']):
    print 'opened session type:', type(session.client)

  return session

def __heatclient():

  session = os_client.heat_client

  if (_args['debug']):
    print 'opened session type:', type(session.client)

  return session

def __neutronclient():

  session = os_client.neutron_client

  if (_args['debug']):
    print 'opened session type:', type(session.client)

  return session

def __keystoneclient():

  session = os_client.keystone_client

  if (_args['debug']):
    print 'opened session type:', type(session.client)

  return session

def __glanceclient():

  session = os_client.glance_client

  if (_args['debug']):
    print 'opened session type:', type(session.client)

  return session

def __novaclient():
 
  session = os_client.nova_client

  if (_args['debug']):
    print 'opened session type:', type(session)

  return session

def __cinderclient():

  session = os_client.cinder_client

  if (_args['debug']):
    print 'opened session type:', type(session.client)

  return session


def powerdown_node(node=None):
  '''
  Power down the host before executing OS evacuate

  INPUT:
  
    STRING node - machine name

  RETURN:

    * BOOL True | False
  '''

  os_client.log_and_print_info('power down not implemented yet, just return True')

  return True


def _evacuate(instance):

  if (debug):
    os_client.log_and_print_info('Evacuating {0}'.format(instance))

  try:
    nova_session.client.servers.evacuate(instance, host=None, on_shared_storage=True, password=None)
  except Exception as e:
    os_client.log_exception(e)
    return True

  return False


def evacuate_host(host_instances=None):
  '''
  Calls native openstack host evacuate methods

  INPUT:

    * LIST host instances

  RETURN:

    INT failed count 

  '''  
  if (not host_instances):
    return 0

  failed = []

  # FIRST CALL METHOD TO POWER DOWN THE MACHINE BEFORE EVACUATION ROUTINE

  for i in host_instances:
    __evacuating_node = i['uuid']

    # FIRST CALL CISCO UCS AND POWER DOWN THE MACHINE BEFORE EVACUATION ROUTINE
    if (powerdown_node(i['name'])):
      failed.append(str(i['name']))
      continue

    runningtime, obj = omfbase.trace(_evacuate, i['uuid'])

    if (debug):
      os_client.log_and_print_info('Evacuate {0}:{1} took: {2}'.format(i['name'],i['uuid'], runningtime)) 
    else:
      os_client.log_info('Evacuate {0}:{1} took: {2}'.format(i['name'],i['uuid'], runningtime))

    if (obj):
      failed.append(str(i['name']))
    
      if (debug):
        os_client.log_and_print_error('Failed to evacuate {0}:{1}'.format(i['name'],i['uuid']))

  if (len(failed) > 0):
    if (debug):
      os_client.log_and_print_error('Total host failed to evacuate: {0} \n{1}'.format(len(failed), failed))
    return len(failed)
  else:
    return 0


'''
RETURNS argparse.ArgumentParser() object 
ADDS utility specific args in the object
'''
#TODO: need to implement nargs= to some of the arguments to allow multi values.
#      for instance volumecfg

def fill_args():

  _p = omfbase.common_args()

  _p.add_argument(
    '--checkclients',
    metavar='CLIENT',
    choices=['all', 'nova', 'cinder', 'keystone', 'heat', 'glance', 'neutron', 'ceilo'],
    help="Create instance of supported OS clients and make an api call. Can be all or specific client.",
    default=None)

  _p.add_argument(
    '--checkhosts',
    help="Check compute nodes for network and OS api access",
    action='store_true')

  _p.add_argument(
    '--checkhostsapi',
    help="Check compute nodes for OS api access (no network verify)",
    action='store_true')

  _p.add_argument(
    '--checkvolumes',
    help="Check Volumes status (take action on result).",
    action='store_true')

  _p.add_argument(
    '--checkmetrics',
    help="Check metrics using ceilometer with optional filters. Use --filter name=svrname,metric=valid.metric",
    action='store_true')

  _p.add_argument(
    '--listmetrics',
    help="List navtive OS  metrics using ceilometer.",
    action='store_true')

  _p.add_argument(
    '--test',
    metavar='CHECK_API_FUNCTION',
    choices=['attachvolume', 'createvolume', 'createserver', 'createstack', 'createimage', 'addip'], 
    help="Excercises one or more openstack apis",
    default=None)

  _p.add_argument(
    '--show',
    metavar='OBJECT',
    choices=['hosts', 'hostsfull', 'flavors', 'networks', 'images', 'imagesfull', 'quotas', 'stacks', 'volumes', 'volumefull'],
    help="Show and object. Can use --filter to filter on single host|volume). Use to learn inputs for --createserver.",
    default=None)

  _p.add_argument(
    '--volumecfg',
    help="Specify external volume config file to use when creating New Volumes.",
    default=None)

  _help = "Create new volume with cinder.\nThis can be done using a config file (json block)" \
          " or passing in the required/optional parameters in a string for parsing.\n" \
          "Example of pure command line:\n\t--createvolume \"name=foo,size=3,description=testing\"\n" \
          "Example using external config file:\n\t --createvolume \"config=config_file\"\n\n" \
          "Sample entries in config_file:\n{\n  \'name\': \'foo\',\n  \'size\': 4,\n  " \
          "\'metadata\':\n  {\n    \'foo\': \'val1xxxxxx\',\n    \'bar\': \'val2yyyy\'\n  }\n}\n\n" \
          "IMPORTANT: If you need to pass metadata, you MUST use the config file method.\nReference" \
          " to all available inputs for volume config: http://developer.openstack.org/api-ref-blockstorage-v2.html#createVolume"


  _p.add_argument(
    '--mountvolume',
    help='Mount volume to a server instance.',
    action='store_true')
         
  _p.add_argument(
    '--createvolume',
    help=_help,
    metavar="VOLUME_CONFIG",
    default=None)

  _p.add_argument(
    '--createserver',
    help='Create new server instance. Example: --createserver name=svr1,image=91d02448-d439-40ec-9ea0-466ef9bfe770,flavor=3,network=newnet',
    metavar="SERVER PARAMS",
    default=None)

  _p.add_argument(
    '--evacuate',
    help="Will enable auto-evacuation when using --checkhosts and result is False | False for network and api access",
    action='store_true')

  _p.add_argument(
    '--failsafe',
    help='Maximum number of hosts allowed to be evacuated. If more are detected, script will abort. default={0}'.format(default_failsafe),
    default=default_failsafe)

  _p.add_argument(
    '--filter',
    help='Filter on name or status of host|server|volume etc.... eval depends on option called.',
    default=None)

  _p.add_argument(
    '--limitresults',
    help='Limit results set. Used with metric (ceilometer) calls.',
    default=3)

  return _p

def test_cinder():
  try:
    __cinderclient().client.volumes.list
    os_client.log_and_print_info("cinderclient=PASS")
  except Exception as e:
    if debug:
      os_client.log_exception(e)

    os_client.log_and_exit('cinderclient=FAILED', 1705)

def test_glance():
  try:
    __glanceclient().client.images.list
    os_client.log_and_print_info("glanceclient=PASS")
  except Exception as e:
    if debug:
      os_client.log_exception(e)

    os_client.log_and_exit('glanceclient=FAILED', 1806)

def test_keystone():
  try:
    __keystoneclient().client.users.list
    os_client.log_and_print_info("keystoneclient=PASS")
  except Exception as e:
    if debug:
      os_client.log_exception(e)

    os_client.log_and_exit('keystoneclient=FAILED', 2201)

def test_nova():
  try:
    __novaclient().client.flavors.list
    os_client.log_and_print_info("novaclient=PASS")
  except Exception as e:
    if debug:
      os_client.log_exception(e)

    os_client.log_and_exit('novaclient=FAILED', 1603)

def test_heat():
  try:
    __heatclient().client.stacks.list
    os_client.log_and_print_info("heatclient=PASS")
  except Exception as e:
    if debug:
      os_client.log_exception(e)

    os_client.log_and_exit('heatclient=FAILED', 1901)

def test_neutron():
  _stderr = sys.stderr
  f = open('trash','w')
  sys.stderr = f
  try:
    #bug in python module, prints warning messag
    __neutronclient().client.list_networks()
    os_client.log_and_print_info("neutronclient=PASS")
  except Exception as e:
    sys.stderr = _stderr
    f.close
    if debug:
      os_client.log_exception(e)

    os_client.log_and_exit('neutronclient=FAILED', 2002)

  sys.stderr = _stderr
  f.close

def test_ceilo():
  try:
    __ceiloclient()
    os_client.log_and_print_info("ceiloclient=PASS")
  except Exception as e:
    if debug:
      os_client.log_exception(e)

    os_client.log_and_exit('ceiloclient=FAILED', 2100)


'------------------------- main entry ----------------------'

''' GLOBALS '''

failsafe = default_failsafe = 4 #should be 2

action_evacuate = False

debug = False

os_environment = 'sandbox'

_args = None

''' <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><> '''

if __name__ == '__main__':

  _args = vars(fill_args().parse_args())

  if (_args['osenv']):
    os_environment = _args['osenv'].lower()
    
    if not os_environment in omfbase.known_environments:
      raise ValueError('No matching known openstack environment found for {0}'.format(os_environment))

  else:
    if (not _args['user']) and (not _args['password']) and (not _args['host']) and (not _args['project']):
      raise NameError("if --osenv is not specified, you must use --user --password --host --project")
  
  if (_args['debug']):
    debug = True

  if (_args['failsafe']):
    failsafe = _args['failsafe']

  if (_args['evacuate']):
    action_evacuate = _args['evacuate']

  ''' OPEN BASE CLIENT CLASS. PROVIDES CREDIENTIAL INIT TO BE CONSUMED (OR OVERWRITTEN) BY CHILD CLIENT CLASSES AND OTHER BASE FUNCTIONS '''

  if _args['checkclients']: #not much overhead opening all clients, but the option to check just one is needed.

    if not _args['checkclients'] == 'all': 
      os_client = OMFClient(osenv=os_environment, req_client=_args['checkclients'], debug=_args['debug'])
    else:
      os_client = OMFClient(osenv=os_environment, debug=_args['debug'])

 
  def _setup_client(client=None):

    global os_client

    if not client:
      os_client = OMFClient(osenv=os_environment, debug=_args['debug'])
    else:
      os_client = OMFClient(osenv=os_environment, debug=_args['debug'], req_client=client)


  if (_args['checkmetrics'] and _args['listmetrics']):
    print 'Slow down cowboy! You can only list or check metric in one pass.'
    sys.stderr.write('1508')
    sys.exit(150)
 
  if (_args['checkmetrics'] or _args['listmetrics']):
    _setup_client() #need nova client as well, so create all clients, since we might not know what it needs
    ceilo_session = __ceiloclient()

    if _args['limitresults']:
      _limit = int(_args['limitresults'])

    _metric = None #default returns all, scoped to OS project
    _sname = None #default returns all, scoped to OS project

    if _args['filter']:
      if ('name=' in  _args['filter']):
        for a in _args['filter'].split(','):
          if 'name=' in a:
            _sname =  a.split('=')[1]
          if 'metric=' in a:
            _metric =  a.split('=')[1]
      if ('metric=' in  _args['filter']):
        for a in _args['filter'].split(','):
          if 'metric=' in a:
            _metric =  a.split('=')[1]
      
    ''' 
    NOTES:

    Just filtering on server name and a single metric will return all the recorded meters for that.
    This can be a very large amount of meters if the interval is frequent or has gone on for a long time.
    So we should always limit the results set.
    We can use ASC - ascending OR DESC - decending

    EXAMPLE USING THE EXTENTED DICTIONARY FIELDS

    query = [dict(field='meter', op='eq', value='memory.usage'), \
             dict(field='metadata.display_name', op='eq', value='web16', counter_volume='ASC')]

    '''
    query_base = {}
    query_ext = {}

    query_base['field'] = 'meter'
    query_base['op'] = 'eq'

    if (_metric):
      query_base['value'] = _metric

    if _sname:
      query_ext['field'] = 'metadata.display_name'
      query_ext['op'] = 'eq'
      query_ext['value'] = _sname
    query_base['counter_volume'] = 'ASC'

    query_list = []
    query_list.append(query_base)

    if query_ext:
      query_list.append(query_ext)

    # MAKE CALL TO GET METRIC DATA
    if _args['checkmetrics']:
      meters = None
      try:
        meters = ceilo_session.client.new_samples.list(q=query_list, limit=_limit)
      except Exception as e:
        os_client.log_and_exit(e, 2102)

      for m in meters:
        os_client.log_and_print_info('{0}\n'.format(m))
    
      sys.exit(0)

    if _args['listmetrics']: 
      meters = ceilo_session.get_metrics(namefilter=_sname, metric=_metric)
      for m in meters:
        os_client.log_and_print_info('{0}\n'.format(m))

      sys.exit(0)

  '''------------------------------------- CHECK HOST API -----------------------------------------'''
  if (_args['checkhostsapi']):
    '''
    THIS WILL NOT DO ANY EVACUATION OR OTHER ACTION
    SIMPLY CHECKS API STATUS OF ONE OR ALL HYERVISORS AND OUTPUTS RESULT
    '''
    _setup_client(client='nova')
    nova_session = __novaclient()

    all_available_hosts = nova_session.get_hypervisors()

    failedhosts = 0
    checkedhosts = 0 
    _hosts = {}
    for h in all_available_hosts:
      if (_args['filter']):
        if _args['filter'].lower() != h.hypervisor_hostname.lower():
          continue

      _hosts[h.hypervisor_hostname] = h.state
      checkedhosts+=1
      if h.state != 'up':
        failedhosts+=1

    failsafe = len(all_available_hosts) - 1

    # GET TOTAL FAILED HOSTS
    if (not failedhosts):
      os_client.log_and_print_info('All hosts ({0}) are responding to api calls.'.format(checkedhosts))
      if (debug):
        os_client.log_and_print_info(_hosts)
      sys.exit(0)
    else:
      os_client.log_and_print_info(_hosts) 

      if (failedhosts == len(all_available_hosts)):
        os_client.log_and_exit('CRITICAL: Catastrophic network or api failure, 0 hosts are available!', 1506)
      
      elif (failedhosts == failsafe):
        os_client.log_and_exit('CRITICAL: Only 1 hosts is available via OS api', 1507)

      else:
        os_client.log_and_exit('Failed hosts detected {0}'.format(failedhosts), 1507)


  '''--------------------------------- CHECK HOSTS API AND NETWORK ACCESS ---------------------------------------'''

  if (_args['checkhosts']):
    _setup_client(client='nova')
    nova_session = __novaclient()

    all_available_hosts = nova_session.get_hypervisors()

    compute_node_set = nova_session.get_hypervisors_info(namefilter=_args['filter'])

    failedhosts = 0

    bad_state_hosts = []
    action_msg = []
    action_msg.append("Evacuation action taken on: ")

    # GET TOTAL FAILED HOSTS
    for h in compute_node_set:
      if ((not h.network_up) and (not h.api_up) and (h.has_nodes)):
        failedhosts+=1

    if (failedhosts > failsafe):
      os_client.log_and_print('CRITICAL: More than {0} hosts need evacuation, beyond the capacity'.format(str(failsafe)), 1507)

    if (failedhosts == len(all_available_hosts)):
      os_client.log_and_print('Catastrophic network or api failure, take no action and abort.', 1506)

    failed_evac_host_ctr = 0

    for h in compute_node_set:
      #if (True): #for testing
      if ((not h.network_up) and (not h.api_up) and (h.has_nodes)):
        # EVAC CANDIDATES
        if (action_evacuate):
          action_msg.append(h.hostname)

          if (h.servers): #we set .servers in ComputeNodes type to empty dict.
                          #because when the Openstack host has no server, the .server attribute doesn't exist
                          #and thus we would need try catch around every enum of the host object when servers are evaluated 
            failed_evac_host_ctr+= (int(evacuate_host(nova_session.hv_search(hvhost=h.hostname, sflag=True).servers)))
          else:
            print 'Skip {0} as it has no server instances'.format(h.hostname)

      elif ((not h.network_up) or (not h.api_up) and (h.has_nodes)):
        bad_state_hosts.append('{0}:{1}:{2}'.format(h.hostname,h.network_up,h.api_up))

    if (not failedhosts): #no failedhosts, but we have bad state hosts.

      if len(bad_state_hosts) > 0:
        print "Hosts in bad state. I.E. one of network access or api access is failed.\n\nHOST:NETWORK:API\n"

        for b in bad_state_hosts:
          print '{0}\n'.format(b)

        sys.stderr.write('1502')
        sys.exit(150)

      elif failed_evac_host_ctr > 0:
        print '\nSummary:\n{0} failed evacuations. Refer to trace log for details. {1}'.format(failed_evac_host_ctr, os_client.logfile)
        sys.stderr.write('1503')
        sys.exit(150)
      else:
        print "\nSummary:\nAll systems are up and responding, no action needed."
        sys.exit(0)

    else:
      print '{0} failed hosts. Refer to trace log for details: {1}'.format(failedhosts, os_client.logfile)
      print action_msg
      sys.stderr.write('1502')
      sys.exit(150)

  '''------------------------------------- CHECK CLIENTS -----------------------------------------'''
  if _args['checkclients']:
    if (_args['checkclients'] == 'all'):
      test_cinder()
      test_nova()
      test_keystone()
      test_glance()
      test_heat()
      test_neutron()
      test_ceilo()
    elif 'cinder' in _args['checkclients'].lower():
      test_cinder()
    elif 'nova' in _args['checkclients'].lower():
      test_nova()
    elif 'heat' in _args['checkclients'].lower():
      test_heat()
    elif 'glance' in _args['checkclients'].lower():
      test_glance()
    elif 'neutron' in _args['checkclients'].lower():
      test_neutron()
    elif 'keystone' in _args['checkclients'].lower():
      test_keystone()
    elif 'ceilo' in _args['checkclients'].lower():
      test_ceilo()
    else:
      os_client.log_and_print_info('Unknown client asked for {0}'.format(_args['checkclients']))

  '''------------------------------------- CHECK VOLUME/S -----------------------------------------'''
  if (_args['checkvolumes']):
    _setup_client(client='cinder')
    cinder_session = __cinderclient()

    _vol = cinder_session.get_volumes_info(namefilter=_args['filter'])

    _failed = {}

    if (_vol):
      if (debug): 
        os_client.log_and_print_info('\n{0} Volumes found:\n'.format(len(_vol)))

      for v in _vol:

        if (debug):
          os_client.log_and_print_info('{0}\n'.format(v))

        if v.status != 'available':
          _failed[v.name] = '{0} :: {1}'.format(v.id,v.status)

      if len(_failed) == len(_vol):
        os_client.log_and_print_error('*** {0} of {1} Volumes are not available'.format(len(_failed), len(_vol)))
        os_client.log_and_print_warn('*** Take Action to create Volumes.')
        sys.stderr.write('1509')
        sys.exit(150)
      else:
        os_client.log_and_print_info('All volumes are in available status')
        sys.exit(0)
    else:
      os_client.log_and_print_info("No volumes to check.")
      sys.exit(0)


  if (_args['mountvolume']):
    _setup_client()
    nova_session = __novaclient() 
    nova_session.create_instance()
   
    print "not implemented yet...."

 
  '''------------------------------------------- SHOW ---------------------------------------------------'''
  if (_args['show']):

    _setup_client('nova')

    def _process_nova_show(obj):
      if type(obj) != 'dict':
        d = {}
        for o in obj:
          d[o.human_id] = o.id
        omfbase.print_pretty_dict(d)
      else:
        for o in obj:
          os_client.log_and_print_info('name={0} id={1}'.format(o.human_id,o.id))

      sys.exit(0)

    def _process_cinder_show(obj):
      for o in obj:
        os_client.log_and_print_info('name={0} id={1}'.format(o.name,o.id))
      sys.exit(0)

    nova_session = __novaclient()

    if (_args['show'] == 'networksfull'):

      _setup_client(client='neutron')

      neutron_session = __neutronclient()
      os_client.log_and_print_info('\nAvailable Networks (using neutron):')
      for net in neutron_session.get_networks():
        print '\n'
        omfbase.print_pretty_dict(net)

    if (_args['show'] == 'stacks'):
     
      #TODO: need to add filter on name
      _setup_client(client='heat')

      heat_session = __heatclient()

      count, stacks_obj, stacks_list  = heat_session.get_stacks()
       
      # THIS IS JUST SHOWING THE OPTIONAL WAYS TO ENUM EACH RETURNED OBJECT
      if (count):
        os_client.log_and_print_info('\nAvailable Stacks:')
        print '\nEnumerating the generator object....'
        try:
          print stacks_obj.next()
        except StopIteration as e:
          None

        print '\nEnumerating the list....'
        for s in stacks_list:
          print s
      else:
        os_client.log_and_print_info('\nNo Stacks found\n')

    if (_args['show'] == 'images'):
      os_client.log_and_print_info('\nAvailable Images:')
      try:
        _process_nova_show(nova_session.client.images.list())
      except Exception as e:
        os_client.log_and_exit(e, 1615)

    if (_args['show'] == 'imagesfull'):

      _setup_client(client='glance')

      os_client.log_and_print_info('\nAvailable Images:')

      glance_session = __glanceclient()
      
      images = None

      try:
        images = glance_session.client.images.list()
      except Exception as e:
        os_client.log_and_exit(e, 1806)

      for image in images:
        print '\n'
        omfbase.print_pretty_dict(image)

    if (_args['show'] == 'flavors'):
      os_client.log_and_print_info('\nAvailable Flavors:')
      omfbase.print_pretty_columns(nova_session.get_flavors(), ['name','human_id','id','ram'])

      #for f in nova_session.get_flavors():
      #  os_client.log_and_print_info('{0}\t{1}\t{2}'.format(f.name,f.human_id,f.id))
      #_process_nova_show(nova_session.get_flavors())

    if (_args['show'] == 'servers'):
      os_client.log_and_print_info('\nAvailable servers:')

      try:
        _process_nova_show(nova_session.client.servers.list())
      except Exception as e:
        os_client.log_and_exit(e, 1604)

    if (_args['show'] == 'networks'):
      os_client.log_and_print_info('\nAvailable Networks:')
      try:
        _process_nova_show(nova_session.client.networks.list())
      except Exception as e:
        os_client.log_and_exit(e, 1605)

    if (_args['show'] == 'hosts'):
      all_available_hosts = nova_session.get_hypervisors()
      for h in  all_available_hosts:
        os_client.log_and_print_info('\n{0}\n{1}\nstatus={2}\nstate={3}\nFreedisk={4}\nFreeMem={5}'.format(h.hypervisor_hostname, \
                                                                         h.host_ip, h.status, h.state, h.free_disk_gb, h.free_ram_mb))
      sys.exit(0)

    if (_args['show'] == 'hostsfull'):
      all_available_hosts = nova_session.get_hypervisors()
      compute_node_set = nova_session.get_hypervisors_info(namefilter=_args['filter'])
      for h in  compute_node_set:
         os_client.log_and_print_info('\n{0}'.format(h))
      sys.exit(0)

    if (_args['show'] == 'volumes'):

      _setup_client(client='cinder')

      cinder_session = __cinderclient()

      os_client.log_and_print_info('\nAll Volumes:')

      _process_cinder_show(cinder_session.client.volumes.list())

    if (_args['show'] == 'volumefull'):

      _setup_client(client='cinder')

      cinder_session = __cinderclient()

      os_client.log_and_print_info('\nAvailable Volumes:')

      _vol = cinder_session.get_volumes_info(namefilter=_args['filter'])
   
      if (_vol):
        os_client.log_and_print_info('\n{0} Volumes found:\n'.format(len(_vol)))

        for v in _vol:
          os_client.log_and_print_info('{0}\n'.format(v))

      sys.exit(0)

    if (_args['show'] == 'quotas'):

      _setup_client(client='cinder')

      cinder_session = __cinderclient()

      _q = cinder_session.get_quotas()
      if (_q):
        os_client.log_and_print_info('Backups: {0}\nBackup GB: {1}\nGB: {2}\nGB Std: {3}'.format(_q.backups, \
                                                                                                     _q.backup_gigabytes, \
                                                                                                     _q.gigabytes, \
                                                                                                     _q.gigabytes_Standard))
        os_client.log_and_print_info('Snapshots: {0}\nSnapshots Std: {1}\nVolumes: {2}\nVolumes Std: {3}'.format(_q.snapshots, \
                                                                                                     _q.snapshots_Standard, \
                                                                                                     _q.volumes, \
                                                                                                     _q.volumes_Standard))
        sys.exit(0)
      else:
        os_client.log_and_exit('Failed Cinder client get_quotas', 1704)


  if (_args['createserver']):

    _setup_client(client='nova')

    nova_session = __novaclient()

    '''------------------------------ CREATE SERVER *INTERACTIVE* -----------------------------------------'''
    if (_args['createserver'] == 'interactive'):

      cfg = {}
      cfg['name'] = raw_input("Enter new server name: ").strip()

      images = None
      flavors = None
      network = None

      try:
        images = nova_session.client.images.list()
      except Exception as e:
        os_client.log_and_exit(e, 1615)

      try:
        flavors = nova_session.client.flavors.list()
      except Exception as e:
        os_client.log_and_exit(e, 1603)

      try:
        networks = nova_session.client.networks.list()
      except Exception as e:
        os_client.log_and_exit(e, 1605)

      def _form(obj):
        ret = []
        ctr = 1
        for i in obj:
          ret.append('{0}. {1} {2}'.format(ctr,i.human_id,i.id))
          ctr+=1
        return ret

      i = raw_input('Pick Image:\n{0}\n'.format(str(_form(images))))
      print 'You picked {0}'.format(images[int(i) - 1].human_id) 
      cfg['image'] = images[int(i) - 1].human_id

      i = raw_input('Pick Flavor:\n{0}\n'.format(str(_form(flavors))))
      print 'You picked {0}'.format(flavors[int(i) - 1].human_id) 
      cfg['flavor'] = flavors[int(i) - 1].human_id

      i = raw_input('Pick Network:\n{0}\n'.format(str(_form(networks))))
      print 'You picked {0}'.format(networks[int(i) - 1].human_id) 
      cfg['network'] = networks[int(i) - 1].human_id

      if nova_session.create_instance(cfg):
        os_client.log_and_exit('Failed to create instance', 1609)

      sys.exit(0)    

    '''------------------------------------- CREATE SERVER -----------------------------------------'''
    if (_args['createserver'] != 'interactive'):

      cfg = {i.split("=")[0] : i.split("=")[1] for i in _args['createserver'].split(',')}

      s = nova_session.create_instance(cfg)
 
      if (not s):
        os_client.log_and_exit('Failed to create instance', 1609)
       
      sys.exit(0)

  '''------------------------------------- TEST CREATE IMAGE -----------------------------------------'''
  if (_args['test'] == 'createimage'):
    _setup_client('glance') # need nova, glance at minimum, so create all
    glance_session = __glanceclient()
    nova_session = __novaclient()

    _name = 'IMG_{0}'.format(str(random.getrandbits(16))) if not _args['filter'] else _args['filter']

    newimage = glance_session.create_image(name = _name, url=glance_session.test_image)

    omfbase.print_pretty_dict({'name': newimage.human_id, 'id': newimage.id, 'status':  newimage.status})

    os_client.log_and_print_info('Deleteing image {0}'.format(newimage.name))

    try:
      nova_session.client.images.delete(newimage.id)
    except Exception as e:
      os_client.log_and_exit(e, 1617)

    sys.exit(0)


  '''------------------------------------- TEST FLOATING IP -----------------------------------------'''
  if (_args['test'] == 'addip'):

    ''' 
    THIS OPTION WILL EXERCISE THE FOLLOWING OPENSTACK API:
    neutron: create, verify, delete, asscociate floating ip
    nova: create server instance, delete
    '''
    #TODO: would like to dynamically create and teardown a private network as well to avoid having a static known one in every env
   
    _setup_client()

    nova_session = __novaclient()
    neutron_session = __neutronclient()

    _fip_net_id = None

    _stderr = sys.stderr
    f = open('trash','w')
    sys.stderr = f

    try:
      _fip_net_id = neutron_session.client.list_floatingips().items()[0][1][0]['floating_network_id']
    except Exception as e:
      sys.stderr = _stderr
      f.close
      os_client.log_and_exit(e, 2003)

    sys.stderr = _stderr
    f.close
    sys.stderr.flush()

    def _teardown(s=None, ip=None, exit=0):
      # s - server
      # n - network 
      # exit - exit code
      os_client.log_and_print_info('Tearing down new server and ip {0} {1}'.format(s.name, ip['floating_ip_address']))

      _stderr = sys.stderr
      f = open('trash','w')
      sys.stderr = f

      try:
        neutron_session.client.delete_floatingip(ip['id'])
      except Exception as e:
        sys.stderr = _stderr
        f.close
        os_client.log_and_exit(e, 2005)

      sys.stderr = _stderr
      f.close

      s.delete()
      sys.exit(exit)

    cfg = {}
    #cfg['network'] = neutron_session.client.list_networks().items()[0][1][0]['name'] #get first network in networks
    cfg['network'] = 'newnet'
    cfg['image'] = 'centos7'
    cfg['flavor'] = 'm1medium'
    cfg['name'] = 'SVR_{0}'.format(str(random.getrandbits(24)))

    s = nova_session.create_instance(cfg)

    if (not s): 
      os_client.log_and_exit('Failed to create instance', 1609)

    #this next line shows how we could use get_host_instances() to get a server if from a namefilter lookup 
    #sid = nova_session.get_host_instances()[0].id

    # note: need to use the instance id for a server that is on the private network and lookup ports
    # there must already be an external network with a route between the private network and external
    # this is the only way to associate a floating ip
    # the port_id must be passed in when creating to associate with instance

    ports = None

    _stderr = sys.stderr
    f = open('trash','w')
    sys.stderr = f

    try:
      ports = neutron_session.client.list_ports(device_id=s.id)
    except Exception as e:
      sys.stderr = _stderr
      f.close
      os_client.log_and_exit(e, 2006)

    sys.stderr = _stderr
    f.close

    if not ports:
      os_client.log_and_exit('No ports found', 2007)

    _port_id = ports.items()[0][1][0]['id']

    fips_meta = {'floatingip': {'floating_network_id': _fip_net_id, 'port_id': _port_id}}

    new_fips = neutron_session.client.create_floatingip(fips_meta)
    new_fips_id = new_fips.items()[0][1]['id']
    new_floating_ip = new_fips.items()[0][1]['floating_ip_address']
    new_fixed_ip = new_fips.items()[0][1]['fixed_ip_address']

    if (new_fips_id):
      os_client.log_and_print_info('Created new ip {0}'.format(new_fixed_ip)) 

      floatingips = None

      _stderr = sys.stderr
      f = open('trash','w')
      sys.stderr = f

      try:
        floatingips = neutron_session.client.list_floatingips().items()
      except Exception as e:
        sys.stderr = _stderr
        f.close
        os_client.log_and_exit(e, 2003)

      sys.stderr = _stderr
      f.close

      if not floatingips:
        os_client.log_and_exit('Failed to list floating ips', 2003)

      for k,v in floatingips: 
        for x in v:

          if x['id'] == new_fips_id:

            os_client.log_and_print_info('Verified new id {0}'.format(x['id'])) 

            # try to ping the new floating ip
            ctr = neutron_session.new_floating_ip_wait
            up = False
            
            while ((not up) and (ctr != 0)):
              os_client.log_and_print_info('pinging {0}'.format(new_floating_ip))
              up = os_client.is_reachable(host=new_floating_ip)

              time.sleep(neutron_session.pause)
              ctr-=1
              
            if (not up):
              os_client.log_and_print_error('Failed to reach new ip {0}\nDeleting new instance and ip.'.format(x['fixed_ip_address']))
              _teardown(s,x,2001)
            else:
              os_client.log_and_print_error('Success validation new floating ip association')
              _teardown(s,x,0) 

            os_client.log_and_print_info('Deleted new ip {0} {1}'.format(x['fixed_ip_address'], x['id']))

    else:
      os_client.log_and_exit('Failed to create new floating ip', 2005)      

    sys.exit(0)


  '''------------------------------------- TEST CREATE STACK -----------------------------------------'''
  if (_args['test'] == 'createstack'):

    _setup_client(client='heat')
    heat_session = __heatclient()

    with open('../templates/test_stack_create') as f:
      data = f.read()
      f.close()

    _stack = None
    _name = None 

    if _args['filter']:
      _name = _args['filter']
    else:
      _name = 'omf-test-stack-create'

    _stack = heat_session.create_stack(name=_name, stack=data)

    if (_stack):
      if (debug):
        os_client.log_and_print_info('Successfully created stack')

      # TEAR IT DOWN 
      s = {}
      s['stack_id'] = _stack.items()[0][1]['id']   
      try:
        x = heat_session.client.stacks.delete(**s)
      except Exception as e:
        os_client.log_and_exit(e, 1905)

      os_client.log_and_print_info('Success')

    else:
      os_client.log_and_exit('Failed to create new stack.', 1902)


  '''------------------------------------- TEST CREATE INSTANCE -----------------------------------------'''
  if (_args['test'] == 'createserver'):

    '''
    ''' 
    _setup_client()

    nova_session = __novaclient()

    
    try:
      f = open('../templates/test_server_create')
    except Exception as e:
      os_client.log_and_exit(e, 1609)

    cfg = {i.split("=")[0] : i.split("=")[1].strip() for i in f.readlines()}

    s = nova_session.create_instance(cfg, True)

    if (not s):
      os_client.log_and_exit('Failed to create instance', 1609)

    try:
      s.delete()
    except Exception as e:
      os_client.log_and_exit(e, 1611)
    
    os_client.log_and_print_info('Sucessfully removed server instance.')
   

  '''------------------------------------- TEST CREATE VOLUME -----------------------------------------'''
  if (_args['test'] == 'createvolume'):

    _setup_client(client='cinder')

    cinder_session = __cinderclient()

    volconfig = None

    try: 
      with open('../templates/test_volume_create', 'r') as f:
        j = f.read()
        volconfig = ast.literal_eval(j)     
    except Exception as e:
      os_client.log_and_exit('Failed to open volume config', 1702) 


    if not isinstance(volconfig, dict):
      os_client.log_and_exit('Invalid volume properties\n{0}'.format(volconfig), 1703) 

    v = cinder_session.create_volume(volconfig, force=True)

    if (not v): 
      os_client.log_and_exit('Failed to create volume {0}'.format(volconfig['name']), 1702)

    os_client.log_and_print_info('Created new volume {0} id: {1}'.format(volconfig['name'], v)) 

    os_client.log_and_print_info('Deleteing new volume')
    try:
      d = v.delete()
    except Exception as e:
      os_client.log_and_exit(e, 1702)

    sys.exit(0)

  '''------------------------------------- TEST ATTACH VOLUME -----------------------------------------'''
  if (_args['test'] == 'attachvolume'):

    ''' 
    THIS OPTION WILL EXERCISE THE FOLLOWING OPENSTACK API:
      - server, image, flavor, network list lookups, create, delete
      - volume lookup, create, attach
    '''
    _setup_client()

    nova_session = __novaclient()
    cinder_session = __cinderclient()

    cfg = {}
    cfg['network'] = 'newnet'
    cfg['image'] = 'centos7'
    cfg['flavor'] = 'm1medium'
    cfg['name'] = 'SVR_{0}'.format(str(random.getrandbits(24)))

    s = nova_session.create_instance(cfg)

    if (not s):
      os_client.log_and_exit('Failed to create instance', 1609)

    v = cinder_session.get_available_volumes()[0]  #just get the 1st for test

    if (nova_session.attach_server_volume(server=s, volume_id=v.id, device='/dev/foo')):  #use default device /dev/foo
      try:
        s.delete()
      except Exception as e:
        os_client.log_and_exit(e, 1610)

    os_client.log_and_print_info('Cleanup, delete new instance {0}, no wait.'.format(s.name))
   
    try:
      s.delete()
    except Exception as e:
      os_client.log_and_exit(e, 1611)

  '''------------------------------------- CREATE VOLUME -----------------------------------------'''
  if (_args['createvolume']):

    _setup_client(client='cinder')

    cinder_session = __cinderclient()

    volconfig = None

    if ('config=' in _args['createvolume']):
      cfg = _args['createvolume'].split("=")[1]
      try:
        with open(cfg, 'r') as f:
          j = f.read()
          volconfig = ast.literal_eval(j)
            
      except Exception as e:
        os_client.log_and_exit('Failed to open volume config {0}'.format(cfg), 1702)
    else:
      volconfig = {i.split("=")[0] : i.split("=")[1] for i in _args['createvolume'].split(',')}

    if not isinstance(volconfig, dict):
      os_client.log_and_exit('Invalid volume properties\n{0}'.format(volconfig), 1703)

    _v = cinder_session.create_volume(volconfig)

    if (not _v):
      os_client.log_and_exit('Failed to create volume {0}'.format(volconfig['name']), 1702)

    os_client.log_and_print_info('Created new volume {0} id: {1}'.format(volconfig['name'], _v))
    sys.exit(0)

  '''---------------------------------------------------------------------------------------------'''





