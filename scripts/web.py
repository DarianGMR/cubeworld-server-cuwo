#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Interface Script for cuwo
Sirve la interfaz web con soporte para WebSocket
Basado en matpow2/cuwo-scripts/tree/master/web
"""

import os
import webbrowser
import threading
import json
import asyncio
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
        """Log de peticiones HTTP"""
        print("[WEB] %s" % (format % args))
    
    def end_headers(self):
        """Agregar headers CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_GET(self):
        """Manejar peticiones GET"""
        # Si pide /players.json, devolver datos de jugadores
        if self.path == '/api/players':
            self.handle_players_api()
            return
        # Si pide /chat, devolver historial de chat
        elif self.path == '/api/chat':
            self.handle_chat_api()
            return
        # Para todo lo demas, servir archivos
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
        players = {}
        
        for entity_id, player in server.players.items():
            entity = player.entity
            players[str(entity_id)] = {
                'name': player.name,
                'level': entity.level,
                'klass': entity.class_type,
                'specialz': entity.specialization,
                'hp': int(entity.hp)
            }
        
        response = json.dumps({'response': 'get_players', **players})
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
        """Procesar comandos (kick, ban, etc)"""
        server = self.server.web_server.server
        auth_key = self.server.web_server.auth_key
        
        # Validar autenticacion
        if data.get('key') != auth_key:
            self.send_error(401, "Unauthorized")
            return
        
        request = data.get('request')
        
        if request == 'command_kick':
            player_id = int(data.get('id'))
            reason = data.get('reason', 'No reason specified')
            if player_id in server.players:
                server.players[player_id].kick(reason)
                response = json.dumps({"response": "Success"})
            else:
                response = json.dumps({"response": "Player not found"})
        
        elif request == 'command_ban':
            player_id = int(data.get('id'))
            reason = data.get('reason', 'No reason specified')
            if player_id in server.players:
                player = server.players[player_id]
                ip = player.address[0]
                server.call_scripts('ban', ip, reason)
                response = json.dumps({"response": "Player banned"})
            else:
                response = json.dumps({"response": "Player not found"})
        
        elif request == 'send_message':
            message = data.get('message', '')
            server.send_chat(message)
            response = json.dumps({"response": "Message sent"})
        
        else:
            response = json.dumps({"response": "Unknown request"})
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def handle_chat_post(self, data):
        """Manejar mensajes de chat"""
        server = self.server.web_server.server
        message = data.get('message', '')
        
        if message:
            server.send_chat(message)
            # Guardar en historial
            chat_history = getattr(self.server.web_server, 'chat_history', [])
            chat_history.append({'id': 0, 'name': 'Server', 'message': message})
            if len(chat_history) > 100:
                chat_history.pop(0)
        
        response = json.dumps({"response": "Success"})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))


class WebServer(ServerScript):
    """Script del servidor web para cuwo"""
    
    connection_class = None
    
    def on_load(self):
        """Se ejecuta cuando se carga el script"""
        try:
            # Cargar configuracion
            config = self.server.config.web
            
            web_port = config.port
            web_host = config.host
            auto_open = config.auto_open
            self.auth_key = config.auth_key
            self.chat_history = []
            
            # Verificar carpeta web
            if not os.path.exists(SITE_PATH):
                print("[WEB] ERROR: Carpeta '%s' no encontrada" % SITE_PATH)
                return
            
            # Actualizar init.js con valores de configuracion
            self._update_init_js(web_port, self.auth_key)
            
            # Crear servidor HTTP personalizado
            handler = SiteHTTPRequestHandler
            self.http_server = HTTPServer((web_host, web_port), handler)
            self.http_server.web_server = self
            
            def run_web_server():
                print("[WEB] [OK] Servidor web iniciado en http://%s:%d" % (web_host, web_port))
                print("[WEB] [OK] Interfaz disponible en http://%s:%d" % (web_host, web_port))
                try:
                    self.http_server.serve_forever()
                except:
                    pass
            
            # Iniciar servidor en thread daemon
            web_thread = threading.Thread(target=run_web_server, daemon=True)
            web_thread.start()
            
            # Abrir navegador
            if auto_open:
                self.loop.call_later(1, lambda: self._open_browser(web_host, web_port))
        
        except (OSError, KeyError, AttributeError) as e:
            print("[WEB] ERROR: No se pudo iniciar: %s" % str(e))
    
    def _update_init_js(self, port, auth_key):
        """Actualizar archivo init.js con puerto y clave de autenticacion"""
        try:
            js_path = os.path.join(SITE_PATH, 'js', 'init.js')
            content = 'var server_port = "%d";\nvar auth_key = "%s";\n' % (port, auth_key)
            
            with open(js_path, 'w') as f:
                f.write(content)
            
            print("[WEB] [OK] Configuracion de JavaScript actualizada")
        except Exception as e:
            print("[WEB] WARNING: No se pudo actualizar init.js: %s" % str(e))
    
    def _open_browser(self, host, port):
        """Abrir navegador"""
        try:
            url = "http://%s:%d" % (host, port)
            print("[WEB] [INFO] Abriendo navegador en %s..." % url)
            webbrowser.open(url)
        except Exception as e:
            print("[WEB] WARNING: No se pudo abrir navegador: %s" % str(e))
            print("[WEB] [INFO] Abre manualmente: http://%s:%d" % (host, port))
    
    def on_unload(self):
        """Se ejecuta cuando se descarga el script"""
        try:
            if hasattr(self, 'http_server'):
                self.http_server.shutdown()
                print("[WEB] [OK] Servidor web detenido")
        except:
            pass


def get_class():
    """Funcion requerida por cuwo para cargar el script"""
    return WebServer