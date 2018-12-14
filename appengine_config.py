# -*- coding: utf-8 -*-
from google.appengine.ext import vendor
import os
import sys

vendor.add('lib')

'''
os.environ.get('SERVER_SOFTWARE')

In the development web server, this value is "Development/X.Y"
where "X.Y" is the version of the runtime.
When running on App Engine, this value is "Google App Engine/X.Y.Z".
'''

on_appengine = os.environ.get('SERVER_SOFTWARE', '').startswith('Development')
if on_appengine and os.name == 'nt':
    sys.platform = "Not Windows"
