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
from http.server import HTTPServer, SimpleHTTPRequestHandler
from cuwo.script import ServerScript

SITE_PATH = 'web'


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
        """Devolver lista de jugadores en JSON - CORREGIDO"""
        server = self.server.web_server.server
        players_list = []
        
        try:
            # server.players es un diccionario donde:
            # - Clave: objeto CubeWorldConnection
            # - Valor: objeto de conexión también (o el mismo objeto)
            # Necesitamos acceder al atributo entity de cada conexión
            
            for connection in server.players.values():
                try:
                    # Verificar que tiene los atributos requeridos
                    if not hasattr(connection, 'entity') or connection.entity is None:
                        continue
                    
                    if not hasattr(connection, 'name'):
                        continue
                    
                    entity = connection.entity
                    
                    # Extraer ID - intentar de varias formas
                    player_id = None
                    if hasattr(entity, 'player_id'):
                        player_id = int(entity.player_id)
                    elif hasattr(connection, 'player_id'):
                        player_id = int(connection.player_id)
                    elif hasattr(entity, 'id'):
                        player_id = int(entity.id)
                    else:
                        # Si no hay ID, usar el hash del objeto como ID temporal
                        player_id = id(connection) % 10000
                    
                    player_data = {
                        'id': player_id,
                        'name': str(connection.name) if connection.name else 'Unknown',
                        'level': int(entity.level) if hasattr(entity, 'level') else 0,
                        'klass': int(entity.class_type) if hasattr(entity, 'class_type') else 0,
                        'specialz': int(entity.specialization) if hasattr(entity, 'specialization') else 0,
                        'hp': int(entity.hp) if hasattr(entity, 'hp') else 0,
                        'x': int(entity.x) if hasattr(entity, 'x') else 0,
                        'y': int(entity.y) if hasattr(entity, 'y') else 0,
                        'z': int(entity.z) if hasattr(entity, 'z') else 0
                    }
                    players_list.append(player_data)
                    
                except (AttributeError, TypeError, ValueError):
                    continue
                    
        except Exception as e:
            pass
        
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
        except:
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
        """Procesar comandos"""
        server = self.server.web_server.server
        auth_key = self.server.web_server.auth_key
        
        if data.get('key') != auth_key:
            self.send_error(401, "Unauthorized")
            return
        
        request = data.get('request')
        response = json.dumps({"response": "Success"})
        
        if request == 'send_message':
            message = data.get('message', '')
            if message:
                server.send_chat(message)
                chat_history = getattr(self.server.web_server, 'chat_history', [])
                chat_history.append({'id': 0, 'name': 'Server', 'message': message})
                if len(chat_history) > 100:
                    chat_history.pop(0)
        
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
                print("[WEB] ERROR: Carpeta '%s' no encontrada" % SITE_PATH)
                return
            
            self._update_init_js(web_port, self.auth_key)
            
            handler = SiteHTTPRequestHandler
            self.http_server = HTTPServer((web_host, web_port), handler)
            self.http_server.web_server = self
            
            def run_web_server():
                print("[WEB] [OK] Panel web disponible en http://%s:%d" % (web_host, web_port))
                try:
                    self.http_server.serve_forever()
                except:
                    pass
            
            web_thread = threading.Thread(target=run_web_server, daemon=True)
            web_thread.start()
            
            if auto_open:
                self.loop.call_later(1, lambda: self._open_browser(web_host, web_port))
        
        except Exception as e:
            print("[WEB] ERROR: %s" % str(e))
    
    def _update_init_js(self, port, auth_key):
        """Actualizar archivo init.js"""
        try:
            js_path = os.path.join(SITE_PATH, 'js', 'init.js')
            content = 'var server_port = "%d";\nvar auth_key = "%s";\n' % (port, auth_key)
            with open(js_path, 'w') as f:
                f.write(content)
        except:
            pass
    
    def _open_browser(self, host, port):
        """Abrir navegador"""
        try:
            url = "http://%s:%d" % (host, port)
            webbrowser.open(url)
        except:
            pass
    
    def on_unload(self):
        """Se ejecuta cuando se descarga el script"""
        try:
            if hasattr(self, 'http_server'):
                self.http_server.shutdown()
        except:
            pass


def get_class():
    return WebServer
