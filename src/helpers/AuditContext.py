from flask import Response

from flask import g
from werkzeug.local import LocalProxy

current_auditlog_action = LocalProxy(lambda: getattr(g, '_current_auditlog_action', None))

def set_current_auditlog_action(action):
    g._current_auditlog_action = action
