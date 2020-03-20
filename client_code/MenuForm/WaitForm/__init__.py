from ._anvil_designer import WaitFormTemplate
from anvil import *
import anvil.server
from .TimerForm import TimerForm
from .. import parameters as p
from .. import helper as h


class WaitForm(WaitFormTemplate):
  def __init__(self, dd_items, rt, pe, **properties):
    # You must call self.init_components() before doing anything else in this function
    self.init_components(**properties)
    #
    self.drop_down_1.items = dd_items
    self.drop_down_1.selected_value = rt
    self.pinged_em_check_box.checked = pe
    self.timer_1.interval = 1
    self.timer_2.interval = 1
    self.top_form = get_open_form()

  def renew_button_click(self, **event_args):
    self.top_form.confirm_wait()

  def cancel_button_click(self, **event_args):
    status = None
    seconds_left = None
    t = anvil.server.call('cancel')
    self.reset_status(status, seconds_left, t)

  def timer_1_tick(self, **event_args):
    """This method is called once per second, updating countdowns"""
    if self.top_form.status == "requesting" and self.top_form.seconds_left > 0:
      self.top_form.seconds_left -= 1
      self.timer_label.text = ("Your request will expire in:  "
                               + h.seconds_to_digital(self.seconds_left) )
    elif self.top_form.status == "pinging" and self.top_form.seconds_left > 0:
      self.top_form.seconds_left -= 1
      self.status_label.text = ("Potential match available. Time left for them "
                                + "to confirm:  "
                                + h.seconds_to_digital(self.top_form.seconds_left))

  def timer_2_tick(self, **event_args):
    """This method is called approx. once per second, checking for status changes"""
    # Run this code approx. once a second
    if self.status == "requesting":
      if self.seconds_left <= 0:
        self.tallies = anvil.server.call('cancel')
        alert("Request cancelled due to "
              + h.seconds_to_words(p.WAIT_SECONDS) + " of inactivity.",
              dismissible=False)
        self.set_seconds_left(None)
        self.reset_status()
    elif self.status == "pinging" and self.seconds_left <= 0:
      s, sl, self.tallies = anvil.server.call('cancel_other')
      self.set_seconds_left(s, sl)
      self.reset_status()
    if (h.now() - self.last_5sec).seconds > 4.5:
      # Run this code every 5 seconds
      self.last_5sec = h.now()
      if self.status == "requesting":
        s, sl, self.tallies = anvil.server.call_s('get_status')
        if s != self.status:
          self.set_seconds_left(s, sl)
          self.reset_status()
      elif self.status == "pinging":
        s, sl, self.tallies = anvil.server.call_s('get_status')
        if s != self.status:
          self.set_seconds_left(s, sl)
          if self.status == "requesting":
            alert("The other empathy request was cancelled.")
          self.reset_status()    
      
  def confirm_match(self, seconds):
    f = TimerForm(seconds, self.top_form.status)
    out = alert(content=f,
                title="A match is available. Are you ready?",
                large=False,
                dismissible=False,
                buttons=[("Yes", True), ("No", False)])
    s = None
    sl = None
    if out == True:
      self.top_form.status = "matched"
      s, sl, t = anvil.server.call('match_commenced')
    elif out in [False, "timer elapsed"]:
      t = anvil.server.call('cancel')
      if out == "timer elapsed":
        alert("A match was found, but the time available for you to confirm ("
              + h.seconds_to_words(p.CONFIRM_MATCH_SECONDS) + ") elapsed.",
              dismissible=False)
    elif out is None:
      t = anvil.server.call_s('get_tallies')
    else:
      print(out)
      assert out == "requesting"
      s, sl, t = anvil.server.call_s('get_status')
    self.reset_status(s, sl, t)
      
  def pinged_em_check_box_change(self, **event_args):
    """This method is called when this checkbox is checked or unchecked"""
    checked = self.pinged_em_check_box.checked
    s, sl, t = anvil.server.call('set_pinged_em', checked)
    self.reset_status(s, sl, t)
    
  def reset_status(self, s, sl, t):
    """Reset WaitForm status, removing from parent if needed"""
    self.top_form.set_seconds_left(s, sl)
    self.top_form.tallies = t
    if self.top_form.status not in ["requesting", "pinging"]:
      self.remove_from_parent()
      self.top_form.reset_status()
