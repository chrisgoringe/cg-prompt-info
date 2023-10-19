import inspect, json
from nodes import LoadImage
from folder_paths import get_annotated_filepath
from PIL import Image
from server import PromptServer

def get_outputs():
    for frame_info in inspect.stack():
        executor_maybe = frame_info.frame.f_locals.get("e",None)
        if hasattr(executor_maybe,'outputs'):
            return executor_maybe.outputs
        
def represent(thing):
    if isinstance(thing,str) or isinstance(thing, int) or isinstance(thing, float):
        return thing
    return f"{thing}"[:30]
        
def insertAllInAndOut(prompt, extra, all_outputs=None):
    extra['workflow']['values'] = {}
    for node in extra['workflow']['nodes']:
        node_id = str(node['id'])
        out = {}
        inp = {}
        type = node['type']
        print(f"Node {node_id} ({type})")
        if all_outputs and 'outputs' in node:
            for i, output in enumerate(node['outputs']):
                try:
                    out[output['name']] = represent(all_outputs[node_id][i][0])
                except KeyError:
                    pass

        if node_id in prompt and 'inputs' in prompt[node_id]:
            for name in prompt[node_id]['inputs']:
                v = prompt[node_id]['inputs'][name]
                if isinstance(v,list):
                    if all_outputs and v[0] in all_outputs:
                        v = all_outputs[v[0]][v[1]][0]
                    else:
                        continue
                inp[name] = represent(v)

        if inp or out:
            extra['workflow']['values'][node_id] = {"type":node['type'],"inputs":inp,"outputs":out}
        
class AddInfo():
    CATEGORY = "prompt_info"
    FUNCTION = "func"
    
    @classmethod    
    def INPUT_TYPES(s):
        return { "required":{"image":("IMAGE",{})}, "hidden":{"prompt":"PROMPT", "extra":"EXTRA_PNGINFO"} }
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    def func(self, image, prompt, extra):
        insertAllInAndOut(prompt, extra, get_outputs())
        return (image,)
    
class LoadImageWithInfo(LoadImage):
    CATEGORY = "prompt_info"
    FUNCTION = "func"

    RETURN_TYPES = LoadImage.RETURN_TYPES + ("STRING",)
    RETURN_NAMES = ("image", "mask", "info")

    def func(self, image):
        loaded = self.load_image(image)
        filepath = get_annotated_filepath(image)
        with Image.open(filepath) as img:
            extra_pnginfo_loaded = img.text if hasattr(img,'text') else {}

            if not 'workflow' in extra_pnginfo_loaded:  # image doesn't have workflow saved
                return loaded + (json.dumps({}),)
            
            extra_pnginfo_loaded['workflow'] = json.loads(extra_pnginfo_loaded['workflow'])
            prompt = json.loads(extra_pnginfo_loaded['prompt'])
            
            if not 'values' in extra_pnginfo_loaded['workflow']: # workflow doesn't have values - do what we can
                insertAllInAndOut(prompt, extra_pnginfo_loaded)
            
            return loaded + (json.dumps(extra_pnginfo_loaded['workflow']['values'], indent=2),)
            
class ExtractInfo():
    CATEGORY = "prompt_info"
    FUNCTION = "func"
    OUTPUT_NODE = True

    @classmethod    
    def INPUT_TYPES(s):
        return {"required": {
            "info": ("STRING", {"forceInput": True}), 
            "node_id": ("INT", {"default": 0 }), 
            "side": (["inputs","outputs"],{}),
            "name": ("STRING", {"default":""},) 
        }, "hidden": {"id":"UNIQUE_ID"}}

    RETURN_TYPES = ("STRING","FLOAT","INT")
    RETURN_NAMES = ("string","float","int")
    def func(self, info, node_id, side, name, id):
        try:
            thing = json.loads(info)
        except json.JSONDecodeError:
            print("JSONDecodeError")
            return (info,0,0)

        try:
            thing = thing[str(node_id)]
        except KeyError:
            text = "\n".join(["Available Nodes:",]+[f"{id} ({thing[id]['type']})" for id in thing])
            PromptServer.instance.send_sync("cg.prompt_info.textmessage", {"id": id, "message":text})
            return (thing, None, None)
        
        try:
            thing = thing[side][name]
        except KeyError:
            text = f"Available values on {node_id}:\n\n"
            if len(thing['inputs']):
                text += "\n".join(["inputs:",]+[f"{name}" for name in thing['inputs']]+["\n"])
            if len(thing['outputs']):
                text += "\n".join(["outputs:",]+[f"{name}" for name in thing['outputs']]+[""])
            PromptServer.instance.send_sync("cg.prompt_info.textmessage", {"id": id, "message":text})
            return (thing, None, None)

        if not isinstance(thing,str):
            thing = json.dumps(thing, indent=2)

        PromptServer.instance.send_sync("cg.prompt_info.textmessage", {"id": id, "message":thing})
        
        try:
            flt = float(thing)
        except ValueError:
            return (thing, None, None)
        
        try:
            nt = int(thing)
        except ValueError:
            return (thing, flt, None)

        return (thing, flt, nt)

CLAZZES = [AddInfo, LoadImageWithInfo, ExtractInfo]