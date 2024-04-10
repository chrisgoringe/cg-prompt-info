import sys, os, re
sys.path.insert(0,os.path.dirname(os.path.realpath(__file__)))
from .prompt_info import *

NODE_CLASS_MAPPINGS= {}
NODE_DISPLAY_NAME_MAPPINGS = {}

VERSION = "1.0.1"

def pretty(name:str):
    return " ".join(re.findall("[A-Z][a-z]*", name))

for clazz in CLAZZES:
    name = clazz.__name__
    NODE_CLASS_MAPPINGS[name] = clazz
    NODE_DISPLAY_NAME_MAPPINGS[name] = pretty(name)

WEB_DIRECTORY = "./js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', "WEB_DIRECTORY"]

