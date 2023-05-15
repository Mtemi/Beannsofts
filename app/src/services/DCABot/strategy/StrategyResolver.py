from typing import Dict
import os
import sys
import inspect
import os
from pathlib import Path
from app.src.utils import logging

logger = logging.GetLogger(__name__)
class StrategyResolver:
    def __init__(self):
        pass

    def loadStrategy(self, config: Dict[str, any] = None):
        """
        Load the custom class from config parameter
        :param config: configuration dictionary or None
        """
        logger.debug(f"The config being passed {config}")
        # get directory path for strategies
        p = Path()
        path = f"{str(p.resolve())}/strategies/"
        logger.debug("Loading strategies from path: %s" % path)
        try:
            self.loadModulesFromPath(path)
            # the strategy classname from the config
            classname = f"{config}.{config}"
            strategy = self.loadClassFromName(classname)
            return strategy
        except Exception as e:
            logger.error(f"Error loading strategy {e}")

    def loadModulesFromPath(self, path):
        """
        Import all modules from the given directory
        """
        # Check and fix the path
        if path[-1:] != '/':
            path += '/'

        # Get a list of files in the directory, if the directory exists
        if not os.path.exists(path):
            raise OSError("Directory does not exist: %s" % path)

        # Add path to the system path
        sys.path.append(path)
        # Load all the files in path
        for f in os.listdir(path):
            # Ignore anything that isn't a .py file
            if len(f) > 3 and f[-3:] == '.py':
                modname = f[:-3]
                # Import the module
                __import__(modname, globals(), locals(), ['*'])
    
    def loadClassFromName(self, fqcn):
        # Break apart fqcn to get module and classname
        paths = fqcn.split('.')
        modulename = '.'.join(paths[:-1])
        classname = paths[-1]
        # Import the module
        __import__(modulename, globals(), locals(), ['*'])
        # Get the class
        cls = getattr(sys.modules[modulename], classname)
        # Check cls
        if not inspect.isclass(cls):
            raise TypeError("%s is not a class" % fqcn)
        # Return class
        return cls