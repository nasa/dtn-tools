from setuptools import setup, find_packages 

# Package metadata 
name = 'dtngen'
version = '0.0.5'
description = 'Generates and interpretes DTN bundles'

# Package dependencies 
dependencies = [ 
	'cbor2>=5.6.2', 
	'crccheck>=1.3.0'
] 

# Package setup 
setup( 
	name=name, 
	version=version, 
	description=description, 
	packages=find_packages(), 
	install_requires=dependencies 
) 
