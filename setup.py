import os, sys
from setuptools import setup

# install: sudo easy_install dist/omf-1.0.0-py2.7.egg 
# build: python setup.py bdist_egg
# mac install tar.gz
# gunzip -c omf-1.0.0.tar.gz | tar xopf -

def get_files(src):

  dirs = src.split(',')

  files = []

  for d in dirs:
    for f in os.listdir(d):
      files.append('{0}/{1}'.format(d, f))

  return files

setup(name='omf',
      version='1.0.0',
      description='Openstack Management Framework',
      maintainer='ADAPT',
      author='Paul Bruno',
      author_email='paul@autoagentframework.com',
      py_modules=['omf_nova','omf_glance', 'omf_cinder', 'omf_neutron', 'omf_ceilometer', 'omf_heat', 'omf_keystone', 'omf_client', 'omfbase', 'omfcodes'],
      scripts=list(get_files('docs,templates,credentials')),
      url='http://stash.epnet.com/projects/OSP/repos/openstack-management-framework/browse/docs',
      packages=['OMF'],
        long_description="""Openstack Management Framework""",
        classifiers=[
          "Programming Language :: Python 2.7+",
        ],
      install_requires=['python-ceilometerclient>=0.4.6', \
                        'python-cinderclient>=1.4.0', \
                        'python-glanceclient>=0.19.0', \
                        'python-heatclient>=0.8.0', \
                        'python-keystoneclient>=1.8.1', \
                        'python-neutronclient>=3.1.0', \
                        'python-novaclient>=2.26.0', \
                        'python-swiftclient>=2.6.0'],
      )   
