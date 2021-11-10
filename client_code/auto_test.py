from anvil import *
import anvil.server
import unittest
import time
from . import helper as h
from . import portable as port
# from .MenuForm import MenuForm
# from .MenuForm.DashForm import DashForm

class Seconds2WordsTest(unittest.TestCase):
  def test_day(self):
    self.assertEqual(h.seconds_to_words(3600*24), "1 day, 0 seconds")
  
  def test_day_no_seconds(self):
    self.assertEqual(h.seconds_to_words(3600*24, include_seconds=False), "1 day, 0 minutes")
    
  def test_minus(self):
    self.assertEqual(h.seconds_to_words(-1), "minus 1 second")

    
class FullNameTest(unittest.TestCase):
  def test_distance(self):
    for distance in range(1, 5):
      self.assertEqual(
        port.full_name("first", "last", distance),
        "first last" if distance <= 2 else "first"
      )
    
def run_auto_tests():
  Seconds2WordsTest().main()
  FullNameTest().main()
  
    
class TestNow():

  def setUp(self):
    self.top_form = get_open_form()
    self.top_form.home_link_click()

  def test_repeat_now_proposal(self):
    for email, user_id in self.top_form.test_requestuser_drop_down.items:
      if email == "A":
        accept_user_id = user_id
    for i in range(2):
      anvil.server.call('add_now_proposal')
      time.sleep(15)
      anvil.server.call('accept_now_proposal', user_id=accept_user_id)
      time.sleep(5)
      anvil.server.call('cancel', user_id=accept_user_id)
      time.sleep(5)
      anvil.server.call('cancel')

  def test_multiple_proposal_times(self):
    self.top_form.content.propose_button_click()
    time.sleep(5)
    self.top_form.proposal_alert.button_add_alternate_click()
    time.sleep(5)
    self.top_form.proposal_alert.save_button_click()

def run_now_test():
  #unittest.main()
  #print("run manually")
  test = TestNow()
  test.setUp()
  #test.test_repeat_now_proposal()
  test.test_multiple_proposal_times()

# class TestNow(unittest.TestCase):

#   def setUp(self):
#     self.top_form = get_open_form()
#     self.top_form.go_dash()

#   def test_add_my_now_proposal(self):
#     self.top_form.content.propose_button_click()
#     focused_component = get_focused_component()
#     print(focused_component.__dict__())
#     #self.assertEqual( multiply(3,4), 12)


# def run_tests():
#   unittest.main()