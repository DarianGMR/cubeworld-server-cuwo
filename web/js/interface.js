$(document).ready(function () {
    const ClassArray = {
        0: "Sin Clase",
        1: "Guerrero",
        2: "Ranger",
        3: "Mago",
        4: "Pícaro"
    };
    
    const Specializations = [
        ["Berserker", "Guardian"],
        ["Sniper", "Scout"],
        ["Fire", "Water"],
        ["Assassin", "Ninja"]
    ];
    
    let playersData = {};
    let updateInterval = null;
    let selectedPlayerId = null;
    
    // ============= TAB SWITCHING =============
    $('.nav-item').on('click', function(e) {
        e.preventDefault();
        const tabName = $(this).data('tab');
        
        $('.nav-item').removeClass('active');
        $('.tab-content').removeClass('active');
        
        $(this).addClass('active');
        $('#' + tabName).addClass('active');
    });
    
    // ============= MODAL MANAGEMENT =============
    function showModal(modalId) {
        $('#' + modalId).addClass('show');
    }
    
    function hideModal(modalId) {
        $('#' + modalId).removeClass('show');
    }
    
    $('[data-dismiss]').on('click', function() {
        const modalId = $(this).data('dismiss');
        hideModal(modalId);
    });
    
    $(window).on('click', function(event) {
        if (event.target.classList.contains('modal')) {
            $(event.target).removeClass('show');
        }
    });
    
    // ============= CONVERT PLAYTIME =============
    function formatPlaytime(minutes) {
        if (minutes < 60) {
            return minutes + ' min';
        }
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return hours + 'h ' + mins + 'min';
    }
    
    // ============= PLAYERS UPDATE - FIXED VERSION =============
    function updatePlayers() {
        $.ajax({
            url: '/api/players',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                if (!data || !Array.isArray(data.players)) {
                    return;
                }
                
                // En lugar de reemplazar toda la lista, actualizar elementos existentes
                if (data.players.length === 0) {
                    if ($('#playersContainer .player-item').length === 0) {
                        $('#playersContainer').html(`
                            <div class="empty-state">
                                <i class="fas fa-inbox"></i>
                                <p>No hay jugadores conectados</p>
                            </div>
                        `);
                    }
                } else {
                    // Mostrar mensaje vacío solo si está actualmente mostrado
                    const emptyState = $('#playersContainer .empty-state');
                    if (emptyState.length > 0) {
                        emptyState.remove();
                    }
                    
                    // Crear un mapa de jugadores actuales
                    const serverPlayerIds = new Set(data.players.map(p => p.id));
                    
                    // Remover jugadores que ya no están en el servidor
                    $('#playersContainer .player-item').each(function() {
                        const itemPlayerId = $(this).data('player-id');
                        if (!serverPlayerIds.has(itemPlayerId)) {
                            $(this).fadeOut(300, function() {
                                $(this).remove();
                            });
                        }
                    });
                    
                    // Actualizar o agregar jugadores
                    data.players.forEach(player => {
                        playersData[player.id] = player;
                        
                        const className = ClassArray[player.klass] || "Desconocida";
                        const spec = player.klass > 0 && player.klass <= 4 
                            ? Specializations[player.klass - 1][player.specialz] || "Desconocida"
                            : "Desconocida";
                        
                        const playtimeStr = formatPlaytime(player.playtime_minutes || 0);
                        
                        const $existingItem = $(`#playersContainer .player-item[data-player-id="${player.id}"]`);
                        
                        if ($existingItem.length > 0) {
                            // Actualizar elemento existente sin parpadeo
                            $existingItem.find('.player-detail-value').each(function(index) {
                                const $label = $(this).siblings('.player-detail-label');
                                const label = $label.text().toLowerCase();
                                
                                if (label.includes('salud')) {
                                    $(this).text(player.hp + ' HP');
                                } else if (label.includes('especialización')) {
                                    $(this).text(spec);
                                } else if (label.includes('posición')) {
                                    $(this).text(`X:${player.x || 0}`);
                                } else if (label.includes('tiempo')) {
                                    $(this).text(playtimeStr);
                                }
                            });
                        } else {
                            // Crear nuevo elemento
                            const firstLetter = (player.name || "?")[0].toUpperCase();
                            
                            const newItem = `
                                <div class="player-item" data-player-id="${player.id}">
                                    <div class="player-avatar">${firstLetter}</div>
                                    <div class="player-info">
                                        <div class="player-name">${player.name} (ID: ${player.id})</div>
                                        <div class="player-details-row">
                                            <div class="player-detail-item">
                                                <span class="player-detail-label">Clase</span>
                                                <span class="player-detail-value">${className}</span>
                                            </div>
                                            <div class="player-detail-item">
                                                <span class="player-detail-label">Especialización</span>
                                                <span class="player-detail-value">${spec}</span>
                                            </div>
                                            <div class="player-detail-item">
                                                <span class="player-detail-label">Salud</span>
                                                <span class="player-detail-value">${player.hp} HP</span>
                                            </div>
                                            <div class="player-detail-item">
                                                <span class="player-detail-label">Posición</span>
                                                <span class="player-detail-value">X:${player.x || 0}</span>
                                            </div>
                                            <div class="player-detail-item">
                                                <span class="player-detail-label">Tiempo</span>
                                                <span class="player-detail-value">${playtimeStr}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="player-actions">
                                        <button class="btn-action btn-heal" data-player-id="${player.id}" data-action="heal">
                                            <i class="fas fa-heart"></i> Sanar
                                        </button>
                                        <button class="btn-action btn-kick" data-player-id="${player.id}" data-action="kick">
                                            <i class="fas fa-sign-out-alt"></i> Expulsar
                                        </button>
                                        <button class="btn-action btn-ban" data-player-id="${player.id}" data-action="ban">
                                            <i class="fas fa-ban"></i> Banear
                                        </button>
                                    </div>
                                </div>
                            `;
                            
                            $('#playersContainer').append(newItem);
                        }
                    });
                }
                
                $('#playerCount').text(data.count);
                
                // Reattach action handlers para nuevos elementos
                attachPlayerActionHandlers();
                
            },
            error: function() {
                // Error silencioso, reintentar
            }
        });
    }
    
    function attachPlayerActionHandlers() {
        $('.btn-action').off('click').on('click', function(e) {
            e.preventDefault();
            const playerId = $(this).data('player-id');
            const action = $(this).data('action');
            const player = playersData[playerId];
            
            if (!player) return;
            
            if (action === 'heal') {
                healPlayer(playerId, player.name);
            } else if (action === 'kick') {
                selectedPlayerId = playerId;
                $('#kickPlayerName').text('Jugador: ' + player.name);
                $('#kickReason').val('');
                showModal('kickModal');
            } else if (action === 'ban') {
                selectedPlayerId = playerId;
                $('#banPlayerName').text('Jugador: ' + player.name);
                $('#banReason').val('');
                showModal('banModal');
            }
        });
    }
    
    function healPlayer(playerId, playerName) {
        $.ajax({
            url: '/api/command',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                request: 'heal_player',
                player_id: playerId,
                key: auth_key
            }),
            success: function(response) {
                addConsoleMessage('success', `Jugador ${playerName} sanado completamente`);
                // Actualizar la lista de jugadores inmediatamente
                updatePlayers();
            },
            error: function(xhr) {
                addConsoleMessage('error', `Error al sanar a ${playerName}`);
                console.error('Error:', xhr);
            }
        });
    }
    
    $('#kickConfirmBtn').on('click', function() {
        const reason = $('#kickReason').val().trim();
        if (!reason) {
            alert('Por favor, proporciona una razón');
            return;
        }
        
        const player = playersData[selectedPlayerId];
        if (!player) return;
        
        $.ajax({
            url: '/api/command',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                request: 'kick_player',
                player_id: selectedPlayerId,
                reason: reason,
                key: auth_key
            }),
            success: function(response) {
                addConsoleMessage('success', `Jugador ${player.name} expulsado. Razón: ${reason}`);
                hideModal('kickModal');
                updatePlayers();
            },
            error: function(xhr) {
                addConsoleMessage('error', `Error al expulsar a ${player.name}`);
                console.error('Error:', xhr);
            }
        });
    });
    
    $('#banConfirmBtn').on('click', function() {
        const reason = $('#banReason').val().trim();
        if (!reason) {
            alert('Por favor, proporciona una razón');
            return;
        }
        
        const player = playersData[selectedPlayerId];
        if (!player) return;
        
        $.ajax({
            url: '/api/command',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                request: 'ban_player',
                player_id: selectedPlayerId,
                reason: reason,
                key: auth_key
            }),
            success: function(response) {
                addConsoleMessage('success', `Jugador ${player.name} baneado. Razón: ${reason}`);
                hideModal('banModal');
                updatePlayers();
            },
            error: function(xhr) {
                addConsoleMessage('error', `Error al banear a ${player.name}`);
                console.error('Error:', xhr);
            }
        });
    });
    
    // ============= SERVER INFO UPDATE =============
    function updateServerInfo() {
        $.ajax({
            url: '/api/server',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                if (!data) return;
                
                $('#serverPlayers').text(data.players_online + '/' + data.max_players);
                
                const hours = Math.floor(data.uptime / 3600);
                const minutes = Math.floor((data.uptime % 3600) / 60);
                $('#uptime').text(hours + ' horas, ' + minutes + ' minutos');
            },
            error: function() {
                // Error silencioso
            }
        });
    }
    
    // ============= CONSOLE =============
    function addConsoleMessage(type, text) {
        let span = '<span class="console-success">✓</span>';
        if (type === 'error') {
            span = '<span class="console-error">✗</span>';
        } else if (type === 'warning') {
            span = '<span class="console-warning">⚠</span>';
        }
        
        const line = `<div class="console-line">${span} ${text}</div>`;
        $('#consoleOutput').append(line);
        $('#consoleOutput').scrollTop($('#consoleOutput')[0].scrollHeight);
    }
    
    $('#consoleInput').on('keypress', function(e) {
        if (e.which === 13) {
            const command = $(this).val().trim();
            if (command) {
                addConsoleMessage('info', '> ' + command);
                
                $.ajax({
                    url: '/api/command',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        request: 'execute_command',
                        command: command,
                        key: auth_key
                    }),
                    success: function(response) {
                        addConsoleMessage('success', 'Comando ejecutado');
                    },
                    error: function() {
                        addConsoleMessage('error', 'Error al ejecutar comando');
                    }
                });
                
                $(this).val('');
            }
            return false;
        }
    });
    
    $('#clearLogBtn').on('click', function() {
        if (confirm('¿Estás seguro de que deseas limpiar el log?')) {
            $('#consoleOutput').html('<div class="console-line"><span class="console-success">✓</span> Log limpiado</div>');
            
            $.ajax({
                url: '/api/command',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    request: 'clear_log',
                    key: auth_key
                }),
                error: function() {
                    // Error silencioso
                }
            });
        }
    });
    
    // ============= CHAT =============
    $('#chatInput').on('keypress', function(e) {
        if (e.which === 13) {
            const message = $(this).val().trim();
            if (message) {
                $.ajax({
                    url: '/api/command',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        request: 'send_message',
                        message: message,
                        key: auth_key
                    }),
                    success: function() {
                        addChatMessage('cuwo', message, 'user');
                    }
                });
                $(this).val('');
            }
            return false;
        }
    });
    
    $('#chatSendBtn').on('click', function() {
        $('#chatInput').trigger('keypress');
    });
    
    function addChatMessage(author, text, type = 'system') {
        let authorHtml = author;
        if (author === 'cuwo') {
            authorHtml = '<span class="message-author cuwo">cuwo:</span>';
        } else {
            authorHtml = `<span class="message-author">${author}:</span>`;
        }
        
        const messageHtml = `
            <div class="chat-message ${type}">
                ${authorHtml}
                <span class="message-text">${text}</span>
            </div>
        `;
        $('#chatMessages').append(messageHtml);
        $('#chatMessages').scrollTop($('#chatMessages')[0].scrollHeight);
    }
    
    // ============= INITIALIZATION =============
    updatePlayers();
    updateServerInfo();
    
    // Cambiar de 2000ms a 5000ms (5 segundos) y mantener elementos sin parpadeo
    updateInterval = setInterval(() => {
        updatePlayers();
        updateServerInfo();
    }, 5000);
    
    // Clean up on unload
    $(window).on('unload', function() {
        if (updateInterval) {
            clearInterval(updateInterval);
        }
    });
});
