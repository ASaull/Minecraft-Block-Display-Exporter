# Minecraft Block Display Exporter Blender Add-on

## About

This is a Blender add-on for generating Minecraft block display commands.

## Installation

Download this repository as a zip file and install it in Blender as an add-on

## Usage

Once the add-on has been installed, you can find the MCBDE panel in the 3D view sidebar.

⠀             |  ⠀
:-------------------------:|:-------------------------:
![]((https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/d54193cf-7f1e-4d97-985e-19fd12eb2bea))  |  ![]((https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/9712ea85-71ee-41d1-b484-18c1e29ec543))

Since we cannot legally bundle the Minecraft textures and models, you must link the add-on to your Minecraft installation directory. By default in Windows, this is located at
    C:\Users\<YOUR_USERNAME>\AppData\Roaming\.minecraft


Once this is done, the data can be loaded with the "Load Data" button, and the rest of the UI will appear.


Now, with any mesh object(s) selected (it doesn't matter what mesh the object has, it will be overwritten!), you can select a Minecraft block from the "Type" dropdown. At this point, the mesh will change, but the texture will not show until you switch the viewport shading to "Material Preview".


Now, for blocks that have properties, these can be changed with the dropdown menus. As you manipulate blocks, you can scale, rotate, and transform them, but do not enter Edit Mode to change the mesh manually as this will not be preserved when exporting to Minecraft.


Once you are happy with your model, you can generate the command by clicking on the "Generate Command" button.




## TODO
 - Support block models for blocks without variants
 - Support cross-shaped plants
 - Fix origin command block resetting to command block
 - Support removing model entirely, with empty type
 - Create user-visible error messages for file-loading errors
 - Allow the user to only input their .minecraft directory, and just choose the latest version of Minecraft automatically
 - Deal with cases where texture is animated (only take top 16x16)
 - Account for texture uv rotation (anvil)
 - Give colour to grayscale blocks (leaves, stems)
 - Create a bed model since they are hardcoded into the game. (why??) So are conduits...
 - Support textures that determine UVs automatically (composter)
 - Create a dedicate release zip file
