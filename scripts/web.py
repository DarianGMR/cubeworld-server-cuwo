#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Interface Script for cuwo
Sirve la interfaz web con soporte para administración
"""

import os
import webbrowser
import threading
import json
import time
import logging
import sys
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from cuwo.script import ServerScript, ConnectionScript

SITE_PATH = 'web'
PLAYTIME_DATA_NAME = 'web_playtimes'

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/web.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class WebConnectionScript(ConnectionScript):
    """Script para trackear tiempo de conexión de jugadores"""
    
    def on_join(self, event):
        """Se ejecuta cuando un jugador entra al servidor"""
        self.connection.web_join_time = time.time()
        logger.info(f"Registrado join_time para {self.connection.name}")
    
    def on_unload(self):
        """Guardar tiempo de juego cuando el jugador se desconecta"""
        try:
            if hasattr(self.connection, 'web_join_time') and self.connection.name:
                playtime_data = self.server.load_data(PLAYTIME_DATA_NAME, {})
                player_name = self.connection.name.lower()
                
                # Calcular tiempo de juego en segundos
                playtime_seconds = int(time.time() - self.connection.web_join_time)
                
                # Si el jugador ya tenía tiempo registrado, sumarle
                if player_name in playtime_data:
                    playtime_data[player_name] += playtime_seconds
                else:
                    playtime_data[player_name] = playtime_seconds
                
                self.server.save_data(PLAYTIME_DATA_NAME, playtime_data)
                logger.info(f"Guardado tiempo de juego para {self.connection.name}: {playtime_data[player_name]} segundos")
        except Exception as e:
            logger.error(f"Error guardando tiempo de juego: {e}\n{traceback.format_exc()}")


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
        elif self.path == '/api/bans':
            self.handle_bans_api()
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
        """Devolver lista de jugadores en JSON"""
        server = self.server.web_server.server
        players_list = []
        current_time = time.time()
        
        # Cargar datos de playtime persistentes
        playtime_data = server.load_data(PLAYTIME_DATA_NAME, {})
        
        try:
            for connection in list(server.players.values()):
                try:
                    if not hasattr(connection, 'entity') or connection.entity is None:
                        continue
                    
                    if not hasattr(connection, 'name') or not connection.name:
                        continue
                    
                    entity = connection.entity
                    
                    # Usar ID simple basado en la conexión
                    player_id = id(connection) % 10000
                    
                    # Calcular tiempo de juego en minutos
                    playtime_minutes = 0
                    if hasattr(connection, 'web_join_time'):
                        session_playtime = int((current_time - connection.web_join_time) / 60)
                        player_name_lower = connection.name.lower()
                        previous_playtime = int(playtime_data.get(player_name_lower, 0) / 60)
                        playtime_minutes = session_playtime + previous_playtime
                    
                    player_data = {
                        'id': player_id,
                        'name': str(connection.name) if connection.name else 'Unknown',
                        'ip': connection.address[0],
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
            logger.error(f"Error en handle_players_api: {e}\n{traceback.format_exc()}")
        
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
    
    def handle_bans_api(self):
        """Devolver lista de IPs baneadas"""
        server = self.server.web_server.server
        
        try:
            # Acceder al script de ban correctamente
            ban_script = None
            for item in server.scripts.items.values():
                if hasattr(item, 'banned_ips'):
                    ban_script = item
                    break
            
            if ban_script and hasattr(ban_script, 'banned_ips'):
                bans_list = []
                for ip, reason in ban_script.banned_ips.items():
                    bans_list.append({
                        'ip': ip,
                        'reason': reason
                    })
                
                response_data = {
                    'response': 'ban_list',
                    'bans': bans_list,
                    'count': len(bans_list)
                }
            else:
                response_data = {
                    'response': 'ban_list',
                    'bans': [],
                    'count': 0
                }
        except Exception as e:
            logger.error(f"Error en handle_bans_api: {e}\n{traceback.format_exc()}")
            response_data = {
                'response': 'ban_list',
                'bans': [],
                'count': 0
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
            logger.error(f"Error en handle_server_api: {e}\n{traceback.format_exc()}")
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
    
    def find_player_by_id(self, server, player_id):
        """Encontrar un jugador por su ID"""
        try:
            for connection in list(server.players.values()):
                if id(connection) % 10000 == player_id:
                    return connection
        except Exception as e:
            logger.debug(f"Error en find_player_by_id: {e}")
        
        return None
    
    def handle_command(self, data):
        """Procesar comandos desde la web"""
        server = self.server.web_server.server
        auth_key = self.server.web_server.auth_key
        
        if data.get('key') != auth_key:
            self.send_error(401, "Unauthorized")
            return
        
        request = data.get('request')
        response_msg = {"response": "Success", "success": False, "error": None}
        
        try:
            if request == 'send_message':
                message = data.get('message', '')
                if message:
                    formatted_msg = f"cuwo: {message}"
                    server.send_chat(formatted_msg)
                    chat_history = getattr(self.server.web_server, 'chat_history', [])
                    chat_history.append({'id': 0, 'name': 'Server', 'message': formatted_msg})
                    if len(chat_history) > 100:
                        chat_history.pop(0)
                    logger.info(f"[CHAT] {formatted_msg}")
                    response_msg["success"] = True
                    
            elif request == 'execute_command':
                command = data.get('command', '').strip()
                if command:
                    logger.info(f"[COMANDO] {command}")
                    try:
                        server.call_command(None, command.split()[0], command.split()[1:] if len(command.split()) > 1 else [])
                        response_msg["success"] = True
                    except Exception as e:
                        logger.error(f"Error ejecutando comando: {e}\n{traceback.format_exc()}")
                        response_msg["success"] = False
                        response_msg["error"] = str(e)
                    
            elif request == 'heal_player':
                player_id = data.get('player_id')
                if player_id is not None:
                    connection = self.find_player_by_id(server, player_id)
                    if connection:
                        try:
                            if hasattr(connection, 'entity') and connection.entity:
                                entity = connection.entity
                                if hasattr(entity, 'damage'):
                                    entity.damage(-1000)
                                    response_msg["success"] = True
                                    logger.info(f"[HEAL] Jugador {connection.name} (ID: {player_id}) sanado")
                                    server.send_chat(f"{connection.name} ha sido sanado")
                                else:
                                    response_msg["error"] = "Entidad sin método damage()"
                            else:
                                response_msg["error"] = "Conexión sin entidad"
                        except Exception as e:
                            response_msg["error"] = str(e)
                            logger.error(f"Error curando jugador: {e}\n{traceback.format_exc()}")
                    else:
                        response_msg["error"] = f"Jugador con ID {player_id} no encontrado"
                    
            elif request == 'kick_player':
                player_id = data.get('player_id')
                reason = data.get('reason', 'Sin especificar')
                if player_id is not None:
                    connection = self.find_player_by_id(server, player_id)
                    if connection:
                        try:
                            connection.kick(reason)
                            response_msg["success"] = True
                            logger.info(f"[KICK] Jugador {connection.name} (ID: {player_id}) expulsado. Razón: {reason}")
                        except Exception as e:
                            response_msg["error"] = str(e)
                            logger.error(f"Error expulsando jugador: {e}\n{traceback.format_exc()}")
                    else:
                        response_msg["error"] = f"Jugador con ID {player_id} no encontrado"
                    
            elif request == 'ban_player':
                player_id = data.get('player_id')
                reason = data.get('reason', 'Sin especificar')
                
                logger.info(f"[BAN REQUEST] Player ID: {player_id}, Reason: {reason}")
                
                if player_id is not None:
                    connection = self.find_player_by_id(server, player_id)
                    if connection:
                        try:
                            player_name = connection.name
                            player_ip = connection.address[0]
                            
                            logger.info(f"[BAN] Encontrado jugador: {player_name} con IP: {player_ip}")
                            
                            # Acceder al script de ban correctamente
                            ban_script = None
                            for item in server.scripts.items.values():
                                if hasattr(item, 'ban_ip'):
                                    ban_script = item
                                    logger.info(f"[BAN] Script de ban encontrado")
                                    break
                            
                            if ban_script:
                                # Banear la IP usando el script de ban
                                logger.info(f"[BAN] Baneando IP {player_ip}")
                                ban_script.ban_ip(player_ip, reason)
                                response_msg["success"] = True
                                logger.info(f"[BAN] IP {player_ip} del jugador {player_name} baneada. Razón: {reason}")
                                server.send_chat(f"IP {player_ip} ha sido baneada")
                            else:
                                response_msg["error"] = "Script de ban no encontrado"
                                logger.error("[BAN] Script de ban no encontrado en los scripts cargados")
                                    
                        except Exception as e:
                            response_msg["error"] = str(e)
                            logger.error(f"Error baneando jugador: {e}\n{traceback.format_exc()}")
                    else:
                        response_msg["error"] = f"Jugador con ID {player_id} no encontrado"
                        logger.warning(f"[BAN] Jugador con ID {player_id} no encontrado")
                else:
                    response_msg["error"] = "ID de jugador no proporcionado"
                    logger.warning("[BAN] ID de jugador no proporcionado")
                    
            elif request == 'clear_log':
                logger.info("[LOG] Log limpiado por admin")
                response_msg["success"] = True
                
        except Exception as e:
            response_msg["error"] = str(e)
            logger.error(f"Error procesando comando {request}: {e}\n{traceback.format_exc()}")
        
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
    
    connection_class = WebConnectionScript
    
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
                    logger.error(f"Error en servidor web: {e}\n{traceback.format_exc()}")
            
            web_thread = threading.Thread(target=run_web_server, daemon=True)
            web_thread.start()
            
            if auto_open:
                self.loop.call_later(1, lambda: self._open_browser(web_host, web_port))
        
        except Exception as e:
            logger.error(f"Error inicializando servidor web: {e}\n{traceback.format_exc()}")
    
    def _update_init_js(self, port, auth_key):
        """Actualizar archivo init.js"""
        try:
            js_path = os.path.join(SITE_PATH, 'js', 'init.js')
            content = f'var server_port = "{port}";\nvar auth_key = "{auth_key}";\n'
            with open(js_path, 'w') as f:
                f.write(content)
            logger.info("Archivo init.js actualizado")
        except Exception as e:
            logger.warning(f"No se pudo actualizar init.js: {e}\n{traceback.format_exc()}")
    
    def _open_browser(self, host, port):
        """Abrir navegador"""
        try:
            url = f"http://{host}:{port}"
            logger.info(f"Abriendo navegador en {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"No se pudo abrir navegador: {e}\n{traceback.format_exc()}")
    
    def on_unload(self):
        """Se ejecuta cuando se descarga el script"""
        try:
            if hasattr(self, 'http_server'):
                self.http_server.shutdown()
                logger.info("Servidor web detenido")
        except Exception as e:
            logger.error(f"Error deteniendo servidor web: {e}\n{traceback.format_exc()}")


def get_class():
    return WebServer
