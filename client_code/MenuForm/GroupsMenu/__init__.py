from ._anvil_designer import GroupsMenuTemplate
from anvil import *
import anvil.server
from .Groups import Groups
from .Members import Members
from ... import parameters as p

class GroupsMenu(GroupsMenuTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
   
    # Any code you write here will run when the form opens.
    self.top_form = get_open_form()
    self.go_members()
    
  def clear_page(self):
    for button in self.tabs_flow_panel.get_components():
      button.background = p.NONSELECTED_TAB_COLOR
    self.content_column_panel.clear()
      
  def load_component(self, content):
    """Reset MenuForm and load content form"""
    self.clear_page()
    self.content = content
    self.content_column_panel.add_component(self.content)  
    
  def go_groups(self):
    content = Groups()
    self.load_component(content)
    self.groups_tab_button.background = p.SELECTED_TAB_COLOR

  def go_members(self):
    content = Members()
    self.load_component(content)
    self.members_tab_button.background = p.SELECTED_TAB_COLOR    
  
  def groups_tab_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    self.go_groups()
    
  def members_tab_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    self.go_members()
  