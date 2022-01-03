from ._anvil_designer import RelationshipTemplate
from anvil import *
import anvil.users
import anvil.server
from ..... import helper as h
from ..RelEdit import RelEdit


class Relationship(RelationshipTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    self.row_spacing = 0
    self.update()
    if self.item['child']:
      self.child_column_panel.add_component(Relationship(item=self.item['child']))
    else:
      their = self.item.get('their')
      if their:
        self.spacer_1.visible = False
        text = f' (and introduces you as their "{their}")'
        tooltip = f"description last edited {h.short_date_str(h.as_local_tz(self.item['their_date']))}"
        self.child_column_panel.add_component(Label(text=text, tooltip=tooltip, spacing_above="none"))

  def update(self):
    self.flow_panel_1.tooltip = f"description last edited {h.short_date_str(h.as_local_tz(self.item['date']))}"
        
  def edit_rel_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    rel_item = {'name': self.item['their_name'],
                'user2_id': self.item['their_id'],
                'relationship': self.item['desc'],
                }
    edit_form = RelEdit(item=rel_item)
    out = alert(content=edit_form,
                large=True,
                dismissible=False,
                buttons=[])
    if out is True:
      self.item['date'] = anvil.server.call('save_relationship', edit_form.item)
      self.item['desc'] = edit_form.item['relationship']
      self.refresh_data_bindings()
      self.update()
