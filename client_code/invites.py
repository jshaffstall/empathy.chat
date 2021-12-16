import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from . import helper as h
from . import parameters as p


class Invites(h.AttributeToKey):
  def __init__(self):
    self.invites = []
    
  def to_data(self):
    return self.invites
    
  def __len__(self):
    return len(self.invites)
    
  def save(self):
    invites_data = [invite.to_data() for invite_data in self.invites]
    anvil.server.call('save_invites', invites_data)
    
  def load(self):
    invites_data = anvil.server.call('load_invites')
    self.invites = [Invite(invite_data) for invite_data in invites_data]

   
@anvil.server.portable_class
class Invite(h.AttributeToKey):
  def __init__(self, invite_id="", inviter=None, rel_to_inviter="", inviter_guess="", link_key="", 
               response_id="", invitee=None, rel_to_invitee="", invitee_guess=""):
    self.invite_id = invite_id
    self.inviter = inviter
    self.rel_to_inviter = rel_to_inviter
    self.inviter_guess = inviter_guess
    self.link_key = link_key
    self.response_id = response_id
    self.invitee = invitee
    self.rel_to_invitee = rel_to_invitee
    self.invitee_guess = invitee_guess
 
  def update(self, new_self):
    for key, value in vars(new_self).items():
      setattr(self, key, value)

  def __str__(self):
    return vars(self)      
      
  @property
  def url(self):
    return f"{p.URL}#?invite={self.link_key}"    
  
  @property
  def not_yet_added(self):
    return not self.invite_id and not (self.response_id or self.invitee_guess or self.rel_to_invitee)
      
  @property                   
  def ready_to_add(self):
    return not self.invalid_invite()
  
  def invalid_invite(self):
    return Invite._check_guess_rel(self.inviter_guess, self.rel_to_inviter)
  
  def invalid_response(self):
    return Invite._check_guess_rel(self.invitee_guess, self.rel_to_invitee)
  
  @staticmethod
  def _check_guess_rel(guess, rel):
    errors = []
    if not guess or len(guess) != 4:
      errors.append("Wrong number of digits entered.")
    if not rel or len(rel) < p.MIN_RELATIONSHIP_LENGTH:
      errors.append("Please add a description of your relationship.")
    return errors
  
  @property                   
  def response_ready(self):
    return not self.invalid_response()
  
  def relay(self, method, kwargs=None, auth=True):
    if not kwargs:
      kwargs = {}
    if auth:
      new_object, errors = anvil.server.call('serve_invite', self, method, kwargs)
    else:
      new_object, errors = anvil.server.call('serve_invite_unauth', self, method, kwargs)
    self.update(new_object)
    return errors

