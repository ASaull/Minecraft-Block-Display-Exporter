import copy
import json
import os


class DataLoader:
    def __init__(self):
        self.block_data_directory = "block_data"  # Adjust if needed
        self.loaded_data = {
            "blockstates": {},
            "block_models": {},
            "item_models": {},
            "block_textures": {},
            "item_textures": {},
        }
        self.initialized = False


    def load_json_directory(self, json_directory_path, data_dict):
        for file_name in os.listdir(json_directory_path):
            file_path = os.path.join(json_directory_path, file_name)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    identifier = os.path.splitext(os.path.basename(file_path))[0]
                    data_dict[identifier] = data
                except json.JSONDecodeError as e:
                    print(f"Error loading JSON file {file_path}: {e}")


    def initialize_data(self, data_directory):
        try:
            blockstates_path = os.path.join(data_directory, self.block_data_directory, "blockstates")
            self.load_json_directory(blockstates_path, self.loaded_data["blockstates"])
            
            blockmodels_path = os.path.join(data_directory, self.block_data_directory, "models", "block")
            self.load_json_directory(blockmodels_path, self.loaded_data["block_models"])

            self.initialized = True
            print("Data initialized!")
        except:
            print("Failed to load data.")



    def get_data(self, data_dict, identifier):
        if data_dict in self.loaded_data:
            return copy.deepcopy(self.loaded_data[data_dict].get(identifier))
        else:
            print(f"Error: {data_dict} not found in loaded data.")
            return None
        
    def is_initialized(self):
        return self.initialized
        
data_loader = DataLoader()