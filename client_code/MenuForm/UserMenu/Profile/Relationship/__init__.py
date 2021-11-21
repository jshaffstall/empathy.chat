from ._anvil_designer import RelationshipTemplate
from anvil import *
import anvil.users
import anvil.server
from ..... import helper as h


class Relationship(RelationshipTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    self.row_spacing = 0
    self.flow_panel_1.tooltip = f"description last edited {h.short_date_str(self.item['date'])}"
    if self.item['child']:
      self.child_column_panel.add_component(Relationship(item=self.item['child']))
    else:
      their = self.item.get('their')
      if their:
        self.spacer_1.visible = False
        text = f' (and describes you as their "{their}")'
        tooltip = f"description last edited {h.short_date_str(self.item['their_date'])}"
        self.child_column_panel.add_component(Label(text=text, tooltip=tooltip, spacing_above="none"))
