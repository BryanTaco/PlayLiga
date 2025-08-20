/**
 * Admin Panel Management System - Versión Profesional Mejorada
 * Sistema completo de gestión del panel de administración
 */

class AdminPanel {
    constructor() {
        this.data = {
            teams: [],
            matches: [],
            players: [],
            referees: [],
            statistics: []
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
            statistics: '/torneo/api/estadisticas_equipo/',
            csrfToken: '/torneo/api/csrf-token/'
        };
        
        this.cache = new Map();
        this.init();
    }

    async init() {
        console.log('🚀 Inicializando AdminPanel...');
        this.showLoading(true);
        
        try {
            // Inicializar componentes
            this.bindEvents();
            this.setupValidations();
            this.setupAutoRefresh();
            
            // Cargar datos iniciales
            await this.loadData();
            
            // Mostrar notificación de éxito
            this.showAlert('✅ Panel cargado correctamente', 'success');
            
            // Inicializar gráficos si existen
            this.initCharts();
            
        } catch (error) {
            console.error('❌ Error de inicialización:', error);
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
                if (confirm('¿Está seguro de que desea cerrar sesión?')) {
                    window.location.href = '/torneo/logout/';
                }
            });
        }

        // Búsqueda en tiempo real
        this.setupSearch();
        
        // Filtros
        this.setupFilters();
    }

    setupSearch() {
        // Agregar campo de búsqueda si no existe
        const searchContainer = document.querySelector('.stats-container');
        if (searchContainer && !document.getElementById('search-input')) {
            const searchDiv = document.createElement('div');
            searchDiv.className = 'search-container';
            searchDiv.innerHTML = `
                <input type="text" id="search-input" placeholder="🔍 Buscar equipos, jugadores..." class="search-input">
            `;
            searchContainer.parentNode.insertBefore(searchDiv, searchContainer);
            
            const searchInput = document.getElementById('search-input');
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }
    }

    handleSearch(query) {
        const lowerQuery = query.toLowerCase();
        
        // Buscar en equipos
        const teamElements = document.querySelectorAll('.data-item');
        teamElements.forEach(element => {
            const text = element.textContent.toLowerCase();
            element.style.display = text.includes(lowerQuery) ? 'flex' : 'none';
        });
    }

    setupFilters() {
        // Implementar filtros para partidos
        const matchesSection = document.querySelector('#vista-partidos');
        if (matchesSection && !document.getElementById('filter-matches')) {
            const filterDiv = document.createElement('div');
            filterDiv.className = 'filter-container';
            filterDiv.innerHTML = `
                <select id="filter-matches" class="filter-select">
                    <option value="all">Todos los partidos</option>
                    <option value="pending">Pendientes</option>
                    <option value="simulated">Simulados</option>
                </select>
            `;
            matchesSection.parentNode.insertBefore(filterDiv, matchesSection);
            
            document.getElementById('filter-matches').addEventListener('change', (e) => {
                this.filterMatches(e.target.value);
            });
        }
    }

    filterMatches(filter) {
        let filteredMatches = [...this.data.matches];
        
        if (filter === 'pending') {
            filteredMatches = filteredMatches.filter(m => !m.simulado);
        } else if (filter === 'simulated') {
            filteredMatches = filteredMatches.filter(m => m.simulado);
        }
        
        this.updateMatchesList(filteredMatches);
    }

    setupValidations() {
        const homeTeamSelect = document.getElementById('home-team');
        const awayTeamSelect = document.getElementById('away-team');
        
        const validateTeamSelection = () => {
            if (homeTeamSelect && awayTeamSelect) {
                if (homeTeamSelect.value && awayTeamSelect.value && 
                    homeTeamSelect.value === awayTeamSelect.value) {
                    awayTeamSelect.setCustomValidity('Debe seleccionar un equipo diferente al local');
                    this.showAlert('⚠️ Un equipo no puede jugar contra sí mismo', 'warning');
                } else {
                    awayTeamSelect.setCustomValidity('');
                }
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
            matchDateInput.value = now.toISOString().slice(0, 16);
        }
    }

    setupAutoRefresh() {
        // Auto-refresh cada 30 segundos para datos en tiempo real
        setInterval(() => {
            this.loadData(true); // true = silent reload
        }, 30000);
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            if (show) {
                loading.classList.remove('hidden');
                loading.style.opacity = '1';
            } else {
                loading.style.opacity = '0';
                setTimeout(() => loading.classList.add('hidden'), 300);
            }
        }
    }

    showAlert(message, type = 'info', duration = 5000) {
        const container = document.getElementById('alerts-container');
        if (!container) {
            console.warn('Alert container not found');
            return;
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in`;
        
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
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(alert);
        
        // Animación de entrada
        setTimeout(() => alert.classList.add('show'), 10);
        
        // Auto-remove con animación de salida
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 300);
        }, duration);
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
        // Verificar caché para GET requests
        if (options.method === 'GET' || !options.method) {
            const cached = this.cache.get(url);
            if (cached && Date.now() - cached.timestamp < 60000) { // 1 minuto de caché
                console.log(`📦 Usando caché para: ${url}`);
                return cached.data;
            }
        }

        try {
            const csrfToken = this.getCookie('csrftoken');
            const headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                ...options.headers
            };

            console.log(`📡 Petición a: ${url}`);

            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`❌ Error HTTP ${response.status}:`, errorText);
                
                let errorMessage;
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || errorJson.message || errorText;
                } catch {
                    errorMessage = errorText;
                }
                
                throw new Error(errorMessage);
            }

            const contentType = response.headers.get("content-type");
            let data;
            
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            // Guardar en caché si es GET
            if (options.method === 'GET' || !options.method) {
                this.cache.set(url, { data, timestamp: Date.now() });
            }

            return data;
            
        } catch (error) {
            console.error('❌ Error en makeRequest:', error);
            throw error;
        }
    }

    async loadData(silent = false) {
        if (!silent) this.showLoading(true);
        
        try {
            console.log('📊 Cargando datos desde la API...');
            
            const [teamsResp, matchesResp, playersResp, refereesResp] = await Promise.allSettled([
                this.makeRequest(this.apiEndpoints.teams),
                this.makeRequest(this.apiEndpoints.matches),
                this.makeRequest(this.apiEndpoints.players),
                this.makeRequest(this.apiEndpoints.referees)
            ]);

            // Procesar respuestas con manejo de errores
            this.data.teams = teamsResp.status === 'fulfilled' ? teamsResp.value : [];
            this.data.matches = matchesResp.status === 'fulfilled' ? matchesResp.value : [];
            this.data.players = playersResp.status === 'fulfilled' ? playersResp.value : [];
            this.data.referees = refereesResp.status === 'fulfilled' ? refereesResp.value : [];

            console.log('✅ Datos cargados:', {
                equipos: this.data.teams.length,
                partidos: this.data.matches.length,
                jugadores: this.data.players.length,
                árbitros: this.data.referees.length
            });

            this.updateUI();
            
            if (!silent) {
                this.showAlert(`Datos actualizados: ${this.data.teams.length} equipos, ${this.data.matches.length} partidos`, 'info', 2000);
            }
            
        } catch (error) {
            console.error('❌ Error cargando datos:', error);
            if (!silent) {
                this.showAlert('Error al cargar los datos: ' + error.message, 'error');
            }
        } finally {
            if (!silent) this.showLoading(false);
        }
    }

    updateUI() {
        this.updateStats();
        this.updateSelects();
        this.updateTeamsList();
        this.updateMatchesList(this.data.matches);
        this.updateCharts();
    }

    updateStats() {
        // Animación de contadores
        const animateValue = (element, start, end, duration) => {
            if (!element) return;
            
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                element.textContent = Math.floor(progress * (end - start) + start);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        };

        const elements = {
            'stat-teams': this.data.teams.length,
            'stat-matches': this.data.matches.length,
            'stat-players': this.data.players.length,
            'stat-referees': this.data.referees.length
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                const currentValue = parseInt(element.textContent) || 0;
                animateValue(element, currentValue, value, 500);
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

            const currentValue = select.value;
            select.innerHTML = `<option value="">${placeholder}</option>`;
            
            // Ordenar equipos alfabéticamente
            const sortedTeams = [...this.data.teams].sort((a, b) => 
                a.nombre.localeCompare(b.nombre)
            );
            
            sortedTeams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.nombre;
                if (currentValue == team.id) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        });
    }

    updatePlayerSelect() {
        const select = document.getElementById('player');
        if (!select) return;

        const currentValue = select.value;
        select.innerHTML = '<option value="">Seleccione jugador</option>';
        
        // Agrupar jugadores por equipo
        const playersByTeam = {};
        this.data.players.forEach(player => {
            const teamName = player.equipo__nombre || 'Sin equipo';
            if (!playersByTeam[teamName]) {
                playersByTeam[teamName] = [];
            }
            playersByTeam[teamName].push(player);
        });
        
        // Crear optgroups
        Object.entries(playersByTeam).forEach(([teamName, players]) => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = teamName;
            
            players.sort((a, b) => 
                `${a.nombre} ${a.apellido}`.localeCompare(`${b.nombre} ${b.apellido}`)
            ).forEach(player => {
                const option = document.createElement('option');
                option.value = player.id;
                option.textContent = `${player.nombre} ${player.apellido}`;
                if (currentValue == player.id) {
                    option.selected = true;
                }
                optgroup.appendChild(option);
            });
            
            select.appendChild(optgroup);
        });
    }

    updateRefereeSelect() {
        const select = document.getElementById('referee');
        if (!select) return;

        const currentValue = select.value;
        select.innerHTML = '<option value="">Seleccione árbitro</option>';
        
        // Ordenar árbitros alfabéticamente
        const sortedReferees = [...this.data.referees].sort((a, b) => 
            `${a.nombre} ${a.apellido}`.localeCompare(`${b.nombre} ${b.apellido}`)
        );
        
        sortedReferees.forEach(referee => {
            const option = document.createElement('option');
            option.value = referee.id;
            option.textContent = `${referee.nombre} ${referee.apellido}`;
            if (currentValue == referee.id) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    updateTeamsList() {
        const container = document.getElementById('vista-equipos');
        if (!container) return;
        
        if (this.data.teams.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users fa-3x"></i>
                    <h3>No hay equipos registrados</h3>
                    <p>Agrega el primer equipo usando el formulario</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        
        // Ordenar equipos por nombre
        const sortedTeams = [...this.data.teams].sort((a, b) => 
            a.nombre.localeCompare(b.nombre)
        );
        
        sortedTeams.forEach(team => {
            const teamDiv = document.createElement('div');
            teamDiv.className = 'data-item fade-in';
            
            // Contar jugadores del equipo
            const teamPlayers = this.data.players.filter(p => p.equipo_id === team.id);
            const playersText = teamPlayers.length > 0 
                ? `${teamPlayers.length} jugador${teamPlayers.length !== 1 ? 'es' : ''}`
                : 'Sin jugadores';
            
            teamDiv.innerHTML = `
                <div class="data-item-info">
                    <div class="data-item-title">
                        <i class="fas fa-shield-alt"></i> ${this.escapeHtml(team.nombre)}
                    </div>
                    <div class="data-item-subtitle">
                        <i class="fas fa-users"></i> ${playersText}
                    </div>
                </div>
                <div class="data-item-actions">
                    <button class="btn btn-info btn-sm" onclick="adminPanel.viewTeamDetails(${team.id})" title="Ver detalles">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="adminPanel.editTeam(${team.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="adminPanel.deleteTeam(${team.id})" title="Eliminar">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            container.appendChild(teamDiv);
        });
    }

    updateMatchesList(matches = this.data.matches) {
        const container = document.getElementById('vista-partidos');
        if (!container) return;
        
        if (matches.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar fa-3x"></i>
                    <h3>No hay partidos</h3>
                    <p>Crea el primer partido usando el formulario</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        
        // Ordenar partidos por fecha
        const sortedMatches = [...matches].sort((a, b) => 
            new Date(b.fecha) - new Date(a.fecha)
        );
        
        sortedMatches.forEach(match => {
            const matchDiv = document.createElement('div');
            matchDiv.className = 'data-item fade-in';
            
            const matchDate = new Date(match.fecha);
            const dateStr = matchDate.toLocaleString('es-ES', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            // Determinar estado del partido
            const now = new Date();
            const isPast = matchDate < now;
            const hasResult = match.simulado;
            
            let statusBadge = '';
            let statusIcon = '';
            if (hasResult) {
                statusBadge = '<span class="badge badge-success">Finalizado</span>';
                statusIcon = 'check-circle';
            } else if (isPast) {
                statusBadge = '<span class="badge badge-warning">Por simular</span>';
                statusIcon = 'clock';
            } else {
                statusBadge = '<span class="badge badge-info">Próximo</span>';
                statusIcon = 'calendar-check';
            }
            
            const resultText = hasResult 
                ? `<strong>${match.goles_local || 0} - ${match.goles_visitante || 0}</strong>` 
                : 'Sin jugar';
            
            const winnerText = match.ganador 
                ? `🏆 ${match.ganador}` 
                : (hasResult ? '🤝 Empate' : '');
            
            matchDiv.innerHTML = `
                <div class="data-item-info">
                    <div class="data-item-title">
                        ${this.escapeHtml(match.equipo_local)} 
                        <span class="vs">VS</span> 
                        ${this.escapeHtml(match.equipo_visitante)}
                        ${statusBadge}
                    </div>
                    <div class="data-item-subtitle">
                        <div><i class="fas fa-${statusIcon}"></i> ${dateStr}</div>
                        <div><i class="fas fa-user-tie"></i> ${this.escapeHtml(match.arbitro || 'Sin árbitro')}</div>
                        <div><i class="fas fa-futbol"></i> ${resultText} ${winnerText}</div>
                    </div>
                </div>
                <div class="data-item-actions">
                    ${!hasResult ? `
                        <button class="btn btn-success btn-sm" onclick="adminPanel.simulateMatch(${match.id})" 
                                title="Simular partido">
                            <i class="fas fa-play"></i> Simular
                        </button>
                    ` : `
                        <button class="btn btn-warning btn-sm" onclick="adminPanel.simulateMatch(${match.id})" 
                                title="Re-simular partido">
                            <i class="fas fa-redo"></i> Re-simular
                        </button>
                    `}
                    <button class="btn btn-secondary btn-sm" onclick="adminPanel.editMatch(${match.id})" 
                            title="Editar partido">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="adminPanel.deleteMatch(${match.id})" 
                            title="Eliminar partido">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            container.appendChild(matchDiv);
        });
    }

    escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        };
        return text.toString().replace(/[&<>"']/g, m => map[m]);
    }

    async handleTeamForm(e) {
        e.preventDefault();
        const teamName = document.getElementById('team-name').value.trim();
        
        if (!teamName) {
            this.showAlert('⚠️ Por favor ingrese un nombre válido', 'warning');
            return;
        }

        if (teamName.length < 3) {
            this.showAlert('⚠️ El nombre del equipo debe tener al menos 3 caracteres', 'warning');
            return;
        }

        if (this.data.teams.some(team => team.nombre.toLowerCase() === teamName.toLowerCase())) {
            this.showAlert('⚠️ Ya existe un equipo con ese nombre', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            const response = await this.makeRequest(this.apiEndpoints.addTeam, {
                method: 'POST',
                body: JSON.stringify({ nombre: teamName })
            });

            this.showAlert(`✅ Equipo "${teamName}" agregado exitosamente`, 'success');
            document.getElementById('form-team').reset();
            await this.loadData();
            
            // Hacer scroll a la lista de equipos
            document.getElementById('vista-equipos')?.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error agregando equipo:', error);
            this.showAlert('❌ Error al agregar el equipo: ' + error.message, 'error');
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

        // Validaciones
        if (!formData.equipo_local_id || !formData.equipo_visitante_id) {
            this.showAlert('⚠️ Debe seleccionar ambos equipos', 'warning');
            return;
        }

        if (!formData.arbitro_id) {
            this.showAlert('⚠️ Debe seleccionar un árbitro', 'warning');
            return;
        }

        if (!formData.fecha) {
            this.showAlert('⚠️ Debe seleccionar fecha y hora', 'warning');
            return;
        }

        if (formData.equipo_local_id === formData.equipo_visitante_id) {
            this.showAlert('⚠️ Un equipo no puede jugar contra sí mismo', 'warning');
            return;
        }

        // Validar fecha futura
        const selectedDate = new Date(formData.fecha);
        const now = new Date();
        if (selectedDate < now) {
            this.showAlert('⚠️ La fecha debe ser futura', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            const response = await this.makeRequest(this.apiEndpoints.createMatch, {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            this.showAlert('✅ Partido creado exitosamente', 'success');
            document.getElementById('form-match').reset();
            await this.loadData();
            
            // Hacer scroll a la lista de partidos
            document.getElementById('vista-partidos')?.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error creando partido:', error);
            this.showAlert('❌ Error al crear el partido: ' + error.message, 'error');
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

        if (!formData.jugador_id) {
            this.showAlert('⚠️ Debe seleccionar un jugador', 'warning');
            return;
        }

        if (!formData.equipo_id) {
            this.showAlert('⚠️ Debe seleccionar un equipo', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            const response = await this.makeRequest(this.apiEndpoints.assignPlayer, {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            this.showAlert(`✅ ${response.mensaje}`, 'success');
            document.getElementById('form-player').reset();
            await this.loadData();
            
        } catch (error) {
            console.error('Error asignando jugador:', error);
            this.showAlert('❌ Error al asignar jugador: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async viewTeamDetails(teamId) {
        try {
            this.showLoading(true);
            const response = await this.makeRequest(this.apiEndpoints.teamDetail(teamId));
            
            if (response.success && response.equipo) {
                const team = response.equipo;
                
                // Crear modal con detalles
                const modalContent = `
                    <div class="team-details">
                        <h3>${this.escapeHtml(team.nombre)}</h3>
                        
                        <div class="stats-grid">
                            <div class="stat-card">
                                <i class="fas fa-trophy"></i>
                                <h4>${team.estadisticas.victorias}</h4>
                                <p>Victorias</p>
                            </div>
                            <div class="stat-card">
                                <i class="fas fa-handshake"></i>
                                <h4>${team.estadisticas.empates}</h4>
                                <p>Empates</p>
                            </div>
                            <div class="stat-card">
                                <i class="fas fa-times-circle"></i>
                                <h4>${team.estadisticas.derrotas}</h4>
                                <p>Derrotas</p>
                            </div>
                            <div class="stat-card">
                                <i class="fas fa-futbol"></i>
                                <h4>${team.estadisticas.goles_favor}</h4>
                                <p>Goles a favor</p>
                            </div>
                        </div>
                        
                        <h4>Jugadores (${team.jugadores.length})</h4>
                        <div class="players-list">
                            ${team.jugadores.map(j => `
                                <div class="player-card">
                                    <span class="player-number">${j.numero_camiseta || '-'}</span>
                                    <span class="player-name">${this.escapeHtml(j.nombre)}</span>
                                    <span class="player-position">${j.posicion || 'Sin definir'}</span>
                                    <span class="player-stats">
                                        ⚽ ${j.goles} | 🎯 ${j.asistencias}
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                
                this.showModal('Detalles del Equipo', modalContent);
            }
            
        } catch (error) {
            console.error('Error obteniendo detalles del equipo:', error);
            this.showAlert('❌ Error al cargar detalles del equipo', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async editTeam(teamId) {
        const team = this.data.teams.find(t => t.id === teamId);
        if (!team) {
            this.showAlert('❌ Equipo no encontrado', 'error');
            return;
        }
        
        const newName = prompt('Ingrese el nuevo nombre del equipo:', team.nombre);
        if (newName === null) return; // Cancelled
        
        if (!newName.trim()) {
            this.showAlert('⚠️ El nombre no puede estar vacío', 'warning');
            return;
        }
        
        if (newName.trim() === team.nombre) {
            this.showAlert('ℹ️ El nombre no ha cambiado', 'info');
            return;
        }
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.teamDetail(teamId), {
                method: 'PUT',
                body: JSON.stringify({ nombre: newName.trim() })
            });
            
            this.showAlert('✅ Equipo actualizado exitosamente', 'success');
            await this.loadData();
            
        } catch (error) {
            console.error('Error actualizando equipo:', error);
            this.showAlert('❌ Error al actualizar el equipo: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteTeam(teamId) {
        const team = this.data.teams.find(t => t.id === teamId);
        if (!team) {
            this.showAlert('❌ Equipo no encontrado', 'error');
            return;
        }
        
        const confirmMessage = `¿Está seguro de que desea eliminar el equipo "${team.nombre}"?\n\nEsta acción no se puede deshacer.`;
        
        if (!confirm(confirmMessage)) return;
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.teamDetail(teamId), {
                method: 'DELETE'
            });
            
            this.showAlert(`✅ Equipo "${team.nombre}" eliminado exitosamente`, 'success');
            await this.loadData();
            
        } catch (error) {
            console.error('Error eliminando equipo:', error);
            this.showAlert('❌ ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async editMatch(matchId) {
        const match = this.data.matches.find(m => m.id === matchId);
        if (!match) {
            this.showAlert('❌ Partido no encontrado', 'error');
            return;
        }
        
        const currentDate = new Date(match.fecha);
        const dateStr = currentDate.toISOString().slice(0, 16);
        
        const newDate = prompt('Ingrese la nueva fecha y hora del partido:', dateStr);
        if (newDate === null) return; // Cancelled
        
        if (!newDate.trim()) {
            this.showAlert('⚠️ La fecha no puede estar vacía', 'warning');
            return;
        }
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.matchDetail(matchId), {
                method: 'PUT',
                body: JSON.stringify({ fecha: newDate.trim() })
            });
            
            this.showAlert('✅ Partido actualizado exitosamente', 'success');
            await this.loadData();
            
        } catch (error) {
            console.error('Error actualizando partido:', error);
            this.showAlert('❌ Error al actualizar el partido: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteMatch(matchId) {
        const match = this.data.matches.find(m => m.id === matchId);
        if (!match) {
            this.showAlert('❌ Partido no encontrado', 'error');
            return;
        }
        
        const confirmMessage = `¿Está seguro de que desea eliminar el partido?\n\n${match.equipo_local} vs ${match.equipo_visitante}\n\nEsta acción no se puede deshacer.`;
        
        if (!confirm(confirmMessage)) return;
        
        try {
            this.showLoading(true);
            await this.makeRequest(this.apiEndpoints.matchDetail(matchId), {
                method: 'DELETE'
            });
            
            this.showAlert('✅ Partido eliminado exitosamente', 'success');
            await this.loadData();
            
        } catch (error) {
            console.error('Error eliminando partido:', error);
            this.showAlert('❌ ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async simulateMatch(matchId) {
        const match = this.data.matches.find(m => m.id === matchId);
        if (!match) {
            this.showAlert('❌ Partido no encontrado', 'error');
            return;
        }
        
        const confirmMessage = match.simulado 
            ? `¿Desea RE-SIMULAR este partido?\n\n${match.equipo_local} vs ${match.equipo_visitante}\n\nEsto sobrescribirá el resultado actual.`
            : `¿Desea simular este partido?\n\n${match.equipo_local} vs ${match.equipo_visitante}\n\nSe generará un resultado basado en las fuerzas de los equipos.`;
        
        if (!confirm(confirmMessage)) return;

        try {
            this.showLoading(true);
            console.log(`⚽ Simulando partido con ID: ${matchId}`);
            
            const result = await this.makeRequest(this.apiEndpoints.simulateMatch(matchId), {
                method: 'POST'
            });
            
            console.log('✅ Resultado de simulación:', result);
            
            if (result.success) {
                // Crear mensaje detallado
                const message = `
                    <div class="simulation-result">
                        <h4>¡Partido Simulado!</h4>
                        <div class="match-result">
                            <div class="team-score">
                                <span>${result.equipo_local}</span>
                                <span class="score">${result.goles_local}</span>
                            </div>
                            <div class="vs">-</div>
                            <div class="team-score">
                                <span class="score">${result.goles_visitante}</span>
                                <span>${result.equipo_visitante}</span>
                            </div>
                        </div>
                        <div class="winner">
                            ${result.ganador === 'Empate' ? '🤝 Empate' : `🏆 Ganador: ${result.ganador}`}
                        </div>
                        ${result.porcentaje_local && result.porcentaje_visitante ? `
                            <div class="probabilities">
                                Probabilidades: ${result.equipo_local} ${result.porcentaje_local}% - ${result.equipo_visitante} ${result.porcentaje_visitante}%
                            </div>
                        ` : ''}
                    </div>
                `;
                
                this.showModal('Resultado de la Simulación', message);
                
                // Recargar datos
                await this.loadData();
                
                // Hacer scroll al partido simulado
                setTimeout(() => {
                    const matchElement = document.querySelector(`[data-match-id="${matchId}"]`);
                    if (matchElement) {
                        matchElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        matchElement.classList.add('highlight');
                        setTimeout(() => matchElement.classList.remove('highlight'), 3000);
                    }
                }, 500);
                
            } else {
                this.showAlert('❌ Error en la simulación: ' + (result.error || 'Error desconocido'), 'error');
            }
            
        } catch (error) {
            console.error('Error simulando partido:', error);
            this.showAlert('❌ Error al simular el partido: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    showModal(title, content) {
        // Remover modal existente si hay uno
        const existingModal = document.getElementById('admin-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Crear nuevo modal
        const modal = document.createElement('div');
        modal.id = 'admin-modal';
        modal.className = 'modal fade-in';
        modal.innerHTML = `
            <div class="modal-backdrop" onclick="adminPanel.closeModal()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close" onclick="adminPanel.closeModal()">×</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="adminPanel.closeModal()">Cerrar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Animación de entrada
        setTimeout(() => modal.classList.add('show'), 10);
    }

    closeModal() {
        const modal = document.getElementById('admin-modal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        }
    }

    initCharts() {
        // Implementar gráficos con Chart.js si está disponible
        if (typeof Chart !== 'undefined') {
            this.updateCharts();
        }
    }

    updateCharts() {
        // Actualizar gráficos si existen
        // Implementación pendiente según necesidades
    }

    // Método de debugging
    debug() {
        console.log('📊 Estado actual del AdminPanel:');
        console.log('Datos:', this.data);
        console.log('Endpoints:', this.apiEndpoints);
        console.log('Cache:', this.cache);
        return this.data;
    }
}

// Inicializar cuando el DOM esté listo
let adminPanel;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🎮 Iniciando PlayLiga Admin Panel...');
    adminPanel = new AdminPanel();
    window.adminPanel = adminPanel; // Para acceso global
    
    // Exponer métodos útiles en consola para debugging
    window.debugAdminPanel = () => adminPanel.debug();
    
    console.log('💡 Tip: Usa debugAdminPanel() en la consola para ver el estado actual');
});