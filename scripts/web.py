#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Interface Script for cuwo
Sirve la interfaz web con soporte para WebSocket
"""

import os
import webbrowser
import threading
import json
import time
import logging
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from cuwo.script import ServerScript

SITE_PATH = 'web'

# Configurar logging para capturar todos los errores
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/web.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class SiteHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Handler para servir archivos desde la carpeta web"""
    
    def translate_path(self, path):
        """Servir desde la carpeta web en lugar de la raiz"""
        translated = super().translate_path(path)
        relpath = os.path.relpath(translated, os.getcwd())
        return os.path.join(os.getcwd(), SITE_PATH, relpath)
    
    def log_message(self, format, *args):
        """Suprimir logs de peticiones HTTP"""
        pass
    
    def end_headers(self):
        """Agregar headers CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_GET(self):
        """Manejar peticiones GET"""
        if self.path == '/api/players':
            self.handle_players_api()
            return
        elif self.path == '/api/chat':
            self.handle_chat_api()
            return
        elif self.path == '/api/server':
            self.handle_server_api()
            return
        super().do_GET()
    
    def do_POST(self):
        """Manejar peticiones POST"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            self.send_error(400, "Invalid JSON")
            return
        
        if self.path == '/api/command':
            self.handle_command(data)
        elif self.path == '/api/chat':
            self.handle_chat_post(data)
        else:
            self.send_error(404, "Not Found")
    
    def handle_players_api(self):
        """Devolver lista de jugadores en JSON con tiempo de juego"""
        server = self.server.web_server.server
        players_list = []
        
        try:
            for connection in server.players.values():
                try:
                    if not hasattr(connection, 'entity') or connection.entity is None:
                        continue
                    
                    if not hasattr(connection, 'name'):
                        continue
                    
                    entity = connection.entity
                    
                    player_id = None
                    if hasattr(entity, 'player_id'):
                        player_id = int(entity.player_id)
                    elif hasattr(connection, 'player_id'):
                        player_id = int(connection.player_id)
                    elif hasattr(entity, 'id'):
                        player_id = int(entity.id)
                    else:
                        player_id = id(connection) % 10000
                    
                    # Calcular tiempo de juego en minutos
                    playtime_minutes = 0
                    if hasattr(connection, 'join_time'):
                        playtime_minutes = int((time.time() - connection.join_time) / 60)
                    elif hasattr(connection, 'playtime'):
                        playtime_minutes = int(connection.playtime / 60)
                    
                    player_data = {
                        'id': player_id,
                        'name': str(connection.name) if connection.name else 'Unknown',
                        'level': int(entity.level) if hasattr(entity, 'level') else 0,
                        'klass': int(entity.class_type) if hasattr(entity, 'class_type') else 0,
                        'specialz': int(entity.specialization) if hasattr(entity, 'specialization') else 0,
                        'hp': int(entity.hp) if hasattr(entity, 'hp') else 0,
                        'max_hp': int(entity.max_hp) if hasattr(entity, 'max_hp') else 100,
                        'x': int(entity.x) if hasattr(entity, 'x') else 0,
                        'y': int(entity.y) if hasattr(entity, 'y') else 0,
                        'z': int(entity.z) if hasattr(entity, 'z') else 0,
                        'playtime_minutes': playtime_minutes
                    }
                    players_list.append(player_data)
                    
                except (AttributeError, TypeError, ValueError) as e:
                    logger.debug(f"Error procesando jugador: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error en handle_players_api: {e}")
        
        response_data = {
            'response': 'get_players',
            'players': players_list,
            'count': len(players_list)
        }
        
        response = json.dumps(response_data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def handle_server_api(self):
        """Devolver información del servidor"""
        server = self.server.web_server.server
        
        try:
            server_data = {
                'response': 'server_info',
                'name': 'Cuwo Server',
                'port': 12345,
                'players_online': len(server.players),
                'max_players': 100,
                'uptime': int(time.time() - self.server.web_server.start_time)
            }
        except Exception as e:
            logger.error(f"Error en handle_server_api: {e}")
            server_data = {
                'response': 'server_info',
                'name': 'Cuwo Server',
                'port': 12345,
                'players_online': 0,
                'max_players': 100,
                'uptime': 0
            }
        
        response = json.dumps(server_data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def handle_chat_api(self):
        """Devolver historial de chat"""
        chat_history = getattr(self.server.web_server, 'chat_history', [])
        response = json.dumps({'response': 'chat_history', 'messages': chat_history})
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def handle_command(self, data):
        """Procesar comandos - AHORA CON EJECUCIÓN REAL"""
        server = self.server.web_server.server
        auth_key = self.server.web_server.auth_key
        
        if data.get('key') != auth_key:
            self.send_error(401, "Unauthorized")
            return
        
        request = data.get('request')
        response_msg = {"response": "Success"}
        
        try:
            if request == 'send_message':
                message = data.get('message', '')
                if message:
                    # Formatear mensaje con prefijo "cuwo:"
                    formatted_msg = f"cuwo: {message}"
                    server.send_chat(formatted_msg)
                    chat_history = getattr(self.server.web_server, 'chat_history', [])
                    chat_history.append({'id': 0, 'name': 'Server', 'message': formatted_msg})
                    if len(chat_history) > 100:
                        chat_history.pop(0)
                    logger.info(f"[CHAT] {formatted_msg}")
                    
            elif request == 'execute_command':
                command = data.get('command', '').strip()
                if command:
                    logger.info(f"[COMANDO] {command}")
                    # Ejecutar comando en el servidor
                    try:
                        server.call_command(None, command.split()[0], command.split()[1:] if len(command.split()) > 1 else [])
                    except Exception as e:
                        logger.warning(f"Error ejecutando comando: {e}")
                    
            elif request == 'heal_player':
                player_id = data.get('player_id')
                if player_id is not None:
                    # Buscar el jugador por ID y curarlo
                    healed = False
                    for connection in server.players.values():
                        try:
                            player_entity_id = None
                            if hasattr(connection, 'entity') and connection.entity:
                                if hasattr(connection.entity, 'player_id'):
                                    player_entity_id = connection.entity.player_id
                                elif hasattr(connection.entity, 'id'):
                                    player_entity_id = connection.entity.id
                            
                            if player_entity_id == player_id or id(connection) % 10000 == player_id:
                                # Curar al jugador al máximo
                                if hasattr(connection.entity, 'hp') and hasattr(connection.entity, 'max_hp'):
                                    connection.entity.hp = connection.entity.max_hp
                                    healed = True
                                    logger.info(f"[ACCIÓN] Jugador {connection.name} (ID: {player_id}) sanado completamente")
                                    server.send_chat(f"{connection.name} ha sido sanado")
                                break
                        except Exception as e:
                            logger.debug(f"Error curando jugador: {e}")
                    
                    if not healed:
                        logger.warning(f"No se pudo encontrar al jugador con ID {player_id}")
                    
                    response_msg["success"] = healed
                    
            elif request == 'kick_player':
                player_id = data.get('player_id')
                reason = data.get('reason', 'Sin especificar')
                if player_id is not None:
                    # Buscar el jugador por ID y expulsarlo
                    kicked = False
                    for connection in list(server.players.values()):
                        try:
                            player_entity_id = None
                            if hasattr(connection, 'entity') and connection.entity:
                                if hasattr(connection.entity, 'player_id'):
                                    player_entity_id = connection.entity.player_id
                                elif hasattr(connection.entity, 'id'):
                                    player_entity_id = connection.entity.id
                            
                            if player_entity_id == player_id or id(connection) % 10000 == player_id:
                                # Expulsar al jugador
                                connection.kick(reason)
                                kicked = True
                                logger.info(f"[EXPULSIÓN] Jugador {connection.name} (ID: {player_id}) expulsado. Razón: {reason}")
                                break
                        except Exception as e:
                            logger.debug(f"Error expulsando jugador: {e}")
                    
                    if not kicked:
                        logger.warning(f"No se pudo encontrar al jugador con ID {player_id}")
                    
                    response_msg["success"] = kicked
                    
            elif request == 'ban_player':
                player_id = data.get('player_id')
                reason = data.get('reason', 'Sin especificar')
                if player_id is not None:
                    # Buscar el jugador por ID y banearlo
                    banned = False
                    for connection in list(server.players.values()):
                        try:
                            player_entity_id = None
                            if hasattr(connection, 'entity') and connection.entity:
                                if hasattr(connection.entity, 'player_id'):
                                    player_entity_id = connection.entity.player_id
                                elif hasattr(connection.entity, 'id'):
                                    player_entity_id = connection.entity.id
                            
                            if player_entity_id == player_id or id(connection) % 10000 == player_id:
                                # Banear al jugador por IP
                                player_ip = connection.address[0]
                                
                                # Llamar a la función ban del script de bans si existe
                                try:
                                    for script in server.scripts.scripts.values():
                                        if hasattr(script, 'parent') and hasattr(script.parent, 'ban'):
                                            script.parent.ban(player_ip, reason)
                                            banned = True
                                            logger.info(f"[BANEO] Jugador {connection.name} (IP: {player_ip}) baneado. Razón: {reason}")
                                            break
                                except:
                                    pass
                                
                                # Si no se pudo usar el script de ban, al menos lo expulsamos
                                if not banned:
                                    connection.kick(reason)
                                    banned = True
                                    logger.info(f"[BANEO] Jugador {connection.name} expulsado (intento de baneo). Razón: {reason}")
                                break
                        except Exception as e:
                            logger.debug(f"Error baneando jugador: {e}")
                    
                    if not banned:
                        logger.warning(f"No se pudo encontrar al jugador con ID {player_id}")
                    
                    response_msg["success"] = banned
                    
            elif request == 'clear_log':
                logger.info("[LOG] Log limpiado por admin")
                
        except Exception as e:
            logger.error(f"Error procesando comando: {e}")
            response_msg["success"] = False
        
        response = json.dumps(response_msg)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def handle_chat_post(self, data):
        """Manejar mensajes de chat"""
        self.handle_command(data)


class WebServer(ServerScript):
    """Script del servidor web para cuwo"""
    
    connection_class = None
    
    def on_load(self):
        """Se ejecuta cuando se carga el script"""
        try:
            self.start_time = time.time()
            config = self.server.config.web
            
            web_port = config.port
            web_host = config.host
            auto_open = config.auto_open
            self.auth_key = config.auth_key
            self.chat_history = []
            
            if not os.path.exists(SITE_PATH):
                logger.error(f"Carpeta '{SITE_PATH}' no encontrada")
                return
            
            self._update_init_js(web_port, self.auth_key)
            
            handler = SiteHTTPRequestHandler
            self.http_server = HTTPServer((web_host, web_port), handler)
            self.http_server.web_server = self
            
            def run_web_server():
                logger.info(f"Panel web disponible en http://{web_host}:{web_port}")
                try:
                    self.http_server.serve_forever()
                except Exception as e:
                    logger.error(f"Error en servidor web: {e}")
            
            web_thread = threading.Thread(target=run_web_server, daemon=True)
            web_thread.start()
            
            if auto_open:
                self.loop.call_later(1, lambda: self._open_browser(web_host, web_port))
        
        except Exception as e:
            logger.error(f"Error inicializando servidor web: {e}")
    
    def _update_init_js(self, port, auth_key):
        """Actualizar archivo init.js"""
        try:
            js_path = os.path.join(SITE_PATH, 'js', 'init.js')
            content = f'var server_port = "{port}";\nvar auth_key = "{auth_key}";\n'
            with open(js_path, 'w') as f:
                f.write(content)
            logger.info("Archivo init.js actualizado")
        except Exception as e:
            logger.warning(f"No se pudo actualizar init.js: {e}")
    
    def _open_browser(self, host, port):
        """Abrir navegador"""
        try:
            url = f"http://{host}:{port}"
            logger.info(f"Abriendo navegador en {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"No se pudo abrir navegador: {e}")
    
    def on_unload(self):
        """Se ejecuta cuando se descarga el script"""
        try:
            if hasattr(self, 'http_server'):
                self.http_server.shutdown()
                logger.info("Servidor web detenido")
        except Exception as e:
            logger.error(f"Error deteniendo servidor web: {e}")


def get_class():
    return WebServer
