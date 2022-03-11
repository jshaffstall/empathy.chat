import anvil.server
import anvil


def error_handler(err):
  app_info_dict = {'id': anvil.app.id,
                   'branch': anvil.app.branch,
                   'environment.name': anvil.app.environment.name,
                  }
  anvil.server.call('report_error', repr(err), app_info_dict)
  raise(err)


anvil.set_default_error_handling(error_handler)

url_hash = anvil.get_url_hash()
known_hash_keys = {'invite', 'group'}
if isinstance(url_hash, dict) and len(url_hash.keys() & known_hash_keys) == 1:
  [known_key] = url_hash.keys() & known_hash_keys
  value = url_hash[known_key]
  from . import invited
  from . import groups
  hash_router = {'invite': invited.handle_link,
                 'group': groups.handle_link,
                }
  hash_router[known_key](value)
else:
  anvil.open_form('LoginForm')
