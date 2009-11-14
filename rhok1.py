#
#  rhok1.py

__author__ = 'matthewf@google.com (Matt Frantz)'

import datetime
import logging

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import webapp_util


MAX_FAMILY_MEMBERS = 20


class Plan(db.Model):
  out_of_town_contact = db.TextProperty()
  neighborhood_meeting_place = db.TextProperty()
  regional_meeting_place = db.TextProperty()
  evacuation_location = db.TextProperty()
  last_updated = db.DateTimeProperty()
  family_members = db.ListProperty(users.User)


def FetchPlanUnsafe():
  """Fetches the plan for this user, creating one if necessary.

  Called inside a transaction from FetchPlan.
    
  Returns
    Plan object, possibly new.
  """
  user = users.get_current_user()
  plan = Plan.gql('WHERE family_members = :1', user).get()
  if not plan:
    plan = Plan()
    plan.family_members.append(user)
    plan.put()
  return plan


def FetchPlan():
  """Fetches the plan for this user, creating one if necessary.
    
  Returns
    Plan object, possibly new.
  """
  db.run_in_transaction(FetchPlanUnsafe)


def SavePlanUnsafe(request, family_members):
  """Saves the family plan.
  
  This runs in a transaction in SavePlan.

  Args:
    request: Web form request object (?)
    family_members: List of email addresses of family members (list of str)
    
  Returns:
    List of users that already have plans (list of users.User).
  """
  plan = FetchPlanUnsafe()
  # Check if there are other plans for those family members.
  already_has_a_plan = []
  for family_member in family_members:
    if HasADifferentPlan(family_member, plan.key()):
      already_has_a_plan.append(family_member)

  if already_has_a_plan:
    logging.error('Already has a plan: %s', users.get_current_user())
  else:
    plan.out_of_town_contact = request.get('out_of_town_contact')
    plan.neighborhood_meeting_place = request.get('neighborhood_meeting_place')
    plan.regional_meeting_place = request.get('regional_meeting_place')
    plan.evacuation_location = request.get('evacuation_location')
    plan.family_members = [users.User(x) for x in family_members]
    plan.last_updated = datetime.datetime.now()
    logging.debug('Save plan: %s', plan.out_of_town_contact)
    plan.put()

  return already_has_a_plan


def SavePlan(where_to_meet, family_members):
  """Saves the family plan.
  """
  return db.run_in_transaction(
      SavePlanUnsafe, request, family_members)


class SavePlanHandler(webapp.RequestHandler):
  def post(self):
    family_members = []
    for i in xrange(MAX_FAMILY_MEMBERS):
      family_member = self.request.get('family_member%d' % i)
      if family_member:
        family_members.append(family_member)
    
    already_has_a_plan = SavePlanUnsafe(self.request, family_members)
    
    if already_has_a_plan:
      webapp_util.WriteTemplate(self.response, 'already_has_a_plan.html', locals())
    else:
      self.redirect('/')


def HasADifferentPlan(family_member, plan_key):
  return bool(Plan.gql('WHERE __key__ != :1 AND family_members = :2', plan_key,
                       users.User(family_member)).get())


class MainPage(webapp.RequestHandler):
  def get(self):
    plan = FetchPlanUnsafe()
    # Build a list of family member email addresses, and pad with empties.
    family_members_emails = (
        [x.email() for x in plan.family_members] +
        ['' for x in xrange(MAX_FAMILY_MEMBERS - len(plan.family_members))])
    logout_url = users.create_logout_url('/')
    webapp_util.WriteTemplate(self.response, 'plan.html', locals())


class FetchPlanHandler(webapp.RequestHandler):
  def get(self):
    logging.info('Fetch plan for user %s', users.get_current_user().email())
    plan = FetchPlanUnsafe()
    webapp_util.WriteTemplate(self.response, 'plan.xml', locals())
    self.response.headers["Content-Type"] = "text/xml"


application = webapp.WSGIApplication([('/', MainPage),
                                      ('/plan.html', MainPage),
                                      ('/fetchplan', FetchPlanHandler),
                                      ('/saveplan', SavePlanHandler),
                                      ],
                                     debug=True)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
    main()
