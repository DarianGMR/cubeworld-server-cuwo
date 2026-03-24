# Copyright (c) Mathias Kaerlev 2013-2017.
#
# This file is part of cuwo.
#
# cuwo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cuwo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cuwo.  If not, see <http://www.gnu.org/licenses/>.

"""
Player versus player mode with command-based activation!
Allows players to opt-in to PvP with the /pvp command
"""

from cuwo.script import ServerScript, ConnectionScript, command
from cuwo.constants import HOSTILE_FLAG
import time


class PvPConnection(ConnectionScript):
    def on_load(self):
        # Inicializar variables de PvP
        self.pvp_enabled = False
        self.pvp_activation_time = 0
        self.pvp_cooldown_duration = 600  # 10 minutos en segundos
        self.original_hostile_type = None

    def on_join(self, event):
        # Por defecto, el jugador es amistoso (hostile_type = 3)
        self.original_hostile_type = self.entity.hostile_type
        self.entity.flags &= ~HOSTILE_FLAG

    def on_hit(self, event):
        # Controlar quién puede atacar a quién
        target = event.target
        
        # Si el atacante no tiene PvP activado, bloquear el golpe
        if not self.pvp_enabled:
            return False
        
        # Si el objetivo no tiene conexión, bloquear (es NPC/mob)
        if not hasattr(target, 'connection') or target.connection is None:
            return False
        
        # Buscar el script PvP del objetivo
        target_script = None
        for script in target.connection.scripts.items.values():
            if isinstance(script, PvPConnection):
                target_script = script
                break
        
        # Si el objetivo no tiene PvP activado, bloquear el golpe
        if target_script is None or not target_script.pvp_enabled:
            return False
        
        # Si ambos tienen PvP activado, permitir el golpe
        return True

    def on_kill(self, event):
        # Mensaje cuando alguien muere
        self.server.send_chat('%s fue asesinado por %s!' % (event.target.name,
                                                             self.entity.name))


class PvPServer(ServerScript):
    connection_class = PvPConnection

    def get_mode(self, event):
        return 'pvp'


# IMPORTANTE: get_class() DEBE estar ANTES de @command
def get_class():
    return PvPServer


# Comando PvP
@command
def pvp(script):
    """Activa o desactiva PvP. Espera 10 min entre activacion y desactivacion"""
    
    connection = script.connection
    
    # Encontrar el script de PvP de este jugador
    pvp_script = None
    for s in connection.scripts.items.values():
        if isinstance(s, PvPConnection):
            pvp_script = s
            break
    
    if pvp_script is None:
        return 'Error: PvP script not found'
    
    current_time = time.time()
    
    # SI PvP está ACTIVADO
    if pvp_script.pvp_enabled:
        # Verificar si ya pasaron 10 minutos desde que se ACTIVÓ
        time_since_activation = current_time - pvp_script.pvp_activation_time
        
        if time_since_activation < pvp_script.pvp_cooldown_duration:
            remaining = int(pvp_script.pvp_cooldown_duration - time_since_activation)
            minutes = remaining // 60
            seconds = remaining % 60
            return 'PvP activo. Debes esperar %d:%02d para desactivarlo' % (minutes, seconds)
        
        # Desactivar PvP (ya pasaron 10 minutos)
        pvp_script.pvp_enabled = False
        pvp_script.entity.flags &= ~HOSTILE_FLAG
        
        # Restaurar al estado original
        if pvp_script.original_hostile_type is not None:
            pvp_script.entity.hostile_type = pvp_script.original_hostile_type
        else:
            pvp_script.entity.hostile_type = 3  # Por defecto amistoso
        
        pvp_script.entity.full_update = True
        script.server.send_chat('[%s] ha DESACTIVADO el PvP!' % connection.name)
        return 'PvP DESACTIVADO'
    
    # SI PvP está DESACTIVADO
    else:
        # Activar PvP y guardar el tiempo de activación
        pvp_script.pvp_enabled = True
        pvp_script.pvp_activation_time = current_time
        
        # Cambiar a hostile_type = 1 (enemigo/rojo)
        # Esto hace que muestre barra de vida roja y nombre rojo
        pvp_script.entity.hostile_type = 1
        
        # Activar el HOSTILE_FLAG para que el servidor permita ataques
        pvp_script.entity.flags |= HOSTILE_FLAG
        
        # Forzar actualización completa
        pvp_script.entity.full_update = True
        
        # Hacer que TODOS los jugadores vean el cambio inmediatamente
        script.server.send_entity_data(pvp_script.entity)
        
        script.server.send_chat('[%s] ha ACTIVADO el PvP! Espera 10 minutos para desactivarlo' % connection.name)
        return 'PvP ACTIVADO - Debes esperar 10 minutos para desactivarlo'