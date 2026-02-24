import os
import importlib


class PluginSystem:

    def __init__(self):
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        if not os.path.exists("plugins"):
            return

        for file in os.listdir("plugins"):
            if file.endswith(".py"):
                module_name = f"plugins.{file[:-3]}"
                module = importlib.import_module(module_name)

                if hasattr(module, "register"):
                    self.plugins.append(module.register())

    def execute(self, event_name, context):
        for plugin in self.plugins:
            if hasattr(plugin, event_name):
                getattr(plugin, event_name)(context)