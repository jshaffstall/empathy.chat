from anvil import *


class MyJitsi(MyJitsiTemplate):
  def __init__(self, name, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.name = name

    # Any code you write here will run when the form opens.
    
  def form_show(self, **event_args):
    """This method is called when the HTML panel is shown on the screen"""
    self.call_js("initJitsi", "meet.jit.si", {"roomName": self.name, "height": 500})

