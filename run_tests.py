import sys, unittest, tkinter as tk
from unittest.mock import patch
original = tk.Toplevel.__init__
def hidden(window, *args, **kwargs):
    original(window, *args, **kwargs)
    window.withdraw()
with patch.object(tk.Toplevel, '__init__', hidden), patch.object(tk.Toplevel, 'grab_set', return_value=None):
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in ['test_word_clean', 'test_mapping_search', 'test_history', 'test_auto_remove'])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
