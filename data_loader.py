import copy
import json
import os
import zipfile
import bpy
import io
import tempfile


class DataLoader:
    loaded_data = None
    block_states_path = "assets/minecraft/blockstates"
    block_models_path = "assets/minecraft/models/block"
    textures_path = "assets/minecraft/textures"


    def __init__(self):
        self.minecraft_location = ""
        self.loaded_data = {
            "blockstates": {},
            "block_models": {},
            "item_models": {},
        }
        self.initialized = False
        self.tmp_dir = "C:\\Users\\saull\\Documents\\GitHub\\MCBDE"
        # tempfile.mkdtemp()


    def load_json_directory(self, jar, path, data_dict):
        all_files = jar.namelist()
        target_json_files = [file for file in all_files if file.startswith(path)]
        for file_name in target_json_files:
            json_content = jar.read(file_name)
            try:
                json_content_string = json_content.decode('utf-8')
                json_data = json.loads(json_content_string)
                identifier = os.path.splitext(os.path.basename(file_name))[0]
                data_dict[identifier] = json_data
            except UnicodeDecodeError:
                print(f"Unable to decode {file_name} as UTF-8. It may be binary data.")
            except json.JSONDecodeError:
                print(f"Unable to parse {file_name} as JSON.")


    def initialize_data(self, minecraft_location):
        self.minecraft_location = minecraft_location
        try:
            with zipfile.ZipFile(minecraft_location, 'r') as jar:
                self.load_json_directory(jar, self.block_states_path, self.loaded_data["blockstates"])
                
                self.load_json_directory(jar, self.block_models_path, self.loaded_data["block_models"])

                self.initialized = True
                print("Data initialized!")
        except Exception as e:
            print("Failed to load data.", e)


    def get_data(self, data_dict, identifier):
        if data_dict in self.loaded_data:
            return copy.deepcopy(self.loaded_data[data_dict].get(identifier))
        else:
            print(f"Error: {data_dict} not found in loaded data.")
            return None
        

    def load_image(self, name):
        print("looking for image", name)

        if name in [i.name for i in bpy.data.images]:
            print(name, "image already loaded")
            return bpy.data.images[name]
        #try:
        with zipfile.ZipFile(self.minecraft_location, 'r') as jar:
            all_files = jar.namelist()

            split_name = name.split('/')
            target_directory = split_name[0]
            target_basename = split_name[1]
            directory_path = self.textures_path + "/" + target_directory

            target_image_files = [file for file in all_files if file.startswith(directory_path)]

            for file_name in target_image_files:
                basename = os.path.splitext(os.path.basename(file_name))[0]
                if basename == target_basename:
                    image_data = jar.read(file_name)

        tmp_image_path = os.path.join(self.tmp_dir, name.replace("/", "-") + ".png")

        with open(tmp_image_path, 'wb') as tmp_image_file:
            tmp_image_file.write(image_data)

        image = bpy.data.images.load(filepath=tmp_image_path)
        image.name = name

        return image

        # except:
        #     print("Failed to load image", name)
            

        
    def is_initialized(self):
        return self.initialized
        
data_loader = DataLoader()