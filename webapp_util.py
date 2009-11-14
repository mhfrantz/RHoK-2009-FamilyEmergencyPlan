#!/usr/bin/python2.4
#
# Copyright 2009 Google Inc. All Rights Reserved.

"""Utilities for dealing with the webapp framework."""

__author__ = 'matthewf@google.com (Matt Frantz)'

import os

from google.appengine.api import users
from google.appengine.ext.webapp import template


def WriteTemplate(response, template_file, params):
  """Writes a response from a Django template.

  Args:
    response: webapp.Response object
    template_file: Path of a Django template, relative to this file (string)
    params: Dict of parameter name (string) to value (object)
  """
  path = os.path.join(os.path.dirname(__file__), template_file)
  params.update({'current_user': users.get_current_user()})
  html = template.render(path, params)
  response.out.write(html)
