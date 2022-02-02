import anvil.server
from .server_misc import authenticated_callable
from . import exchange_interactor as ei


@authenticated_callable
def add_chat_message(user_id="", message="[blank test message]"):
  print(f"add_chat_message, '[redacted]', {user_id}")
  return ei.add_chat_message(user_id, message)


@authenticated_callable
def update_my_external(my_external, user_id=""):
  print(f"update_my_external, {my_external}, {user_id}")
  ei.update_my_external(my_external, user_id="")


@authenticated_callable
def update_match_form(user_id=""):
  return ei.update_match_form(user_id)

  
@authenticated_callable
def submit_slider(value, user_id=""):
  """Return their_value"""
  print(f"submit_slider, '[redacted]', {user_id}")
  return ei.submit_slider(value, user_id)
