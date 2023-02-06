bl_info = {
    "name": "Multiple PyMOL protein importer",
    "author": "Guy E Mayneord",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Scene",
    "description": "Adds an import panel for importing a directory of wrl files, and simplifying",
    "warning": "",
    "wiki_url": "",
    "category": "Guy Scripting",
    }

import bpy
from os import path, walk

# =============================================================
# Setting up the buttons to be called in the panel
# =============================================================
class import_wrl_files(bpy.types.Operator):
    """Import wrl files in the directory given"""
    bl_idname = "myops.import_wrl_files"
    bl_label = "Import the wrl files from the directory given"

    def execute(self, context):
        wrl_files_list = self.find_all_files(
                       str(context.window_manager.input_directory_location),
                       file_type="wrl",
                       dir_only=True)

        # Check if the pymol colour scheme already exists.
        material_list = [each_item.name for each_item in bpy.data.materials]
        if "PyMOL_Colour_Scheme" not in material_list:
            pymol_mat_obj = bpy.data.materials.new("PyMOL_Colour_Scheme")
            pymol_mat_obj.use_nodes = True
            vertex_input = pymol_mat_obj.node_tree.nodes.new('ShaderNodeVertexColor')

            pymol_mat_obj.node_tree.links.new(
                vertex_input.outputs['Color'],
                pymol_mat_obj.node_tree.nodes['Principled BSDF'].inputs['Base Color'])

        for each_file in wrl_files_list:
            current_mesh = self.wrl_importer(context, each_file)
            self.remove_doubles_function(current_mesh)
            self.decimate_vertices(context,
                                   current_mesh,
                                   context.scene.simplify_val)

            if context.scene.add_texture:
                self.create_pymol_colourscheme(context, current_mesh)

        if len(wrl_files_list) > 0:
            self.report({'INFO'}, 'All objects imported and simplified')
        if len(wrl_files_list) == 0:
            self.report({'ERROR'},
                        "No wrl files found. Nothing imported. Please check source directory")
        return {'FINISHED'}

    def find_all_files(self, input_location, file_type='any',
                       dir_only=False, seperate_names_list=False):

        list_of_names = []
        for root, subFolders, files in walk(input_location):
            for file in files:
                if file_type == 'any':
                    list_of_names.append(str(path.join(root, file)))
                elif str(file).split('.')[-1] == file_type:
                    list_of_names.append(str(path.join(root, file)))
            if dir_only:
                break
        return list_of_names

    def wrl_importer(self, context, input_wrl_loc):
        mesh_object = None
        obj_file_name = path.basename(input_wrl_loc).split(".wrl")[0]
        # Get original list of objects and materials so we can remove
        # unnecessary new ones.
        original_objects = list(bpy.data.objects)
        original_materials_list = list(bpy.data.materials)
        # Import the file.
        bpy.ops.import_scene.x3d(filepath=input_wrl_loc,
                                 axis_forward='Z',
                                 axis_up='Y')

        # Work out the new name of the object in blender.
        imported_objs = [obj_name for obj_name in
                         list(bpy.data.objects) if obj_name not in
                         original_objects]

        new_materials = [each_material for each_material in
                         list(bpy.data.materials) if each_material not in
                         original_materials_list]

        # Object 1 is going to be the mesh, others are useless and
        # hence deleted.
        for i in range(len(imported_objs)):
            if i != 1:
                # Deselect all others
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[imported_objs[i].name].select_set(True)
                bpy.ops.object.delete()
            else:
                # Rename the object
                imported_objs[i].name = obj_file_name
                mesh_object = imported_objs[i]

        for each_material in new_materials:
            bpy.data.materials.remove(each_material)

        return obj_file_name

    def remove_doubles_function(self, object_for_simplification):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[object_for_simplification].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[object_for_simplification]
        # Switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles()
        # Switch back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Now smooth the verices.
        bpy.ops.object.shade_smooth()

    def decimate_vertices(self, context,
                          obj_for_dec, simplification_parameter):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[obj_for_dec].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[obj_for_dec]
        decimation_parameter = float(simplification_parameter)/100
        # Create a new decimation modifier called 'Simplification_Decimate'
        bpy.data.objects[obj_for_dec].modifiers.new("simp_dec", type="DECIMATE")
        # Now edit the parameters of this.
        bpy.data.objects[obj_for_dec].modifiers["simp_dec"].decimate_type = 'COLLAPSE'
        bpy.data.objects[obj_for_dec].modifiers["simp_dec"].ratio = decimation_parameter
        # Apply the modifier to the object.
        bpy.ops.object.modifier_apply(modifier="simp_dec")
        # Deselect everything
        bpy.ops.object.select_all(action='DESELECT')

    def create_pymol_colourscheme(self, context, obj_for_material):
        bpy.data.objects[obj_for_material].active_material = bpy.data.materials["PyMOL_Colour_Scheme"]

# =============================================================
# Now setting up the panel itself. Attaching in all the buttons
# =============================================================


class Protein_import_PT_panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "PyMOL Protein importer"
    bl_idname = "Protein_import_PT_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        layout.label(text="Directory containing .wrl files:")
        row = layout.row()
        row.prop(context.window_manager, "input_directory_location")
        row = layout.row()
        row.scale_y = 1.0
        layout.label(text="Simplification Parameter:")
        row = layout.row()
        row.scale_y = 1.0
        row.prop(context.scene, 'simplify_val', slider=True)
        row = layout.row()
        row.scale_y = 1.0
        row.prop(context.scene, "add_texture")
        row = layout.row()
        row.scale_y = 1.0
        row.operator("myops.import_wrl_files",
                     text="Import and Simplify Items")

# =============================================================
# Register modules for add-on.
# =============================================================
classes_for_register = [Protein_import_PT_panel, import_wrl_files]


def register():
    for each_class in classes_for_register:
        bpy.utils.register_class(each_class)

    bpy.types.Scene.add_texture = bpy.props.BoolProperty(name='Apply Pymol Texture',
                                                         description='Apply the pymol colorscheme to the imported objects',
                                                         default=False)

    bpy.types.Scene.simplify_val = bpy.props.FloatProperty(
                                 name='Simplification value',
                                 description='Simplification value: lower value = lower detail in model, but also fewer vertices',
                                 default=100,
                                 min=1,
                                 max=100,
                                 precision=1,
                                 step=1)

    from bpy.types import WindowManager
    from bpy.props import StringProperty
    # Need to declare this to be able to use it as a file explorer.
    WindowManager.input_directory_location = StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default=""
    )


def unregister():
    from bpy.types import WindowManager
    del WindowManager.input_directory_location
    del bpy.types.Scene.add_texture
    del bpy.types.Scene.simplify_val
    for each_class in classes_for_register:
        bpy.utils.unregister_class(each_class)


if __name__ == "__main__":
    register()
