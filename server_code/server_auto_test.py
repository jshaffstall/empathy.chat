import anvil.users
import anvil.server
import anvil.tables
from anvil.tables import app_tables, order_by
import anvil.tables.query as q
import unittest
from anvil_extras.server_utils import timed
from . import matcher as m
from . import parameters as p
from . import connections as c
from . import invites
from . import invites_server
from . import server_misc as sm
from . import notifies as n


def name_mock(user, to_user):
  return user


class NamesTest(unittest.TestCase):
  def setUp(self):
    self.user = anvil.users.get_user()
    self.poptibo = app_tables.users.get(email="poptibo@yahoo.com")
    
  def test_single_name(self):
    self.assertEqual("Peter", n._names(["Peter"], to_user=self.poptibo, name_fn=name_mock))
    
  def test_two_names(self):
    self.assertEqual("Peter and Paul", n._names(["Peter", "Paul"], to_user=self.poptibo, name_fn=name_mock))

  def test_three_plus_names(self):  
    self.assertEqual("Peter, Paul, and Mary", n._names(["Peter", "Paul", "Mary"], to_user=self.poptibo, name_fn=name_mock))
    self.assertEqual("Peter, Paul, James, and Mary", n._names(["Peter", "Paul", "James", "Mary"], to_user=self.poptibo, name_fn=name_mock))


class InviteBasicTest(unittest.TestCase):
  def test_conversion(self):
    invite1 = invites.Invite(rel_to_inviter='test subject 1', inviter_guess="6666")
    s_invite1 = invites_server.Invite(invite1)
    self.assertEqual(s_invite1.inviter_guess, "6666")
    invite2 = s_invite1.portable()
    self.assertEqual(invite2.rel_to_inviter, 'test subject 1')
    
class InviteTest(unittest.TestCase):
  def setUp(self):
    self.start_time = sm.now()
    self.user = anvil.users.get_user()
    self.poptibo = app_tables.users.get(email="poptibo@yahoo.com")

  def test_invalid_add(self):
    invite1 = invites.Invite(inviter_guess="6666")
    s_invite1 = invites_server.Invite(invite1)
    errors = s_invite1.add()
    self.assertTrue(errors)

  def add_link_invite(self):
    self.invite1 = invites.Invite(rel_to_inviter='test subject 1', inviter_guess="6666")
    self.s_invite1 = invites_server.Invite(self.invite1)
    #self.invite1.relay('add')
    errors = self.s_invite1.add()
    self.assertFalse(errors)
    self.invite1 = self.s_invite1.portable()

  def cancel_link_invite(self): 
    self.s_invite1.cancel()
    self.assertFalse(self.s_invite1.inviter)
    
  def add_connect_invite(self):
    port_invitee = sm.get_port_user(self.poptibo, user1_id=self.user.get_id())
    self.invite2 = invites.Invite(rel_to_inviter='test subject 1', inviter_guess="5555", invitee=port_invitee)
    self.s_invite2 = invites_server.Invite(self.invite2)
    errors = self.s_invite2.add()
    self.assertFalse(errors)
    self.assertEqual(self.s_invite2.inviter, self.user)
    self.invite2 = self.s_invite2.portable()    
 
  def cancel_connect_invite(self): 
    self.s_invite2.cancel()
    self.assertFalse(self.s_invite2.inviter)

  def test_new_link(self):
    self.add_link_invite()
    self.assertEqual(self.invite1.inviter.user_id, self.user.get_id())
    self.assertTrue(self.invite1.link_key)
    self.cancel_link_invite()

#   def test_new_link2(self):
#     self.test_new_link()

  def test_new_connect1(self):
    self.add_connect_invite()
    self.assertEqual(self.invite2.inviter.user_id, self.user.get_id())
    self.assertFalse(self.invite2.link_key)
    self.assertTrue(self.invite2.invitee)
    #test_new_connect_dup
    port_invitee = sm.get_port_user(self.poptibo, user1_id=self.user.get_id())
    invite2dup = invites.Invite(rel_to_inviter='test subject 1 dup', inviter_guess="5555", invitee=port_invitee)
    s_invite2dup = invites_server.Invite(invite2dup)
    errors = s_invite2dup.add()
    self.assertTrue(errors)
    self.cancel_connect_invite()   
    
  def test_new_connect_failed_guess(self):
    port_invitee = sm.get_port_user(self.poptibo, user1_id=self.user.get_id())
    invite2 = invites.Invite(rel_to_inviter='test subject 1 dup', inviter_guess="6666", invitee=port_invitee)
    s_invite2 = invites_server.Invite(invite2)
    errors = s_invite2.add()
    self.assertTrue(errors)
    test_prompts = app_tables.prompts.search(user=self.user, 
                                             spec={'name': 'invite_guess_fail', 'to_id': self.poptibo.get_id()})
    print({'name': 'invite_guess_fail', 'to_id': self.poptibo.get_id()})
    self.assertEqual(len(test_prompts), 1)
    for test_prompt in test_prompts:
      test_prompt.delete()
     
  @timed
  def test_logged_in_visit1(self):
    self.add_link_invite()
    invite2a = invites.Invite(link_key=self.invite1.link_key)
#     s_invite2a = invites_server.Invite(invite2a)
#     errors = s_invite2a.visit(user=self.poptibo)
    errors = invite2a.relay('visit', {'user': self.poptibo})
    self.assertTrue(errors)
    self.assertEqual(errors[0], p.MISTAKEN_INVITER_GUESS_ERROR)

  def test_logged_in_visit2(self):
    self.add_link_invite()
    self.s_invite1.inviter_guess = self.poptibo['phone'][-4:]
    self.s_invite1.edit_invite()
    invite2b = invites.Invite(link_key=self.s_invite1.link_key)
    s_invite2b = invites_server.Invite(invite2b)
    errors = s_invite2b.visit(**{'user': self.poptibo})
    self.assertFalse(errors)
    self.assertEqual(s_invite2b.invitee, self.poptibo)

  def test_new_visit(self):
    self.add_link_invite()
    invite2c = invites.Invite(link_key=self.invite1.link_key)
    s_invite2c = invites_server.Invite(invite2c)
    errors = s_invite2c.relay('visit', {'user': None})
    self.assertFalse(errors)
    self.assertFalse(invite2c.invitee)
    
  @timed
  def test_connect_response(self):
    self.add_connect_invite()
#     self.invite2['invitee_guess'] = "6688"
#     self.invite2['rel_to_invitee'] = "tester 3"
#     errors = self.invite2.relay('respond')
    self.s_invite2['invitee_guess'] = "6688"
    self.s_invite2['rel_to_invitee'] = "tester 3"
    self.assertEqual(self.s_invite2.inviter, self.user)
    errors = self.s_invite2.relay('respond', {'user_id': self.poptibo.get_id()})
    self.assertFalse(errors)
    self.assertEqual(c.distance(self.user, self.poptibo, up_to_distance=1), 1)
    c.disconnect(self.poptibo.get_id())

  def tearDown(self):
    test_invites = app_tables.invites.search(user1=q.any_of(self.user, self.poptibo), date=q.greater_than(self.start_time), current=True)
    for test_invite in test_invites:
      test_invite.delete()

class SecondsLeftTest(unittest.TestCase):
  def test_initial_requesting(self):
    self.assertEqual(m._seconds_left("requesting"), p.WAIT_SECONDS)
 

class NotifyConnectedTest(unittest.TestCase):
  def test_notify_connected(self):
    class FakeUser(dict):
      def get_id(self):
        return [42,42]
    invite_dict = {'user1': FakeUser(), 'user2': FakeUser(first_name="first", last_name="last"), 'distance': 1}
    invite_reply_dict = {'relationship2to1': "spouse"}
    self.assertEqual(c._connected_prompt(invite_dict, invite_reply_dict)['spec'], 
                     dict(name="connected", to_name="first last", to_id=[42,42], rel="spouse"),
                    )


@anvil.server.background_task
def server_auto_tests(verbosity=2):
  #unittest.main(exit=False)
  import sys
  test_modules = ['auto_test', 'exchange_test']#, 'server_auto_test']
  test = unittest.TestLoader().loadTestsFromNames(test_modules)
  unittest.TextTestRunner(stream=sys.stdout, verbosity=verbosity).run(test)
    