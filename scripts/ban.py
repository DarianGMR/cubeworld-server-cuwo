"""
Ban management - Banea solo por IP
El comando /ban banea la IP del jugador
"""

from cuwo.script import ServerScript, ConnectionScript, command, admin

SELF_BANNED_IP = 'Tu IP está baneada: {reason}'
IP_BANNED = 'IP {ip} ha sido baneada (Razón: {reason}). Jugador {name} desconectado.'
DEFAULT_REASON = 'Sin motivo especificado'

IP_BAN_DATA = 'banlist_ips'


class BanConnectionScript(ConnectionScript):
    """Script de conexión para verificar ban de IP"""
    pass


class BanServer(ServerScript):
    connection_class = BanConnectionScript
    
    def on_load(self):
        """Cargar lista de IPs baneadas"""
        self.banned_ips = self.server.load_data(IP_BAN_DATA, {})

    def save_bans(self):
        """Guardar lista de IPs baneadas"""
        self.server.save_data(IP_BAN_DATA, self.banned_ips)

    def ban_ip(self, ip, reason):
        """Banea una IP"""
        self.banned_ips[ip] = reason
        self.save_bans()
        
        banned_players = []
        # Desconectar jugadores de esa IP
        for connection in self.server.connections.copy():
            if connection.address[0] != ip:
                continue
            
            name = connection.name
            if name is not None:
                connection.send_chat(SELF_BANNED_IP.format(reason=reason))
            connection.disconnect()
            banned_players.append(connection)
            
            if name is not None:
                message = IP_BANNED.format(ip=ip, reason=reason, name=name)
                print(message)
                self.server.send_chat(message)
        
        return banned_players

    def unban_ip(self, ip):
        """Desbanea una IP"""
        try:
            self.banned_ips.pop(ip)
            self.save_bans()
            return True
        except KeyError:
            return False

    def is_ip_banned(self, ip):
        """Verifica si una IP está baneada"""
        return ip in self.banned_ips

    def get_ban_reason(self, ip):
        """Obtiene la razón del ban de una IP"""
        return self.banned_ips.get(ip, DEFAULT_REASON)

    def on_connection_attempt(self, event):
        """Verifica si la IP está baneada ANTES de conectar"""
        ip = event.address[0]
        
        if ip in self.banned_ips:
            reason = self.banned_ips[ip]
            return SELF_BANNED_IP.format(reason=reason)
        
        return None


def get_class():
    return BanServer


@command
@admin
def ban(script, name, *reason):
    """Banea la IP de un jugador. Uso: /ban (nombre_jugador) (razón)"""
    reason_str = ' '.join(reason) or DEFAULT_REASON
    
    # Encontrar el jugador por nombre
    player = script.get_player(name)
    if player is None:
        return f'No se encontró al jugador "{name}"'
    
    # Obtener IP del jugador
    ip = player.address[0]
    player_name = player.name
    
    # Banear la IP
    script.parent.ban_ip(ip, reason_str)
    
    return f'IP {ip} del jugador "{player_name}" baneada correctamente. Razón: {reason_str}'


@command
@admin
def unban(script, ip):
    """Desbanea una IP. Uso: /unban (IP)"""
    if script.parent.unban_ip(ip):
        return f'IP "{ip}" desbaneada exitosamente'
    else:
        return f'IP "{ip}" no encontrada en la lista de baneados'


@command
@admin
def banlist(script):
    """Muestra la lista de IPs baneadas"""
    if not script.parent.banned_ips:
        return 'No hay IPs baneadas'
    
    ban_list = []
    for ip, reason in script.parent.banned_ips.items():
        ban_list.append(f'{ip}: {reason}')
    
    message = f'IPs baneadas ({len(ban_list)}): ' + ' | '.join(ban_list)
    return message
