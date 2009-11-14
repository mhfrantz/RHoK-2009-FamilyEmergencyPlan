#
#  rhok1.py

__author__ = 'matthewf@google.com (Matt Frantz)'

import datetime

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import webapp_util


MAX_FAMILY_MEMBERS = 20


class Plan(db.Model):
  where_to_meet = db.TextProperty()
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


def SavePlanUnsafe(where_to_meet, family_members):
  """Saves the family plan.
  
  This runs in a transaction in SavePlan.

  Args:
    where_to_meet: Where to meet (str)
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

  if not already_has_a_plan:
    plan.where_to_meet = where_to_meet
    plan.family_members = [users.User(x) for x in family_members]
    plan.last_updated = datetime.datetime.now()
    plan.put()

  return already_has_a_plan


def SavePlan(where_to_meet, family_members):
  """Saves the family plan.
  """
  return db.run_in_transaction(
      SavePlanUnsafe, where_to_meet, family_members)


class SavePlanHandler(webapp.RequestHandler):
  def post(self):
    family_members = []
    for i in xrange(MAX_FAMILY_MEMBERS):
      family_member = self.request.get('family_member%d' % i)
      if family_member:
        family_members.append(family_member)
    
    where_to_meet = self.request.get('where_to_meet')
    already_has_a_plan = SavePlanUnsafe(where_to_meet, family_members)
    
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


application = webapp.WSGIApplication([('/', MainPage),
                                      ('/saveplan', SavePlanHandler),
                                      ],
                                     debug=True)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
    main()
