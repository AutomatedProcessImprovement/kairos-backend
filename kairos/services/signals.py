from blinker import Namespace

my_signals = Namespace()
case_updated = my_signals.signal('case-updated')
status_changed = my_signals.signal('status-changed')