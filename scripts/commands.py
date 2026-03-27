"""
Conjunto de comandos predeterminado incluido con cuwo
"""

from cuwo.script import ServerScript, command, admin, alias
from cuwo.common import get_chunk
from cuwo import constants
from cuwo import static
from cuwo.vector import vec3, qvec3
import platform

MAX_STUN_TIME = 1000 * 60  # 60 segundos en milisegundos


class CommandServer(ServerScript):
    pass


def get_class():
    return CommandServer


@command
@admin
def say(script, *message):
    """Envia un mensaje global al servidor."""
    message = ' '.join(message)
    script.server.send_chat(message)
    return f"Mensaje enviado: {message}"


@command
def server(script):
    """Devuelve informacion sobre la plataforma del servidor."""
    msg = 'El servidor se esta ejecutando %r' % platform.system()
    revision = script.server.git_rev
    if revision is not None:
        msg += ', revision %s' % revision
    return msg


@command
def login(script, password):
    """Inicia sesion con la contraseña especificada."""
    password = password.lower()
    user_types = script.server.passwords.get(password, [])
    if not user_types:
        return 'Contraseña no valida'
    script.connection.rights.update(user_types)
    return 'Iniciado sesion como %s' % (', '.join(user_types))


@command
def help(script, name=None):
    """Devuelve informacion sobre los comandos."""
    if name is None:
        commands = sorted([item.name for item in script.get_commands()])
        return 'Comandos: ' + ', '.join(commands)
    else:
        command = script.get_command(name)
        if command is None:
            return 'No existe tal comando'
        return command.get_help()


@command
@admin
def kick(script, name, *reason):
    """expulsa al jugador especificado."""
    reason = ' '.join(reason) or 'No se especifica ningun motivo'
    player = script.get_player(name)
    player.kick(reason)
    return f"Jugador {player.name} expulsado. Razón: {reason}"


@command
@admin
def setclock(script, value):
    """Establece la hora del dia. Formato: hh:mm."""
    try:
        script.server.set_clock(value)
    except ValueError:
        return 'Reloj especificado no valido'
    return 'Reloj configurado en %s' % value


@command
def whereis(script, name=None):
    """Muestra donde esta un jugador en el mundo."""
    player = script.get_player(name)
    if player is script.connection:
        message = 'estas en %s'
    else:
        message = '%s esta en %%s' % player.name
    return message % (get_chunk(player.position),)


@command
def pm(script, name, *message):
    """Envia un mensaje privado a un jugador."""
    player = script.get_player(name)
    message = ' '.join(message)
    player.send_chat('%s (PM): %s' % (script.connection.name, message))
    return 'PM enviado'


@command
@admin
def kill(script, name=None):
    """Mata a un jugador."""
    player = script.get_player(name)
    player.entity.kill()
    message = '%s fue asesinado' % player.name
    print(message)
    script.server.send_chat(message)
    return message


@command
@admin
def stun(script, name, milliseconds=1000):
    """Aturde a un jugador por un tiempo especifico."""
    
    # Limita el tiempo de aturdimiento, ya que valores demasiado altos pueden provocar que el servidor falle.
    # Ademas, prohibe los valores negativos por si acaso.
    try:
        milliseconds = int(milliseconds)  # Convertir a int para evitar error con str
    except ValueError:
        return f"Error: El tiempo debe ser un número, recibido: {milliseconds}"
    
    milliseconds = abs(milliseconds)
    if milliseconds > MAX_STUN_TIME:
        err = 'El tiempo de aturdimiento es demasiado largo. Por favor, especifique un valor inferior a %d..'
        return err % MAX_STUN_TIME
    
    player = script.get_player(name)
    player.entity.damage(stun_duration=int(milliseconds))
    message = '%s fue aturdido' % player.name
    print(message)
    script.server.send_chat(message)
    return message


@command
@admin
def heal(script, name=None, hp=1000):
    """Cura a un jugador en una cantidad especifica."""
    player = script.get_player(name)
    player.entity.damage(-int(hp))
    message = '%s fue sanado' % player.name
    return message


def who_where(script, include_where):
    server = script.server
    player_count = len(server.players)
    if player_count == 0:
        return 'No hay jugadores conectados'
    formatted_names = []
    for player in list(server.players.values()):
        name = '%s #%s' % (player.name, player.entity_id)
        if include_where:
            name += ' %s' % (get_chunk(player.position),)
        formatted_names.append(name)
    noun = 'jugador' if player_count == 1 else 'jugadores'
    msg = '%s %s conectado: ' % (player_count, noun)
    msg += ', '.join(formatted_names)
    return msg


@command
def who(script):
    """Lista de jugadores."""
    return who_where(script, False)


@command
def whowhere(script):
    """Enumera a los jugadores y sus ubicaciones."""
    return who_where(script, True)


@command
def player(script, name):
    """Devuelve informacion sobre un jugador."""
    player = script.get_player(name)
    entity = player.entity
    typ = entity.class_type
    klass = constants.CLASS_NAMES[typ]
    spec = constants.CLASS_SPECIALIZATIONS[typ][entity.specialization]
    level = entity.level
    return '%r es un nivel %s %s (%s)' % (player.name, level, klass, spec)


@command
@admin
def addrights(script, player, *rights):
    """Otorga derechos a un usuario."""
    player = script.get_player(player)
    rights = set(rights) & player.rights
    player.rights.update(rights)
    if rights:
        rights = ', '.join((repr(right) for right in rights))
    else:
        rights = 'no'
    return '%s derechos otorgados a %r' % (rights, player.name)


@command
@admin
def removerights(script, player, *rights):
    """Elimina los derechos de un usuario."""
    player = script.get_player(player)
    rights = set(rights) & player.rights
    player.rights.difference_update(rights)
    if rights:
        rights = ', '.join((repr(right) for right in rights))
    else:
        rights = 'no'
    return '%s derechos eliminados de %r' % (rights, player.name)


@command
def rights(script, player=None):
    """Muestra los derechos de un usuario."""
    player = script.get_player(player)
    rights = player.rights
    if rights:
        rights = ', '.join((repr(right) for right in player.rights))
    else:
        rights = 'no'
    return '%r tiene %s derechos' % (player.name, rights)


@command
@admin
def sound(script, name):
    """Reproduce un sonido global."""
    try:
        script.server.play_sound(name)
        return f"Sonido '{name}' reproducido"
    except KeyError:
        return 'No hay tal sonido'


def create_teleport_packet(pos, chunk_pos, user_id):
    packet = static.StaticEntityPacket()
    header = static.StaticEntityHeader()
    packet.header = header
    packet.chunk_x = chunk_pos[0]
    packet.chunk_y = chunk_pos[1]
    packet.entity_id = 0
    header.set_type('Bench')
    header.size = vec3(0, 0, 0)
    header.closed = True
    header.orientation = static.ORIENT_SOUTH
    header.pos = pos
    header.time_offset = 0
    header.something8 = 0
    header.user_id = user_id
    return packet


@command
@admin
@alias('t')
def teleport(script, a, b=None, c=None):
    """Teletransportate a un chunk o jugador."""
    entity = script.connection.entity

    if b is None:
        # teletransportarse al jugador
        player = script.get_player(a)
        pos = player.entity.pos
    elif c is None:
        # teletransportarse al chunk
        pos = qvec3(int(a), int(b), 0) * constants.CHUNK_SCALE
        pos.z = script.world.get_height(pos.xy) or entity.pos.z
    else:
        # teletransportarse a la posicion
        pos = qvec3(int(a), int(b), int(c))

    update_packet = script.server.update_packet
    chunk = script.connection.chunk

    packet = create_teleport_packet(pos, chunk.pos, entity.entity_id)
    update_packet.static_entities.append(packet)

    def send_reset_packet():
        if chunk.static_entities:
            chunk.static_entities[0].update()
        else:
            packet = create_teleport_packet(pos, chunk.pos, 0)
            update_packet.static_entities.append(packet)

    script.loop.call_later(0.1, send_reset_packet)


@command
@admin
def load(script, name):
    """Carga un script en tiempo de ejecucion."""
    name = str(name)
    if name in script.server.scripts:
        return 'El script %r ya esta activado' % name
    script.server.load_script(name)
    return 'Script %r activado' % name


@command
@admin
def unload(script, name):
    """Desactiva un script en tiempo de ejecucion."""
    name = str(name)
    if not script.server.unload_script(name):
        return 'El script %r no esta activado' % name
    return 'Script %r desactivado' % name


@command
@admin
def reload(script, name):
    """Recarga un script en tiempo de ejecucion."""
    name = str(name)
    if not script.server.unload_script(name):
        return 'El script %r no esta activado.' % name
    script.server.load_script(name, update=True)
    return 'Script %r recargado' % name


@command
def scripts(script):
    """Muestra los scripts cargados actualmente."""
    return 'Scripts: ' + ', '.join(script.server.scripts.items)
