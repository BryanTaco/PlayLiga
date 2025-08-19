/**
 * Admin Panel Management System - Versión Corregida
 * Soluciona problemas de simulación de partidos
 */

class AdminPanel {
    constructor() {
        this.data = {
            teams: [],
            matches: [],
            players: [],
            referees: []
        };
        
        this.apiEndpoints = {
            teams: '/torneo/api/equipos/',
            addTeam: '/torneo/api/agregar_equipo/',
            teamDetail: (id) => `/torneo/api/equipo/${id}/`,
            matches: '/torneo/api/partidos/',
            createMatch: '/torneo/api/crear_partido/',
            matchDetail: (id) => `/torneo/api/partido/${id}/`,
            simulateMatch: (id) => `/torneo/api/partido/${id}/simular/`,
            players: '/torneo/api/jugadores/',
            assignPlayer: '/torneo/api/asignar_jugador/',
            referees: '/torneo/api/arbitros/',
            csrfToken: '/torneo/api/csrf-token/'
        };
        
        this.init();
    }

    async init() {
        console.log('Inicializando AdminPanel...');
        this.showLoading(true);
        this.bindEvents();
        try {
            await this.loadData();
            this.setupValidations();
            this.showAlert('Panel cargado correctamente', 'success');
        } catch (error) {
            console.error('Error de inicialización:', error);
            this.showAlert('Error al inicializar el panel: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    bindEvents() {
        // Formulario de equipos
        const teamForm = document.getElementById('form-team');
        if (teamForm) {
            teamForm.addEventListener('submit', (e) => this.handleTeamForm(e));
        }
        
        // Formulario de partidos
        const matchForm = document.getElementById('form-match');
        if (matchForm) {
            matchForm.addEventListener('submit', (e) => this.handleMatchForm(e));
        }

        // Formulario de asignación de jugadores
        const assignForm = document.getElementById('form-player');
        if (assignForm) {
            assignForm.addEventListener('submit', (e) => this.handleAssignPlayerForm(e));
        }

        // Botón de logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                window.location.href = '/torneo/logout/';
            });
        }
    }

    setupValidations() {
        const homeTeamSelect = document.getElementById('home-team');
        const awayTeamSelect = document.getElementById('away-team');
        
        const validateTeamSelection = () => {
            if (homeTeamSelect.value && awayTeamSelect.value && 
                homeTeamSelect.value === awayTeamSelect.value) {
                awayTeamSelect.setCustomValidity('Debe seleccionar un equipo diferente al local');
            } else {
                awayTeamSelect.setCustomValidity('');
            }
        };
        
        homeTeamSelect?.addEventListener('change', validateTeamSelection);
        awayTeamSelect?.addEventListener('change', validateTeamSelection);
        
        // Configurar fecha mínima para partidos
        const matchDateInput = document.getElementById('match-date');
        if (matchDateInput) {
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            matchDateInput.min = now.toISOString().slice(0, 16);
        }
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.classList.toggle('hidden', !show);
        }
    }

    showAlert(message, type = 'info') {
        const container = document.getElementById('alerts-container');
        if (!container) {
            console.warn('Alert container not found');
            return;
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        
        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        const icon = iconMap[type] || 'info-circle';
        
        alert.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    async makeRequest(url, options = {}) {
        try {
            const csrfToken = this.getCookie('csrftoken');
            const headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                ...options.headers
            };

            console.log(`Haciendo petición a: ${url}`);
            console.log('Opciones:', { ...options, headers });

            const response = await fetch(url, {
                ...options,
                headers
            });

            console.log(`Respuesta de ${url}:`, response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Error HTTP ${response.status}:`, errorText);
                throw new Error(`Error HTTP ${response.status}: ${errorText}`);
            }

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const jsonData = await response.json();
                console.log('Datos JSON recibidos:', jsonData);
                return jsonData;
            } else {
                const textData = await response.text();
                console.log('Datos de texto recibidos:', textData);
                return textData;
            }
        } catch (error) {
            console.error('Error en makeRequest:', error);
            throw error;
        }
    }

    async loadData() {
        this.showLoading(true);
        try {
            console.log('Cargando datos desde la API...');
            
            const [teamsResp, matchesResp, playersResp, refereesResp] = await Promise.all([
                this.makeRequest(this.apiEndpoints.teams),
                this.makeRequest(this.apiEndpoints.matches),
                this.makeRequest(this.apiEndpoints.players),
                this.makeRequest(this.apiEndpoints.referees)
            ]);

            this.data = {
                teams: teamsResp || [],
                matches: matchesResp || [],
                players: playersResp || [],
                referees: refereesResp || []
            };

            console.log('Datos cargados:', this.data);
            this.updateUI();
        } catch (error) {
            console.error('Error cargando datos:', error);
            this.showAlert('Error al cargar los datos del servidor: ' + error.message, 'error');
            throw error;
        } finally {
            this.showLoading(false);
        }
    }

    updateUI() {
        this.updateStats();
        this.updateSelects();
        this.updateTeamsList();
        this.updateMatchesList();
    }

    updateStats() {
        const elements = {
            'stat-teams': this.data.teams.length,
            'stat-matches': this.data.matches.length,
            'stat-players': this.data.players.length,
            'stat-referees': this.data.referees.length
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    updateSelects() {
        this.updateTeamSelects();
        this.updatePlayerSelect();
        this.updateRefereeSelect();
    }

    updateTeamSelects() {
        const teamSelects = [
            { id: 'home-team', placeholder: 'Seleccione equipo local' },
            { id: 'away-team', placeholder: 'Seleccione equipo visitante' },
            { id: 'team', placeholder: 'Seleccione equipo' }
        ];

        teamSelects.forEach(({ id, placeholder }) => {
            const select = document.getElementById(id);
            if (!select) return;

            select.innerHTML = `<option value="">${placeholder}</option>`;
            
            this.data.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.nombre;
                select.appendChild(option);
            });
        });
    }

    updatePlayerSelect() {
        const select = document.getElementById('player');
        if (!select) return;

        select.innerHTML = '<option value="">Seleccione jugador</option>';
        
        this.data.players.forEach(player => {
            const option = document.createElement('option');
            option.value = player.id;
            option.textContent = `${player.nombre} ${player.apellido}`;
            select.appendChild(option);
        });
    }

    updateRefereeSelect() {
        const select = document.getElementById('referee');
        if (!select) return;

        select.innerHTML = '<option value="">Seleccione árbitro</option>';
        
        this.data.referees.forEach(referee => {
            const option = document.createElement('option');
            option.value = referee.id;
            option.textContent = `${referee.nombre} ${referee.apellido}`;
            select.appendChild(option);
        });
    }

    updateTeamsList() {
        const container = document.getElementById('vista-equipos');
        if (!container) {
            console.error('Contenedor de equipos no encontrado');
            return;
        }
        
        if (this.data.teams.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <p>No hay equipos registrados</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        this.data.teams.forEach(team => {
            const teamDiv = document.createElement('div');
            teamDiv.className = 'data-item';
            
            const playersText = team.jugadores && team.jugadores.length > 0 
                ? team.jugadores.map(p => `${p.nombre} ${p.apellido}`).join(', ')
                : 'Sin jugadores asignados';
            
            teamDiv.innerHTML = `
                <div class="data-item-info">
                    <div class="data-item-title">${this.escapeHtml(team.nombre)}</div>
                    <div class="data-item-subtitle">${this.escapeHtml(playersText)}</div>
                </div>
                <div class="data-item-actions">
                    <button class="btn btn-secondary" onclick="adminPanel.editTeam(${team.id})">
                        <i class="fas fa-edit"></i>
                        Editar
                    </button>
                    <button class="btn btn-danger" onclick="adminPanel.deleteTeam(${team.id})">
                        <i class="fas fa-trash"></i>
                        Eliminar
                    </button>
                </div>
            `;
            
            container.appendChild(teamDiv);
        });
    }

    updateMatchesList() {
        const container = document.getElementById('vista-partidos');
        if (!container) {
            console.error('Contenedor de partidos no encontrado');
            return;
        }
        
        if (this.data.matches.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar"></i>
                    <p>No hay partidos programados</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        this.data.matches.forEach(match => {
            const matchDiv = document.createElement('div');
            matchDiv.className = 'data-item';
            
            const matchDate = new Date(match.fecha).toLocaleString('es-ES');
            
            // Determinar si el partido ya fue simulado
            const hasResult = match.simulado;
            const resultText = hasResult ? 
                `Resultado: ${match.goles_local || 0} - ${match.goles_visitante || 0}` : 
                'Sin simular';
            
            matchDiv.innerHTML = `
                <div class="data-item-info">
                    <div class="data-item-title">
                        ${this.escapeHtml(match.equipo_local)} vs ${this.escapeHtml(match.equipo_visitante)}
                    </div>
                    <div class="data-item-subtitle">
                        <i class="fas fa-calendar"></i> ${matchDate}<br>
                        <i class="fas fa-user-tie"></i> Árbitro: ${this.escapeHtml(match.arbitro)}<br>
                        <i class="fas fa-futbol"></i> ${resultText}
                    </div>
                </div>
                <div class="data-item-actions">
                    <button class="btn btn-success" onclick="adminPanel.simulateMatch(${match.id})" 
                            ${hasResult ? 'title="Re-simular partido"' : 'title="Simular partido"'}>
                        <i class="fas fa-play"></i>
                        ${hasResult ? 'Re-simular' : 'Simular'}
                    </button>
                    <button class="btn btn-secondary" onclick="adminPanel.editMatch(${match.id})">
                        <i class="fas fa-edit"></i>
                        Editar
                    </button>
                    <button class="btn btn-danger" onclick="adminPanel.deleteMatch(${match.id})">
                        <i class="fas fa-trash"></i>
                        Eliminar
                    </button>
                </div>
            `;
            
            container.appendChild(matchDiv);
        });
    }

    escapeHtml(text) {
        if (!text) return '';
        return text.replace(/[&<>"']/g, function(m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[m];
        });
    }

    async handleTeamForm(e) {
        e.preventDefault();
        const teamName = document.getElementById('team-name').value.trim();
        
        if (!teamName) {
            this.showAlert('Por favor ingrese un nombre válido', 'warning');
            return;
        }

        if (this.data.teams.some(team => team.nombre.toLowerCase() === teamName.toLowerCase())) {
            this.showAlert('Ya existe un equipo con ese nombre', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.addTeam, {
                method: 'POST',
                body: JSON.stringify({ nombre: teamName })
            });

            this.showAlert('Equipo agregado exitosamente', 'success');
            document.getElementById('form-team').reset();
            await this.loadData();
        } catch (error) {
            console.error('Error agregando equipo:', error);
            this.showAlert('Error al agregar el equipo: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async handleMatchForm(e) {
        e.preventDefault();
        
        const formData = {
            equipo_local_id: document.getElementById('home-team').value,
            equipo_visitante_id: document.getElementById('away-team').value,
            arbitro_id: document.getElementById('referee').value,
            fecha: document.getElementById('match-date').value
        };

        if (!formData.equipo_local_id || !formData.equipo_visitante_id || !formData.arbitro_id || !formData.fecha) {
            this.showAlert('Todos los campos son obligatorios', 'warning');
            return;
        }

        if (formData.equipo_local_id === formData.equipo_visitante_id) {
            this.showAlert('Un equipo no puede jugar contra sí mismo', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.createMatch, {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            this.showAlert('Partido creado exitosamente', 'success');
            document.getElementById('form-match').reset();
            await this.loadData();
        } catch (error) {
            console.error('Error creando partido:', error);
            this.showAlert('Error al crear el partido: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async handleAssignPlayerForm(e) {
        e.preventDefault();
        
        const formData = {
            jugador_id: document.getElementById('player').value,
            equipo_id: document.getElementById('team').value,
            posicion: document.getElementById('position').value
        };

        if (!formData.jugador_id || !formData.equipo_id) {
            this.showAlert('Por favor seleccione jugador y equipo', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.assignPlayer, {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            this.showAlert('Jugador asignado exitosamente', 'success');
            document.getElementById('form-player').reset();
            await this.loadData();
        } catch (error) {
            console.error('Error asignando jugador:', error);
            this.showAlert('Error al asignar jugador: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async editTeam(teamId) {
        const team = this.data.teams.find(t => t.id === teamId);
        if (!team) {
            this.showAlert('Equipo no encontrado', 'error');
            return;
        }
        
        const newName = prompt('Ingrese el nuevo nombre del equipo:', team.nombre);
        if (newName === null) return; // Cancelled
        
        if (!newName.trim()) {
            this.showAlert('El nombre no puede estar vacío', 'warning');
            return;
        }
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.teamDetail(teamId), {
                method: 'PUT',
                body: JSON.stringify({ nombre: newName.trim() })
            });
            
            this.showAlert('Equipo actualizado exitosamente', 'success');
            await this.loadData();
        } catch (error) {
            console.error('Error actualizando equipo:', error);
            this.showAlert('Error al actualizar el equipo: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteTeam(teamId) {
        if (!confirm('¿Está seguro de que desea eliminar este equipo? Esta acción no se puede deshacer.')) return;
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.teamDetail(teamId), {
                method: 'DELETE'
            });
            
            this.showAlert('Equipo eliminado exitosamente', 'success');
            await this.loadData();
        } catch (error) {
            console.error('Error eliminando equipo:', error);
            this.showAlert('Error al eliminar el equipo: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async editMatch(matchId) {
        const match = this.data.matches.find(m => m.id === matchId);
        if (!match) {
            this.showAlert('Partido no encontrado', 'error');
            return;
        }
        
        const newDate = prompt('Ingrese la nueva fecha y hora del partido (YYYY-MM-DDTHH:mm):', match.fecha);
        if (newDate === null) return; // Cancelled
        
        if (!newDate.trim()) {
            this.showAlert('La fecha no puede estar vacía', 'warning');
            return;
        }
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.matchDetail(matchId), {
                method: 'PUT',
                body: JSON.stringify({ fecha: newDate.trim() })
            });
            
            this.showAlert('Partido actualizado exitosamente', 'success');
            await this.loadData();
        } catch (error) {
            console.error('Error actualizando partido:', error);
            this.showAlert('Error al actualizar el partido: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteMatch(matchId) {
        if (!confirm('¿Está seguro de que desea eliminar este partido? Esta acción no se puede deshacer.')) return;
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.matchDetail(matchId), {
                method: 'DELETE'
            });
            
            this.showAlert('Partido eliminado exitosamente', 'success');
            await this.loadData();
        } catch (error) {
            console.error('Error eliminando partido:', error);
            this.showAlert('Error al eliminar el partido: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async simulateMatch(matchId) {
        if (!confirm('¿Desea simular este partido? Esto generará un resultado aleatorio basado en las fuerzas de los equipos.')) {
            return;
        }

        try {
            this.showLoading(true);
            console.log(`Simulando partido con ID: ${matchId}`);
            
            const result = await this.makeRequest(this.apiEndpoints.simulateMatch(matchId), {
                method: 'POST'
            });
            
            console.log('Resultado de simulación:', result);
            
            if (result.success) {
                const message = `Partido simulado exitosamente!\n` +
                    `${result.equipo_local}: ${result.goles_local}\n` +
                    `${result.equipo_visitante}: ${result.goles_visitante}\n` +
                    `Ganador: ${result.ganador}`;
                
                this.showAlert(message, 'success');
                
                // Recargar datos para reflejar los cambios
                await this.loadData();
                
                // Opcional: mostrar más detalles
                if (result.porcentaje_local && result.porcentaje_visitante) {
                    setTimeout(() => {
                        this.showAlert(
                            `Probabilidades: ${result.equipo_local} ${result.porcentaje_local}% - ${result.equipo_visitante} ${result.porcentaje_visitante}%`, 
                            'info'
                        );
                    }, 1000);
                }
            } else {
                this.showAlert('Error en la simulación: ' + (result.error || 'Error desconocido'), 'error');
            }
        } catch (error) {
            console.error('Error simulando partido:', error);
            this.showAlert('Error al simular el partido: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Método auxiliar para debugging
    debugMatch(matchId) {
        console.log('Debug info for match:', matchId);
        console.log('All matches:', this.data.matches);
        console.log('API endpoint:', this.apiEndpoints.simulateMatch(matchId));
        console.log('CSRF Token:', this.getCookie('csrftoken'));
    }
}

// Inicializar cuando el DOM esté listo
let adminPanel;

document.addEventListener('DOMContentLoaded', () => {
    adminPanel = new AdminPanel();
    window.adminPanel = adminPanel; // Para acceso global
    
    // Debugging: exponer métodos útiles en consola
    window.debugAdminPanel = () => {
        console.log('AdminPanel instance:', adminPanel);
        console.log('Current data:', adminPanel.data);
        console.log('API endpoints:', adminPanel.apiEndpoints);
    };
});