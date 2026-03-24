$(document).ready(function () {
    var ClassArray = {"1": "Guerrero", "2": "Ranger", "3": "Mago", "4": "Pícaro"};
    var PlayersArr = {};
    var Specializations = [
        ["Berserker", "Guardian"],
        ["Sniper", "Scout"],
        ["Fire", "Water"],
        ["Assassin", "Ninja"]
    ];
    var refresh_interval = null;
    
    function add_player(data, id) {
        PlayersArr[id] = data;
        var spec = Specializations[data['klass'] - 1][data['specialz']];
        $('table.players tbody').append(
            "<tr data-id=" + id + "><td>" + id + "</td>" +
            "<td>" + data['name'] + "</td>" +
            "<td>" + data['level'] + "</td>" +
            "<td>" + ClassArray[data['klass']] + "</td>" +
            "<td>" + spec + "</td></tr>"
        );
    }
    
    function update_players() {
        $.ajax({
            url: '/api/players',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Borrar jugadores actuales
                $('table.players tbody').html('');
                PlayersArr = {};
                
                // Agregar nuevos
                for (var id in data) {
                    if (id !== 'response' && data[id]['name']) {
                        add_player(data[id], id);
                    }
                }
            },
            error: function() {
                console.log("Error al cargar jugadores");
            }
        });
    }
    
    // Cambiar tabs
    $('ul.nav li').on('click', function() {
        var target_tab = $(this).attr('data-name');
        $('ul.nav > li.current_tab').removeClass('current_tab');
        $(this).addClass('current_tab');
        $('.content_container > div:not(.hidden_tab)').addClass('hidden_tab');
        $('.content_container > div#' + target_tab).removeClass('hidden_tab');
    });
    
    // Actualizar jugadores cada 2 segundos
    refresh_interval = setInterval(update_players, 2000);
    update_players();
    
    // Chat
    $('#chatInput').on('keypress', function(e) {
        if (e.which == 13) {
            var message = $(this).val();
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
                        $('#chatInput').val('');
                        $('#chatMessages').append(
                            '<p><span>Tu:</span> ' + message + '</p>'
                        );
                        $("#chatMessages").scrollTop($("#chatMessages")[0].scrollHeight);
                    }
                });
            }
            return false;
        }
    });
});