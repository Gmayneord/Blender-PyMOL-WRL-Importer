# Blender-PyMOL-WRL-Importer
A blender add-on that allows the user to import .wrl files exported from PyMOL.
The add-on will create a panel in Properties > Scene called "PyMOL Protein importer". 
This can be given a directory containing .wrl files, and a simplification value can be set. When the "Import and Simplify" button is pressed, it will cycle through each .wrl file, import it into the blender scene and simplify it down according to the simplification value set (Removing doubles and decimating vertices). 
This allows the importing of large multi-subunit structures without crashing / machine slow-down from RAM shortages when importing these structures, as they frequently contain high mesh densities not required to maintain visual fidelity. Finally, the user can also select whether to apply the default PyMOL colour scheme (texture) upon import or not. If this is not selected, the texture is still imported, however not applied to the mesh. 
