import os
import importlib
import sys


class PluginSystem:

    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = plugin_dir
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        if not os.path.exists(self.plugin_dir):
            return

        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        for file in os.listdir(self.plugin_dir):
            if file.endswith(".py"):
                module_name = file[:-3]
                module = importlib.import_module(module_name)

                if hasattr(module, "register"):
                    self.plugins.append(module.register())

    def execute(self, event_name, context):
        for plugin in self.plugins:
            if hasattr(plugin, event_name):
                try:
                    getattr(plugin, event_name)(context)
                except Exception:
                    # Avoid crashing the app on plugin errors.
                    continue
