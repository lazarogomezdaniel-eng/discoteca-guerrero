# 🛡️ FICHA TÉCNICA E INSTRUCCIONES DE INTEGRACIÓN DEL ASSET 3D: GUERRERO
**Documento para el Agente Antigravity de Desarrollo de Videojuegos (Godot 4 / Web Three.js)**

---

## 1. Identificación y Especificaciones del Archivo
* **Nombre del archivo principal:** `guerrero_completo_84_animaciones_rootmotion.glb`
* **Formato:** glTF 2.0 Binary (`.glb`)
* **Peso:** ~13.2 MB (altamente optimizado, 1 sola petición de carga)
* **Escala:** 1.80 metros de altura (escala métrica real 1:1, Y-up)
* **Malla principal:** `Solid_Guerrero` (Malla única consolidada, ~79.5k triángulos / 85.7k vértices, materiales PBR con texturas integradas)
* **Esqueleto (Rig):** `Armature` estándar ActionForge con **71 huesos** nativos.
* **Características de armadura:** Hombreras rígidas con cabezas de dragón y placas de coraza no deformables (0% distorsión o aplastamiento en rotaciones extremas).
* **Animaciones integradas:** **84 clips nativos** empaquetados dentro del mismo archivo `.glb`.

> **Nota:** Si tu arquitectura de juego requiere animaciones estáticas en el sitio (sin desplazamiento físico del hueso raíz), existe también el gemelo exacto: `guerrero_completo_84_animaciones_inplace.glb`.

---

## 2. Jerarquía de Nodos del Modelo
Al instanciar el `.glb`, la estructura de nodos es:
```text
guerrero (Node3D / Scene)
└── Armature
    ├── Skeleton3D (71 huesos, raíz = "root")
    ├── Solid_Guerrero (MeshInstance3D / SkinnedMesh)
    └── AnimationPlayer (84 animaciones precargadas)
```

---

## 3. ¿Cómo Funciona el Root Motion en este Archivo?
El hueso raíz se llama **`root`** (hueso padre de `pelvis`).
* En las animaciones de locomoción (`walk_loop_fit`, `sprint_loop_fit`, etc.), ataques de avance (`sword_dash_fit`, `sword_heavy_combo_fit`) y evasiones (`roll_fit`, `slide_loop_fit`), el hueso `root` traslada sus coordenadas físicas en el espacio 3D.
* **En Godot 4:** El motor debe configurarse para extraer el movimiento de este hueso y transferirlo al `CharacterBody3D`, evitando deslizamiento de pies (*foot sliding*).

---

## 4. Guía de Integración para Godot 4 (`CharacterBody3D`)

### A. Configuración de Importación en Godot
1. Arrastra `guerrero_completo_84_animaciones_rootmotion.glb` al panel `FileSystem` de Godot.
2. Selecciona el archivo y ve al panel **Import** (arriba a la izquierda):
   * Verifica que en *Animation* -> *Import* esté activado.
   * Haz clic en **Reimport**.
3. Clic derecho en el archivo `.glb` ➔ **New Inherited Scene**. Guárdala como `Guerrero.tscn`.

### B. Configuración con `AnimationTree` y Root Motion
Para que el personaje se mueva impulsado por la animación:
1. Agrega un nodo **`AnimationTree`** como hijo de `Guerrero`.
2. Asigna la propiedad `Anim Player` a tu nodo `AnimationPlayer`.
3. En la propiedad **`Root Motion Track`**, selecciona la pista del hueso raíz:
   `Armature/Skeleton3D:root` (o `..:root`).
4. Selecciona un `Tree Root` de tipo **`AnimationNodeStateMachine`**.

### C. Script GDScript de Ejemplo (`Guerrero.gd`)
```gdscript
extends CharacterBody3D

@onready var anim_tree: AnimationTree = $AnimationTree
@onready var state_machine: AnimationNodeStateMachinePlayback = anim_tree.get("parameters/playback")
@onready var skeleton: Skeleton3D = $Armature/Skeleton3D

var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")

func _ready():
    anim_tree.active = true
    state_machine.travel("idle_loop_fit")

func _physics_process(delta):
    # Aplicar gravedad si no está en el suelo
    if not is_on_floor():
        velocity.y -= gravity * delta

    # 1. Leer desplazamiento del Root Motion de la animación actual
    var root_motion_pos = anim_tree.get_root_motion_position()
    var root_motion_rot = anim_tree.get_root_motion_rotation()

    # 2. Aplicar rotación del root motion
    quaternion *= root_motion_rot

    # 3. Orientar y aplicar la velocidad horizontal usando el vector del root motion
    var velocity_horizontal = (quaternion * root_motion_pos) / delta
    velocity.x = velocity_horizontal.x
    velocity.z = velocity_horizontal.z

    # 4. Inputs del jugador para cambiar de estado
    var input_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    if input_dir != Vector2.ZERO:
        if Input.is_action_pressed("sprint"):
            state_machine.travel("sprint_loop_fit")
        else:
            state_machine.travel("walk_loop_fit")
        
        # Rotar al personaje hacia la dirección de la cámara / entrada
        var target_rot = atan2(input_dir.x, input_dir.y)
        rotation.y = lerp_angle(rotation.y, target_rot, delta * 10.0)
    else:
        state_machine.travel("idle_loop_fit")

    # Botones de acción
    if Input.is_action_just_pressed("attack"):
        state_machine.travel("sword_regular_combo_fit")
    elif Input.is_action_just_pressed("roll"):
        state_machine.travel("roll_fit")

    move_and_slide()
```

---

## 5. Guía de Integración para Juego Web (Three.js / WebGL)

Si el juego se desarrolla para navegador web:
```javascript
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
let mixer, actions = {}, activeAction;

loader.load('guerrero_completo_84_animaciones_rootmotion.glb', (gltf) => {
  const model = gltf.scene;
  scene.add(model);

  mixer = new THREE.AnimationMixer(model);

  // Mapear los 84 clips disponibles
  gltf.animations.forEach((clip) => {
    actions[clip.name] = mixer.clipAction(clip);
  });

  // Función para transicionar entre animaciones con suavizado cruzado (crossfade)
  function transitionTo(clipName, duration = 0.3) {
    const nextAction = actions[clipName];
    if (!nextAction || nextAction === activeAction) return;

    if (activeAction) activeAction.fadeOut(duration);
    nextAction.reset().fadeIn(duration).play();
    activeAction = nextAction;
  }

  // Iniciar en reposo
  transitionTo('idle_loop_fit', 0.0);
});

function animate(delta) {
  if (mixer) mixer.update(delta);
}
```

---

## 6. Diccionario Completo de las 84 Animaciones Disponibles
Usa exactamente estos nombres de string al llamar a `play()` o `travel()`:

### 🚶 Locomoción
* `walk_loop_fit` - Caminata estándar con paso firme
* `walk_formal_loop_fit` - Caminata marcial / guardia militar
* `walk_carry_loop_fit` - Caminar transportando caja u objeto pesado
* `jog_fwd_loop_fit` - Trote continuo moderado
* `sprint_loop_fit` - Carrera rápida a máxima velocidad
* `crouch_fwd_loop_fit` - Caminar en sigilo agachado
* `crouch_idle_loop_fit` - Reposo en postura agachada
* `zombie_walk_fwd_loop_fit` - Paso monstruoso / zombificado
* `swim_fwd_loop_fit` - Nado hacia adelante
* `swim_idle_loop_fit` - Flotación acuática estática

### ⚔️ Combate con Espada & Escudo
* `sword_idle_fit` - Guardia táctica de espada
* `sword_attack_fit` - Corte básico con espada
* `sword_regular_a_fit` - Ataque ligero combo 1 (Corte A)
* `sword_regular_a_rec_fit` - Recuperación tras Corte A
* `sword_regular_b_fit` - Ataque ligero combo 2 (Corte B)
* `sword_regular_b_rec_fit` - Recuperación tras Corte B
* `sword_regular_c_fit` - Ataque final ligero (Corte C)
* `sword_regular_combo_fit` - Secuencia completa de combo triple
* `sword_heavy_combo_fit` - Gran combo de ataque pesado con salto
* `sword_dash_fit` - Embestida cortante con impulso frontal
* `sword_block_fit` - Bloqueo / Parada con arma
* `idle_shield_loop_fit` - Guardia defensiva con escudo alzado
* `shield_dash_fit` - Carga de choque con escudo
* `shield_oneshot_fit` - Golpe contundente de escudo frontal
* `idle_shield_break_fit` - Reacción a rotura de guardia / escudo

### 🥊 Combate Cuerpo a Cuerpo
* `punch_jab_fit` - Puñetazo directo rápido (Jab)
* `punch_cross_fit` - Puñetazo de potencia cruzado (Cross)
* `melee_hook_fit` - Gancho potente (Hook)
* `melee_hook_rec_fit` - Recuperación de postura tras gancho

### 🤸 Saltos, Acrobacias y Parkour
* `jump_start_fit` - Impulso de despegue de salto
* `jump_loop_fit` - Suspensión en el aire
* `jump_land_fit` - Aterrizaje firme amortiguado
* `ninjajump_start_fit` - Salto mortal ninja acrobático
* `ninjajump_idle_loop_fit` - Suspensión acrobática de salto ninja
* `ninjajump_land_fit` - Aterrizaje ninja posado
* `roll_fit` - Voltereta de evasión en el suelo (Dodge Roll)
* `slide_start_fit` - Inicio de deslizamiento por el suelo
* `slide_loop_fit` - Deslizamiento activo
* `slide_exit_fit` - Incorporación tras deslizamiento
* `climbup_1m_fit` - Trepar obstáculo o repisa de 1 metro

### 🧍 Reposo y Poses (Idles)
* `idle_loop_fit` - Reposo natural con respiración sutil
* `idle_foldarms_loop_fit` - Brazos cruzados en postura desafiante
* `idle_torch_loop_fit` - Sostener antorcha encendida en mano
* `idle_lantern_loop_fit` - Sostener farol o linterna
* `idle_talking_loop_fit` - Gesto de conversación informal
* `idle_talkingphone_loop_fit` - Hablar por auricular / comunicador
* `idle_no_loop_fit` - Gesto rotundo de negación con cabeza y manos
* `idle_rail_loop_fit` - Apoyado en barandilla o muro bajo
* `idle_rail_call_fit` - Llamar a alguien desde la barandilla
* `zombie_idle_loop_fit` - Reposo de criatura bestial

### 💥 Daño y Reacciones
* `hit_chest_fit` - Retroceso por impacto en el pecho
* `hit_head_fit` - Sacudida por golpe en la cabeza
* `hit_knockback_fit` - Impacto fuerte con pérdida de equilibrio
* `death01_fit` - Caída dramática y colapso al suelo
* `laytoidle_fit` - Levantarse desde el suelo tras caída

### 🕺 Baile y Celebración
* `dance_loop_fit` - Danza rítmica de batalla sincronizable a música
* `yes_fit` - Celebración triunfal con puño alzado

### 🔫 Armas de Fuego
* `pistol_idle_loop_fit` - Guardia con arma corta
* `pistol_aim_neutral_fit` - Apuntado neutral frontal
* `pistol_aim_up_fit` - Apuntado en ángulo superior
* `pistol_aim_down_fit` - Apuntado en ángulo inferior
* `pistol_shoot_fit` - Disparo con retroceso en brazos
* `pistol_reload_fit` - Extracción y recarga de cargador

### 🔮 Magia y Hechizos
* `spell_simple_enter_fit` - Postura inicial de invocación
* `spell_simple_idle_loop_fit` - Concentración de energía arcana
* `spell_simple_shoot_fit` - Proyección y disparo de hechizo
* `spell_simple_exit_fit` - Disipación de energía mágica

### 🧰 Interacciones con el Entorno
* `chest_open_fit` - Apertura de cofre o baúl
* `pickup_table_fit` - Recoger objeto de superficie
* `consume_fit` - Beber de frasco / poción
* `push_loop_fit` - Empujar elemento pesado
* `fixing_kneeling_fit` - Reparación de rodillas con herramienta
* `sitting_enter_fit` - Transición a sentarse
* `sitting_idle_loop_fit` - Reposo sentado
* `sitting_talking_loop_fit` - Conversación mientras está sentado
* `sitting_exit_fit` - Ponerse de pie desde asiento
* `driving_loop_fit` - Postura de conducción de montura o vehículo
* `treechopping_loop_fit` - Talar con hacha a dos manos
* `overhandthrow_fit` - Lanzamiento de granada o proyectil
* `interact_fit` - Pulsar botón, interruptor o palanca
* `farm_harvest_fit` - Cosechar cultivo
* `farm_plantseed_fit` - Plantar semilla
* `farm_watering_fit` - Regar cultivos
* `zombie_scratch_fit` - Ataque de arañazo salvaje
