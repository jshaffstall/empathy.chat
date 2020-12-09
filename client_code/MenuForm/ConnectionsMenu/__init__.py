from ._anvil_designer import ConnectionsMenuTemplate
from anvil import *
import anvil.server
from .Connections import Connections
from .Blocks import Blocks
from ... import parameters as p

class ConnectionsMenu(ConnectionsMenuTemplate):
  
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
   
    # Any code you write here will run when the form opens.
    self.top_form = get_open_form()
    self.go_connections()
    
  def clear_page(self):
    for button in self.tabs_flow_panel.get_components():
      button.background = p.NONSELECTED_TAB_COLOR
    self.content_column_panel.clear()
      
  def load_component(self, content):
    """Reset MenuForm and load content form"""
    self.clear_page()
    self.content = content
    self.content_column_panel.add_component(self.content)  
    
  def go_connections(self):
    content = Connections()
    self.load_component(content)
    self.connections_tab_button.background = p.SELECTED_TAB_COLOR

  def go_blocks(self):
    content = Blocks()
    self.load_component(content)
    self.blocks_tab_button.background = p.SELECTED_TAB_COLOR
    
  def connections_tab_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    self.go_connections()

  def blocks_tab_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    self.go_blocks()

