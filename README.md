# Minecraft Block Display Exporter Blender Add-on

## About

This is a Blender add-on for generating vanilla Minecraft block display commands.

|In Blender|In Minecraft|
|-|-|
|![mcbde_1](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/eca8f41f-9d4e-4a42-8728-76f93e9c89bb)|![mcbde_2](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/322455c1-bb7c-4fbc-a85d-7f1c42892a99)|


## Installation

Download this repository as a zip file and install it in Blender as an add-on

## Usage

Once the add-on has been installed, you can find the MCBDE panel in the 3D view sidebar.

|![](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/d54193cf-7f1e-4d97-985e-19fd12eb2bea) | ![](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/9712ea85-71ee-41d1-b484-18c1e29ec543)|
|-|-|

Since we cannot legally bundle the Minecraft textures and models, you must link the add-on to a Minecraft jar file in your Minecraft installation directory. By default in Windows, this is located at

    C:\Users\<YOUR_USERNAME>\AppData\Roaming\.minecraft\versions\1.X.X\1.X.X.jar

|![howto_annotated_3](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/2d022090-75a6-47fa-b382-cb28348393ed) | ![howto_annotated_4](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/20eb2d20-9604-42fd-9b96-7cb41acedee8)|
|-|-|

Once this is done, the data can be loaded with the "Load Data" button, and the rest of the UI will appear.

|![howto_annotated_5](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/fd7308ec-8d33-4811-ba6f-be6805ca2ef2)|
|-|

Now, with any mesh object(s) selected (it doesn't matter what mesh the object has, it will be overwritten!), you can select a Minecraft block from the "Type" dropdown. At this point, the mesh will change, but the texture will not show until you switch the viewport shading to "Material Preview".

|![howto_annotated_6](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/491b3db6-6efe-421d-b047-f8f6f5459145)|![howto_annotated_7](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/2a6a7113-1d69-4978-9baf-cc2f67546755)|
|-|-|

Now, for blocks that have properties, these can be changed with the dropdown menus. As you manipulate blocks, you can scale, rotate, and transform them as you usually would in Blender, but do not enter Edit Mode to change the mesh manually as this will not be preserved when generating the Minecraft command.

|![howto_annotated_8](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/37d05af1-8497-4d99-a68a-eac4492fa3d7)|![howto_annotated_9](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/ec90814d-7393-416b-842b-436f4cfe17b5)|
|-|-|

Once you are happy with your model, you can generate the command by clicking on the "Generate Command" button, Note that the command block which will run the command is considered to have its north west corner at the Blender origin, and is
positioned as indicated in the screenshot.

|![howto_annotated_10](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/1272e6f5-f229-4bf2-8ac4-63c7ccb0f149)|
|-|

Once you copy the command from the textbox in Blender, you can open Minecraft and place a command block and a button where you want the entity to be placed. Simply paste the command into the
command block, press the button, and the entity will be generated. Delete the command block and you're finished!

|![howto_annotated_11](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/6b20e712-ecf1-4336-84c3-47eed1223f7d)|![howto_annotated_12](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/e0471304-fac1-4c8b-b1fd-0afb62340c28)|
|-|-|
|![howto_annotated_13](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/60c3f518-131f-40aa-a91e-9afebad4fc55)|![howto_annotated_14](https://github.com/ASaull/Minecraft-Block-Display-Exporter/assets/34991394/bd0090d5-ece9-46d8-8fd4-cc08022539cd)|

Once the entity has been created, you can delete it with the command

    /kill @e[type=minecraft:block_display, distance=..3]

which will delete *all* entities in a 3 block range. If you want more discretion, I highly reccommend the Axiom mod.

**Axiom:** https://modrinth.com/mod/axiom

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
