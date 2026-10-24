"""
Script Maestro de Renderizado en Cycles GPU (Google Colab)
Construye el escenario de concierto de alta gama, importa el Guerrero con sus 71 huesos
y anima las 4 tomas cinematográficas con trazado de rayos fotorrealista.
"""

import bpy
import mathutils
import math
import os

# 1. Limpiar escena predeterminada
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 450
scene.render.fps = 30

# 2. Configurar motor Cycles con GPU (OptiX / CUDA)
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences

print("--- Configurando GPU en Cycles ---")
for dev_type in ['OPTIX', 'CUDA']:
    try:
        prefs.compute_device_type = dev_type
        prefs.get_devices()
        gpu_found = False
        for d in prefs.devices:
            if d.type in ['CUDA', 'OPTIX']:
                d.use = True
                gpu_found = True
                print(f"Activada GPU {d.name} con {dev_type}")
        if gpu_found:
            scene.cycles.device = 'GPU'
            break
    except Exception as e:
        print(f"Info {dev_type}: {e}")

scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'

# Configuración de salida MP4 Full HD con audio
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.audio_bitrate = 192
video_out = os.path.abspath('videoclip_guerrero_cine_colab.mp4')
scene.render.filepath = video_out

# 3. Importar el modelo GLB con todas las texturas PBR y animación de 71 huesos
glb_path = os.path.abspath('guerrero_baile_motion.glb')
print(f"Importando modelo desde: {glb_path}...")
bpy.ops.import_scene.gltf(filepath=glb_path)

# Buscar armature y personaje
armature = None
warrior_mesh = None
for obj in scene.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH' and 'Guerrero' in obj.name:
        warrior_mesh = obj

# Asignar animación tecktonik al armature
if armature and bpy.data.actions:
    dance_action = bpy.data.actions.get('tecktonik_dance_real') or bpy.data.actions[0]
    if not armature.animation_data:
        armature.animation_data_create()
    armature.animation_data.action = dance_action
    print(f"Animación asignada: {dance_action.name}")

# Activar suavizado perfecto en la malla
if warrior_mesh:
    for p in warrior_mesh.data.polygons:
        p.use_smooth = True

# 4. Construir Escenario de Concierto
# A. Pista de Obsidiana Pulida (Reflectante)
bpy.ops.mesh.primitive_cylinder_add(radius=5.0, depth=0.1, vertices=64, location=(0, 0, -0.05))
floor = bpy.context.active_object
floor.name = 'Club_Floor'
mat_floor = bpy.data.materials.new('Mat_Floor')
mat_floor.use_nodes = True
bsdf_floor = mat_floor.node_tree.nodes.get('Principled BSDF')
if bsdf_floor:
    bsdf_floor.inputs['Base Color'].default_value = (0.015, 0.02, 0.035, 1.0)
    bsdf_floor.inputs['Metallic'].default_value = 0.90
    bsdf_floor.inputs['Roughness'].default_value = 0.12
floor.data.materials.append(mat_floor)

# B. Anillo Neón Cian
bpy.ops.mesh.primitive_cylinder_add(radius=4.8, depth=0.02, vertices=64, location=(0, 0, 0.01))
ring = bpy.context.active_object
ring.name = 'Neon_Ring'
mat_ring = bpy.data.materials.new('Mat_Ring')
mat_ring.use_nodes = True
bsdf_ring = mat_ring.node_tree.nodes.get('Principled BSDF')
if bsdf_ring:
    bsdf_ring.inputs['Emission Color'].default_value = (0.0, 0.95, 1.0, 1.0)
    bsdf_ring.inputs['Emission Strength'].default_value = 5.0
ring.data.materials.append(mat_ring)

# C. Pantalla LED Gigante de Fondo (Visual Waves)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 4.2, 2.7))
led = bpy.context.active_object
led.name = 'LED_Screen'
led.scale = (9.5, 5.2, 1.0)
led.rotation_euler = (math.pi / 2, 0, 0)

mat_led = bpy.data.materials.new('Mat_LED')
mat_led.use_nodes = True
nodes = mat_led.node_tree.nodes
links = mat_led.node_tree.links
bsdf_led = nodes.get('Principled BSDF')

wave_node = nodes.new('ShaderNodeTexWave')
wave_node.wave_type = 'BANDS'
wave_node.bands_direction = 'DIAGONAL'
wave_node.inputs['Scale'].default_value = 4.0
wave_node.inputs['Distortion'].default_value = 8.0

ramp_node = nodes.new('ShaderNodeValToRGB')
ramp_node.color_ramp.elements[0].position = 0.15
ramp_node.color_ramp.elements[0].color = (0.05, 0.01, 0.1, 1.0)
ramp_node.color_ramp.elements[1].position = 0.85
ramp_node.color_ramp.elements[1].color = (0.97, 0.14, 0.52, 1.0) # Magenta neon
e3 = ramp_node.color_ramp.elements.new(0.5)
e3.color = (0.0, 0.95, 1.0, 1.0) # Cian neon

links.new(wave_node.outputs['Color'], ramp_node.inputs['Fac'])
links.new(ramp_node.outputs['Color'], bsdf_led.inputs['Base Color'])
links.new(ramp_node.outputs['Color'], bsdf_led.inputs['Emission Color'])
bsdf_led.inputs['Emission Strength'].default_value = 3.5
led.data.materials.append(mat_led)

# D. Focos de Concierto
# Foco frontal suave
key_light = bpy.data.lights.new('Key_Light', type='SPOT')
key_light.energy = 550.0
key_light.spot_size = math.radians(45)
key_light.spot_blend = 0.4
key_obj = bpy.data.objects.new('Key_Light', key_light)
key_obj.location = (0, -3.2, 2.5)
key_obj.rotation_euler = (math.radians(55), 0, 0)
scene.collection.objects.link(key_obj)

# Focos cenitales cian y magenta
spot_l = bpy.data.lights.new('Spot_Left', type='SPOT')
spot_l.color = (0.0, 0.95, 1.0)
spot_l.energy = 850.0
spot_l.spot_size = math.radians(35)
obj_sl = bpy.data.objects.new('Spot_Left', spot_l)
obj_sl.location = (-2.8, 1.2, 4.8)
obj_sl.rotation_euler = (math.radians(-45), math.radians(25), 0)
scene.collection.objects.link(obj_sl)

spot_r = bpy.data.lights.new('Spot_Right', type='SPOT')
spot_r.color = (0.97, 0.14, 0.52)
spot_r.energy = 850.0
spot_r.spot_size = math.radians(35)
obj_sr = bpy.data.objects.new('Spot_Right', spot_r)
obj_sr.location = (2.8, 1.2, 4.8)
obj_sr.rotation_euler = (math.radians(-45), math.radians(-25), 0)
scene.collection.objects.link(obj_sr)

# Fondo oscuro
world = bpy.data.worlds.new('Concert_World')
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value = (0.015, 0.01, 0.025, 1.0)
    bg.inputs['Strength'].default_value = 0.3
scene.world = world

# 5. Cámara de Cine con Animación de 4 Tomas
cam_data = bpy.data.cameras.new('Cinema_Camera')
cam_data.dof.use_dof = True
cam_data.dof.focus_object = warrior_mesh
cam_data.dof.aperture_fstop = 2.8

cam_obj = bpy.data.objects.new('Cinema_Camera', cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def set_cam_kf(frame, loc, target, lens):
    scene.frame_set(frame)
    cam_obj.location = mathutils.Vector(loc)
    direction = mathutils.Vector(target) - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    cam_obj.data.lens = lens
    
    cam_obj.keyframe_insert(data_path='location', frame=frame)
    cam_obj.keyframe_insert(data_path='rotation_euler', frame=frame)
    cam_obj.data.keyframe_insert(data_path='lens', frame=frame)

print("Programando las 4 tomas cinematográficas...")
# Toma 1: Pedestal Heroico (1 - 114)
set_cam_kf(1, (0.25, -3.5, 0.40), (0.0, 0.0, 1.25), 38)
set_cam_kf(114, (-0.15, -3.2, 1.20), (0.0, 0.0, 1.35), 40)

# Toma 2: Primer plano dedos y rostro (115 - 228)
set_cam_kf(115, (0.95, -2.1, 1.50), (0.0, 0.0, 1.48), 52)
set_cam_kf(228, (-0.95, -2.1, 1.50), (0.0, 0.0, 1.48), 52)

# Toma 3: Travelling lateral footwork (229 - 342)
set_cam_kf(229, (-2.8, -3.2, 1.10), (0.0, 0.0, 1.25), 38)
set_cam_kf(342, (2.8, -3.2, 1.15), (0.0, 0.0, 1.25), 38)

# Toma 4: Clímax y retranqueo del escenario (343 - 450)
set_cam_kf(343, (0.0, -2.6, 1.35), (0.0, 0.0, 1.30), 45)
set_cam_kf(450, (0.0, -4.6, 1.55), (0.0, 0.0, 1.20), 34)

# 6. Sincronizar audio en el editor de secuencias
audio_file = os.path.abspath('beat_baile.wav')
if os.path.exists(audio_file):
    scene.sequence_editor_create()
    scene.sequence_editor.sequences.new_sound('Beat1', audio_file, 1, 1)
    scene.sequence_editor.sequences.new_sound('Beat2', audio_file, 1, 193)
    scene.sequence_editor.sequences.new_sound('Beat3', audio_file, 1, 385)
    print("Pista de audio sincronizada.")

# 7. Ejecutar Render
print(f"--- Iniciando renderizado de 450 fotogramas en Cycles GPU ---")
bpy.ops.render.render(animation=True)
print("--- ¡RENDERIZADO COMPLETADO CON ÉXITO! ---")
