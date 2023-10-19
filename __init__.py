import sys, os, re
sys.path.insert(0,os.path.dirname(os.path.realpath(__file__)))
from .prompt_info import *

NODE_CLASS_MAPPINGS= {}
NODE_DISPLAY_NAME_MAPPINGS = {}

VERSION = "1.0.0"

def pretty(name:str):
    return " ".join(re.findall("[A-Z][a-z]*", name))

for clazz in CLAZZES:
    name = clazz.__name__
    NODE_CLASS_MAPPINGS[name] = clazz
    NODE_DISPLAY_NAME_MAPPINGS[name] = pretty(name)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

import shutil
import folder_paths

application_root_directory = os.path.dirname(folder_paths.__file__)
application_web_extensions_directory = os.path.join(application_root_directory, "web", "extensions", "cg_prompt_info")
module_root_directory = os.path.dirname(os.path.realpath(__file__))
module_js_directory = os.path.join(module_root_directory, "js")

shutil.copytree(module_js_directory, application_web_extensions_directory, dirs_exist_ok=True)
