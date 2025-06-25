# To make this add-on installable, create an extension with it:
# https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html

bl_info = {
    "name": "SMPL-X + for Blender",
    "author": "Lison Boo",
    "version": (1, 0, 1),
    "blender": (4, 3, 2),
    "location": "Viewport > Right panel",
    "description": "",
    "doc_url": "",
    "category": "3D View",
}



import bpy
from random import randint
from bpy.types import (Panel, Operator)
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from json import JSONEncoder

from math import sqrt


global jointList

# subclass JSONEncoder
class setEncoder(JSONEncoder):
        def default(self, obj):
            return list(obj)


###### LOAD PANEL ########


class LoadOperator(Operator, ImportHelper):
    """Tooltip"""
    bl_idname = "load.1"
    bl_label = "Simple Object Operator"


    # Optional filter for file extensionsn for now only .npz
    filter_glob: StringProperty(
        default='*.npz',
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        print("enter execute")
        # This is the selected file path
        self.report({'INFO'}, f"Selected file: {self.filepath}")
        
        #Clean the scene
        
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        context.scene.my_file_path = self.filepath
        
        #needed to be here to get the choice of file
        
        bpy.ops.object.smplx_add_animation(filepath=context.scene.my_file_path)
        
        global jointList
        jointList = []
        
        #register the list of joints for descriptors
        for armature in [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']:
            for bone in armature.data.bones:
                jointList.append(bone.name)
                
        
        return {'FINISHED'}
    
class DeloadOperator(Operator):
    """Tooltip"""
    bl_idname = "load.2"
    bl_label = "Simple Object Operator"

    def execute(self, context):
        
        #Clean the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        global jointList
        jointList = []
        
        return {'FINISHED'}
        
    
class LoadPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Load Panel"
    bl_idname = "OBJECT_PT_load"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SMPL-X+"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.operator(LoadOperator.bl_idname, text="Load")
        row2 = layout.row()
        row2.operator(DeloadOperator.bl_idname, text="Deload")


####### DESCRIPTORS ########

class MyCheckboxItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    value: bpy.props.BoolProperty()


    #### POSITION DESCRIPTOR ####
    
def position(list):
    """Print in the Python console coordonates XYZ of the list of joints inside 'list' """
    obj = bpy.context.object.name        
    armature_obj = bpy.data.objects.get(obj)
    bone_names = {}
    
    #Get the name of the armature
    armature_test = [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']

    #for all joints selected
    for join in list:
        
        ob = bpy.data.objects[armature_test[0].name].pose.bones[join]
        
        world_matrix = armature_obj.matrix_world @ ob.matrix
        world_location = world_matrix.to_translation()
            
        bone_names.update({join:{"x":world_location[0],"y":world_location[1],"z":world_location[2]}})
            
    #print dictionary with joints and their coordonates
    print(bone_names)

class PopUpPosition (bpy.types.Operator):
    """Open a pop Up permitting to select joints run 'position'"""
    
    bl_label = "Position Dialog Box"
    bl_idname = "descript.position"
    
    text = bpy.props.StringProperty(name = "Enter Text", default = "")
    
    def execute(self,context):
        
        #aka the code when the botton is pressed
        selected = [item.name for item in context.scene.my_checkbox_list if item.value]
        position(selected)
        
        return {'FINISHED'}
    
    def invoke(self,context,event):
        
        global jointList
        
        context.scene.my_checkbox_list.clear()
        
        for joint in jointList:
            new_item = context.scene.my_checkbox_list.add()
            new_item.name = joint
            new_item.value = False  # Default unchecked
            
        return context.window_manager.invoke_props_dialog(self, width=300)
           
    def draw(self, context):
        
        global jointList
        layout = self.layout
        
        for item in context.scene.my_checkbox_list:
            layout.prop(item, "value", text=item.name)
        
        
    #### DISTANCE DESCRIPTOR ####
 
def get_items(self, context):
    
    global jointList
    return [(item.upper().replace(" ", "_"), item, f"Select {item}") for item in jointList]

def distance(joint_1, joint_2):
    
    obj = bpy.context.object.name        
    armature_obj = bpy.data.objects.get(obj)
    
    armature_test = [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']
    
    ob_joint1 = bpy.data.objects[armature_test[0].name].pose.bones[joint_1]
    ob_joint2 = bpy.data.objects[armature_test[0].name].pose.bones[joint_2]
        
    world_matrix_j1 = armature_obj.matrix_world @ ob_joint1.matrix
    world_matrix_j2 = armature_obj.matrix_world @ ob_joint2.matrix
    
    world_location_j1 = world_matrix_j1.to_translation()
    world_location_j2 = world_matrix_j2.to_translation()
    
    x = world_location_j1[0] - world_location_j2[0]
    y = world_location_j1[1] - world_location_j2[1]
    z = world_location_j1[2] - world_location_j2[2]
    
    distance = sqrt(sqrt(x**2 + y**2)+z**2)
    
    print("La distance entre les deux jointures est de ",distance, "metre(s)")
    

class PopUpDistance(bpy.types.Operator):
    
    bl_idname = "descript.distance"
    bl_label = "Dropdown Popup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        selected1 = context.scene.my_dropdown_enum1
        selected2 = context.scene.my_dropdown_enum2
        
        #print(selected1.lower())
        #print(selected2.lower())
        
        distance(selected1.lower(), selected2.lower())
        
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "my_dropdown_enum1")
        layout2 = self.layout
        layout2.prop(context.scene, "my_dropdown_enum2")

    ##### SPEED DESCRIPTOR #####
    
    
def distance_frames(joint, frame_start, frame_end):
    """ Return the distance of a joint between two frame"""
    # distance with only start and end, no in between, can't be reliable on long therme
    
    
    obj = bpy.context.object.name        
    armature_obj = bpy.data.objects.get(obj)
    
    armature_test = [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']
    
    ##### INFO AT FRAME_START #######
    
    bpy.data.scenes['Scene'].frame_set(frame_start)
    
    ob_joint_start = bpy.data.objects[armature_test[0].name].pose.bones[joint]
    world_matrix_start = armature_obj.matrix_world @ ob_joint_start.matrix
    world_location_start = world_matrix_start.to_translation()
    
    ##### INFO AT FRAME_END #####
    
    bpy.data.scenes['Scene'].frame_set(frame_end)
    
    ob_joint_end = bpy.data.objects[armature_test[0].name].pose.bones[joint]
    world_matrix_end = armature_obj.matrix_world @ ob_joint_end.matrix
    world_location_end = world_matrix_end.to_translation()
    
    
    #### FINAL CALCULATION ####
    
    
    x = world_location_start[0] - world_location_end[0]
    y = world_location_start[1] - world_location_end[1]
    z = world_location_start[2] - world_location_end[2]
    
    print("total distance meter :",sqrt(sqrt(x**2 + y**2)+z**2))
    
    return sqrt(sqrt(x**2 + y**2)+z**2)


    
def speed(joints, frame_start, frame_end):
    """ Print the  movement speed of a list of joints for a selected period of time"""
    myList = {"Result":{}}
    frames = frame_end - frame_start
    
    if (frames > 0):
        
        time = frames / 30
        print ("time :",time)
        
        for j in joints :
            
            myList["Result"].update({j:str((distance_frames(j, frame_start, frame_end)/time))})
    
    bpy.data.scenes['Scene'].frame_set(0)
    
    print(myList)
    
    

class PopUpSpeed (bpy.types.Operator):
    """Open a pop Up permitting to select joints run 'position'"""
    
    bl_label = "Speed Dialog Box"
    bl_idname = "descript.speed"
    
    def execute(self,context):
        
        frame_start : context.scene.my_frame_start 
        frame_end : context.scene.my_frame_end
        
        selected = [item.name for item in context.scene.my_checkbox_list if item.value]
        
        print("Selected joints:", selected)
        print("Start Frame:", frame_start)
        print("End Frame:", frame_end)
        
        speed(selected, frame_start, frame_end)
        
        return {'FINISHED'}
    
    def invoke(self,context,event):
        
        global jointList
        
        context.scene.my_checkbox_list.clear()
        
        for joint in jointList:
            new_item = context.scene.my_checkbox_list.add()
            new_item.name = joint
            new_item.value = False  # Default unchecked
        
            
        return context.window_manager.invoke_props_dialog(self, width=300)
           
    def draw(self, context):
        
        global jointList
        layout = self.layout
        
        layout.prop(context.scene, "my_frame_start")
        layout.prop(context.scene, "my_frame_end")

        layout.label(text="Select joints:")
        
        for item in context.scene.my_checkbox_list:
            layout.prop(item, "value", text=item.name)



############################


class DescriptorPanel(bpy.types.Panel):
    """Creates a Panel for all descriptors"""
    
    bl_label = "Descriptors Panel"
    bl_idname = "OBJECT_PT_descript"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SMPL-X+"

    def draw(self, context):
        
        layout = self.layout
        obj = context.object
        
        row1 = layout.row()
        row1.operator(PopUpPosition.bl_idname, text="Position")
        row2 = layout.row()
        row2.operator(PopUpDistance.bl_idname, text="Distance")
        row3 = layout.row()
        row3.operator(PopUpSpeed.bl_idname, text="Speed")




###### REGISTER ALL PART OF THE ADD ON #######


from bpy.utils import register_class, unregister_class

_classes = {
    LoadOperator,
    DeloadOperator,
    LoadPanel,
    
    MyCheckboxItem,
    PopUpPosition,
    
    PopUpDistance,
    
    PopUpSpeed,
    
    DescriptorPanel
}

def register():
    for cls in _classes:
        register_class(cls) 
        
    bpy.types.Scene.my_file_path = StringProperty(name="Selected File")   
    bpy.types.Scene.my_frame_start = bpy.props.IntProperty(name="Selected First Frame",default=0, min=0)
    bpy.types.Scene.my_frame_end = bpy.props.IntProperty(name="Selected Last Frame",default=0, min=0)
    
    # Register the collection property
    bpy.types.Scene.my_checkbox_list = bpy.props.CollectionProperty(type=MyCheckboxItem)

    bpy.types.Scene.my_dropdown_enum1 = bpy.props.EnumProperty(
    name="Select 1",
    description="Choose an option",
    items=get_items
    )

    bpy.types.Scene.my_dropdown_enum2 = bpy.props.EnumProperty(
        name="Select 2",
        description="Choose an option",
        items=get_items
    )
    
    


def unregister():
    for cls in _classes:
        unregister_class(cls)
    del bpy.types.Scene.my_file_path
    del bpy.types.Scene.my_checkbox_list
    
    del bpy.types.Scene.my_frame_start
    del bpy.types.Scene.my_frame_end


if __name__ == "__main__":
    register()
