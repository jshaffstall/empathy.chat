import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from . import invites
from . import server_misc as sm
from . import accounts
from . import parameters as p
from . import invite_gateway as ig


@anvil.server.callable
@anvil.tables.in_transaction
def serve_invite_unauth(port_invite, method, kwargs):
  from . import matcher
  matcher.propagate_update_needed()
  return _serve_invite(port_invite, method, kwargs, auth=False)


@sm.authenticated_callable
@anvil.tables.in_transaction
def serve_invite(port_invite, method, kwargs):
  from . import matcher
  matcher.propagate_update_needed()
  return _serve_invite(port_invite, method, kwargs, auth=True)


def _serve_invite(port_invite, method, kwargs, auth):
  print(f"invites_server: {method}({kwargs}) called on {port_invite}")
  invite = Invite(port_invite)
  errors = invite.relay(method, kwargs, auth=auth)
  return invite.portable(), errors


def phone_match(last4, user):
  return last4 == user['phone'][-4:]


class Invite(invites.Invite):
  no_auth_methods = ['visit', 'register', 'respond']
  
  def __init__(self, port_invite):
    self.update(port_invite)
    self._convert_port_user('inviter')
    self._convert_port_user('invitee')

  def _convert_port_user(self, port_user_attr_name):
    port_user_attr = getattr(self, port_user_attr_name)
    if port_user_attr:
      setattr(self, port_user_attr_name, port_user_attr.s_user)
 
  def portable(self):
    port = invites.Invite()
    port.update(self)
    port.inviter = sm.get_port_user(self.inviter)
    port.invitee = sm.get_port_user(self.invitee)
    return port

  def relay(self, method, kwargs=None, auth=True):
    if not kwargs:
      kwargs = {}
    if (method in self.no_auth_methods) or auth:
      return getattr(self, method)(**kwargs)
    else:
      return ["Not authorized."]
  
  def add(self, user_id=""):
    """Side effect: Add invites row"""
    user = sm.get_acting_user(user_id)
    self.inviter = user
    errors = self.invalid_invite()
    if self.invitee:
      if not self.invitee['phone']:
        errors.append(f"{sm.name(self.invitee)} does not have a confirmed phone number.")
      elif not phone_match(self.inviter_guess, self.invitee):
        errors.append(f"The digits you entered do not match {sm.name(self.invitee)}'s confirmed phone number.")
    else:
      user['last_invite'] = sm.now()
    if not errors:
      self.link_key = "" if self.invitee else sm.random_code(num_chars=7)
      errors = ig.add_invite(self)
    return errors

  def edit_invite(self):
    errors = self.invalid_invite()
    if not errors:
      errors = ig.update_invite(self)
    return errors
    
  def cancel(self, invite_row=None):
    if not invite_row:
      invite_row, errors = ig._invite_row(self)
    else:
      errors = []
    if invite_row:
      if self.invitee:
        from . import connections as c
        c.try_removing_from_invite_proposal(invite_row, self.invitee)
      invite_row['current'] = False
    else:
      errors.append(f"Invites row not found with id {self.invite_id}")
    self.cancel_response() # Not finding a response_row is not an error here
    self._clear()
    return errors

  def cancel_response(self):
    from . import connections as c
    invite_row, _ = ig._invite_row(self)
    if invite_row and self.invitee:
      c.try_removing_from_invite_proposal(invite_row, self.invitee)
    response_row, errors = ig._response_row(self)
    if response_row:
      response_row['current'] = False
    else:
      errors.append(f"Response row not found")
    self._clear()
    return errors
  
  def _clear(self):
    for key, value in vars(self).items():
      if key in ['inviter', 'invitee']:
        self[key] = None
      else:
        self[key] = ""

  def _old_invite_row(self):
    return app_tables.invites.get(origin=True, link_key=self.link_key, current=False)
  
  def visit(self, user, register=False):
    """Assumes only self.link_key known (unless register)
    
       Side effects: set invite['user2'] if visitor is logged in,
       likewise for invite_reply['user1'] if it exists"""
    invite_row, errors = ig._invite_row(self)
    if invite_row:
      errors += self._load_invite(invite_row)
      if user:
        errors += self._try_adding_invitee(user, invite_row)
      response_row = app_tables.invites.get(origin=False, link_key=self.link_key, current=True)
      if response_row:
        if self.invitee:
          response_row['user1'] = self.invitee
          if register:
            accounts.init_user_info(user)
        errors += self._load_response(response_row)
    else:
      non_current_invite = self._old_invite_row()
      if non_current_invite:
        errors.append("This invite link is no longer active.")
      else:
        errors.append("Invalid invite link")
    return errors
        
  def _load_invite(self, invite_row):
    errors = []
    self.invite_id = invite_row.get_id()
    self.inviter = invite_row['user1']
    self.inviter_guess = invite_row['guess']
    self.rel_to_inviter = invite_row['relationship2to1']
    return errors
  
  def _load_response(self, response_row):
    errors = []
    self.response_id = response_row.get_id()
    self.invitee = response_row['user1']
    self.invitee_guess = response_row['guess']
    self.rel_to_invitee = response_row['relationship2to1']
    return errors

  def _try_adding_invitee(self, user, invite_row):
    from . import connections as c
    errors = []
    self.invitee = user
    if user['phone'] and not phone_match(self.inviter_guess, user):
      errors += [p.MISTAKEN_INVITER_GUESS_ERROR]
      sm.add_invite_guess_fail_prompt(self)
      errors += self.cancel(invite_row)
    else:
      if invite_row['user2'] and invite_row['user2'] != self.invitee:
        sm.warning(f"invite['user2'] being overwritten, {user['email']}, {dict(invite_row)}, {self.invite_id}")
      invite_row['user2'] = self.invitee
      c.try_adding_to_invite_proposal(invite_row, self.invitee)
    return errors

  def respond(self, user_id=""):
    """Returns list of error strings"""
    user = sm.get_acting_user(user_id)
    invite_row, errors = ig._invite_row(self)
    if user:
      errors += self._try_adding_invitee(user, invite_row)
      if errors:
        return errors
    now = sm.now()
    errors += self.invalid_response()
    if errors:
      return errors
    if not phone_match(self.invitee_guess, self.inviter):
      errors.append(f"You did not accurately provide the last 4 digits of {sm.name(self.inviter)}'s confirmed phone number.")
      return errors
    response_row, errors = ig._response_row(self)
    if not response_row:
      response_row = app_tables.invites.add_row(date=now,
                                                origin=False,
                                                distance=1,
                                                user1=self.invitee,
                                                user2=self.inviter,
                                                link_key=self.link_key,
                                                current=True,
                                               )
    ig._edit_row(response_row, self.invitee_guess, self.rel_to_invitee, now)
    if self.invitee and self.invitee['phone']:
      from . import connections as c
      self.connection_successful = c.try_connect(invite_row, response_row)
      if not self.connection_successful:
        sm.warning(f"unexpected failed connect, {self.invitee['email']}, {self.invite_id}")
    return errors

  def load(self):
    invite_row, errors = ig._invite_row(self)
    if invite_row:
      errors += self._load_invite(invite_row)
      response_row, _ = ig._response_row(self)
      if response_row:
        errors += self._load_response(response_row)
    return errors
