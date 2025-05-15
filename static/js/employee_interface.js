// DOM Elements
const screens = document.querySelectorAll('.screen');
const navLinks = document.querySelectorAll('.nav-link');
const tabItems = document.querySelectorAll('.tab-item');
const tabContents = document.querySelectorAll('.tab-content');
const newRequestBtn = document.getElementById('newRequestBtn');
const newRequestModal = document.getElementById('newRequestModal');
const requestDetailModal = document.getElementById('requestDetailModal');
const submitRequestBtn = document.getElementById('submitRequestBtn');
const cancelRequestBtn = document.getElementById('cancelRequestBtn');
const modalCloseButtons = document.querySelectorAll('.modal-close, .close-modal');

// ====== APPLICATION STATE ======
const state = {
    profile: null,
    stats: null,
    attendanceHistory: {
        period: 'week',
        filter: 'ALL',
        data: null
    },
    leaveRequests: {
        filter: 'PENDING',
        data: null
    },
    currentRequestDetail: null
};

// ====== INITIALISATION ======
document.addEventListener('DOMContentLoaded', function() {
    // Charger les données initiales
    loadProfileData();
    loadStatsData();
    loadAttendanceHistory();
    loadLeaveRequests();

    // Configurer les écouteurs d'événements pour la navigation
    setupEventListeners();
});

// ====== NAVIGATION & UI ======
function setupEventListeners() {
    // Navigation entre les écrans
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Retirer la classe active de tous les liens et écrans
            navLinks.forEach(item => item.classList.remove('active'));
            screens.forEach(screen => screen.classList.remove('active'));
            
            // Ajouter la classe active au lien cliqué et à l'écran correspondant
            this.classList.add('active');
            const screenId = this.getAttribute('data-screen');
            document.getElementById(screenId).classList.add('active');
            
            // Charger les données spécifiques à l'écran si nécessaire
            if (screenId === 'historyScreen') {
                loadAttendanceHistory();
            } else if (screenId === 'requestsScreen') {
                loadLeaveRequests();
            }
        });
    });

    // Onglets dans l'écran Demandes
    tabItems.forEach(tab => {
        tab.addEventListener('click', function() {
            // Retirer la classe active de tous les onglets et contenus
            tabItems.forEach(item => item.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Ajouter la classe active à l'onglet cliqué et au contenu correspondant
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            // Mettre à jour le filtre et recharger les données
            if (tabId === 'pendingRequests') {
                state.leaveRequests.filter = 'PENDING';
            } else if (tabId === 'approvedRequests') {
                state.leaveRequests.filter = 'APPROVED';
            } else if (tabId === 'historyRequests') {
                state.leaveRequests.filter = 'ALL';
            }
            
            loadLeaveRequests();
        });
    });

    // Filtres dans l'écran Historique
    const periodFilter = document.querySelector('#historyScreen .filter-select:first-of-type');
    if (periodFilter) {
        periodFilter.addEventListener('change', function() {
            // Mettre à jour la période et recharger l'historique
            const value = this.value;
            if (value === 'Aujourd\'hui') {
                state.attendanceHistory.period = 'day';
            } else if (value === 'Cette semaine') {
                state.attendanceHistory.period = 'week';
            } else if (value === 'Ce mois') {
                state.attendanceHistory.period = 'month';
            } else if (value === 'Mois précédent') {
                // Calculer le mois précédent
                const today = new Date();
                const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                const lastDay = new Date(today.getFullYear(), today.getMonth(), 0);
                state.attendanceHistory.customStartDate = lastMonth.toISOString().split('T')[0];
                state.attendanceHistory.customEndDate = lastDay.toISOString().split('T')[0];
            }
            
            loadAttendanceHistory();
        });
    }

    const typeFilter = document.querySelector('#historyScreen .filter-select:last-of-type');
    if (typeFilter) {
        typeFilter.addEventListener('change', function() {
            // Mettre à jour le type de pointage et recharger l'historique
            const value = this.value;
            if (value === 'Tous') {
                state.attendanceHistory.filter = 'ALL';
            } else if (value === 'Arrivée') {
                state.attendanceHistory.filter = 'IN';
            } else if (value === 'Départ') {
                state.attendanceHistory.filter = 'OUT';
            } else if (value === 'Pause') {
                state.attendanceHistory.filter = 'BREAK_START'; // ou BREAK_END
            }
            
            loadAttendanceHistory();
        });
    }

    // Ouvrir le modal de nouvelle demande
    newRequestBtn.addEventListener('click', function() {
        newRequestModal.classList.add('active');
        
        // Réinitialiser le formulaire
        document.getElementById('requestForm').reset();
        
        // Définir les dates par défaut (aujourd'hui + demain)
        const today = new Date();
        const tomorrow = new Date();
        tomorrow.setDate(today.getDate() + 1);
        
        const startDateField = document.querySelector('#requestForm input[type="date"]:first-of-type');
        const endDateField = document.querySelector('#requestForm input[type="date"]:last-of-type');
        
        if (startDateField && endDateField) {
            startDateField.value = today.toISOString().split('T')[0];
            endDateField.value = tomorrow.toISOString().split('T')[0];
            
            // S'assurer que la date de début est au minimum aujourd'hui
            startDateField.min = today.toISOString().split('T')[0];
            
            // Mettre à jour la date minimum de fin quand la date de début change
            startDateField.addEventListener('change', function() {
                endDateField.min = this.value;
                
                // Si la date de fin est inférieure à la date de début, la mettre à jour
                if (endDateField.value < this.value) {
                    endDateField.value = this.value;
                }
            });
        }
    });

    // Soumettre une nouvelle demande
    submitRequestBtn.addEventListener('click', function() {
        // Récupérer les données du formulaire
        const leaveTypeSelect = document.querySelector('#requestForm select');
        const startDateField = document.querySelector('#requestForm input[type="date"]:first-of-type');
        const endDateField = document.querySelector('#requestForm input[type="date"]:last-of-type');
        const reasonField = document.querySelector('#requestForm textarea');
        
        // Mapper les valeurs d'interface aux valeurs attendues par l'API
        const leaveTypeMap = {
            'Congé annuel': 'VACATION',
            'Congé maladie': 'SICK',
            'Congé sans solde': 'PERSONAL',
            'Congé spécial': 'OTHER',
            'Autre': 'OTHER'
        };
        
        // Créer l'objet de demande
        const requestData = {
            start_date: startDateField.value,
            end_date: endDateField.value,
            leave_type: leaveTypeMap[leaveTypeSelect.value] || 'VACATION',
            reason: reasonField.value
        };
        
        // Envoyer la demande à l'API
        createLeaveRequest(requestData);
    });

    // Fermer les modals
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            newRequestModal.classList.remove('active');
            requestDetailModal.classList.remove('active');
        });
    });

    // Annuler une demande
    cancelRequestBtn.addEventListener('click', function() {
        if (state.currentRequestDetail && state.currentRequestDetail.id) {
            cancelLeaveRequest(state.currentRequestDetail.id);
        }
    });

    // Fermer les modals en cliquant à l'extérieur
    window.addEventListener('click', function(e) {
        if (e.target === newRequestModal) {
            newRequestModal.classList.remove('active');
        }
        if (e.target === requestDetailModal) {
            requestDetailModal.classList.remove('active');
        }
    });
}

// Créer des écouteurs d'événements pour les éléments de demande (générés dynamiquement)
function setupRequestItemListeners() {
    document.querySelectorAll('.request-item').forEach(item => {
        item.addEventListener('click', function() {
            const requestId = this.getAttribute('data-request-id');
            loadLeaveRequestDetail(requestId);
        });
    });
}

// ====== API DATA LOADING ======

// Charger les données de profil
function loadProfileData() {
    fetch('/api/profile/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors du chargement du profil');
            }
            return response.json();
        })
        .then(data => {
            state.profile = data;
            updateProfileUI();
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Afficher une notification d'erreur
        });
}

// Charger les statistiques
function loadStatsData() {
    fetch('/api/stats/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des statistiques');
            }
            return response.json();
        })
        .then(data => {
            state.stats = data;
            updateStatsUI();
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Afficher une notification d'erreur
        });
}

// Charger l'historique des pointages
function loadAttendanceHistory() {
    let url = `/api/attendance/history/?period=${state.attendanceHistory.period}`;
    
    if (state.attendanceHistory.filter !== 'ALL') {
        url += `&record_type=${state.attendanceHistory.filter}`;
    }
    
    if (state.attendanceHistory.customStartDate && state.attendanceHistory.customEndDate) {
        url += `&start_date=${state.attendanceHistory.customStartDate}&end_date=${state.attendanceHistory.customEndDate}`;
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors du chargement de l\'historique');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                state.attendanceHistory.data = data;
                updateAttendanceHistoryUI();
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Afficher une notification d'erreur
        });
}

// Charger les demandes de congé
function loadLeaveRequests() {
    let url = `/api/leaves/?status=${state.leaveRequests.filter}`;
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des demandes');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                state.leaveRequests.data = data;
                updateLeaveRequestsUI();
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Afficher une notification d'erreur
        });
}

// Charger les détails d'une demande de congé
function loadLeaveRequestDetail(requestId) {
    fetch(`/api/leaves/${requestId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des détails de la demande');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                state.currentRequestDetail = data.leave;
                updateLeaveRequestDetailUI();
                requestDetailModal.classList.add('active');
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Afficher une notification d'erreur
        });
}

// Créer une nouvelle demande de congé
function createLeaveRequest(requestData) {
    fetch('/api/leaves/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken() // Voir la fonction utilitaire ci-dessous
        },
        body: JSON.stringify(requestData)
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Erreur lors de la création de la demande');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Fermer le modal et afficher une notification de succès
                newRequestModal.classList.remove('active');
                
                // Mettre à jour l'UI
                loadLeaveRequests();
                loadStatsData();
                
                showNotification('Demande créée avec succès !', 'success');
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showNotification(error.message, 'error');
        });
}

// Annuler une demande de congé
function cancelLeaveRequest(requestId) {
    fetch(`/api/leaves/${requestId}/action/?action=cancel`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Erreur lors de l\'annulation de la demande');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Fermer le modal et afficher une notification de succès
                requestDetailModal.classList.remove('active');
                
                // Mettre à jour l'UI
                loadLeaveRequests();
                loadStatsData();
                
                showNotification('Demande annulée avec succès !', 'success');
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showNotification(error.message, 'error');
        });
}

// ====== UI UPDATES ======

// Mettre à jour l'UI du profil
function updateProfileUI() {
    if (!state.profile) return;
    
    // Mettre à jour l'en-tête
    const userName = document.querySelector('.user-name');
    const userAvatar = document.querySelector('.user-avatar');
    if (userName && userAvatar && state.profile.name) {
        userName.textContent = state.profile.name;
        
        // Initialiser l'avatar avec les initiales (première lettre du prénom et du nom)
        const nameParts = state.profile.name.split(' ');
        const initials = nameParts.length > 1 
            ? (nameParts[0][0] + nameParts[1][0]).toUpperCase() 
            : nameParts[0][0].toUpperCase();
        userAvatar.textContent = initials;
    }
    
    // Mettre à jour la carte de profil
    const employeeName = document.querySelector('.employee-name');
    const employeeRole = document.querySelector('.employee-role');
    const employeeDept = document.querySelector('.employee-department');
    const employeeId = document.querySelector('.employee-id');
    const qrCode = document.querySelector('.qr-image');
    
    if (employeeName && state.profile.name) {
        employeeName.textContent = state.profile.name;
    }
    
    if (employeeRole && state.profile.role) {
        employeeRole.textContent = state.profile.role;
    }
    
    if (employeeDept && state.profile.department) {
        employeeDept.textContent = state.profile.department;
    }
    
    if (employeeId && state.profile.employee_id) {
        employeeId.textContent = `ID: ${state.profile.employee_id}`;
    }
    
    if (qrCode && state.profile.qr_code_image) {
        qrCode.src = state.profile.qr_code_image;
        qrCode.alt = 'Code QR personnel de ' + state.profile.name;
    }
}

// Mettre à jour l'UI des statistiques
function updateStatsUI() {
    if (!state.stats) return;
    
    // Mettre à jour les statistiques rapides
    const presenceValue = document.querySelector('.status-card:first-of-type .status-value');
    const presenceLabel = document.querySelector('.status-card:first-of-type .status-label');
    const leaveValue = document.querySelector('.status-card:last-of-type .status-value');
    
    if (presenceValue && state.stats.current_month) {
        presenceValue.textContent = state.stats.current_month.days_present;
        presenceLabel.textContent = state.stats.current_month.name;
    }
    
    if (leaveValue && state.stats.leave) {
        leaveValue.textContent = state.stats.leave.days_remaining;
    }
}

// Mettre à jour l'UI de l'historique des pointages
function updateAttendanceHistoryUI() {
    if (!state.attendanceHistory.data) return;
    
    const historyList = document.querySelector('.history-list');
    
    // Masquer le spinner de chargement
    const loader = document.getElementById('attendanceLoader');
    if (loader) {
        loader.style.display = 'none';
    }
    
    // Conserver l'en-tête
    const historyHeader = document.querySelector('.history-header');
    
    // Vider la liste actuelle (sauf l'en-tête)
    if (historyList) {
        // Supprimer tout sauf l'en-tête et le spinner
        Array.from(historyList.children).forEach(child => {
            if (!child.classList.contains('history-header') && !child.classList.contains('loading-spinner')) {
                child.remove();
            }
        });
    }
    
    // Ajouter les nouveaux éléments d'historique
    if (state.attendanceHistory.data.days && historyList) {
        if (state.attendanceHistory.data.total_records === 0) {
            // Aucun enregistrement
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <div class="empty-state-icon">📅</div>
                <div class="empty-state-text">Aucun pointage trouvé</div>
                <div class="empty-state-subtext">Aucun enregistrement pour cette période et ce filtre</div>
            `;
            historyList.appendChild(emptyState);
        } else {
            // Parcourir les jours et ajouter les enregistrements
            state.attendanceHistory.data.days.forEach(day => {
                // Ajouter une section pour le jour avec un en-tête
                const dayHeader = document.createElement('div');
                dayHeader.className = 'day-header';
                dayHeader.style.padding = '10px';
                dayHeader.style.backgroundColor = '#f7f9fa';
                dayHeader.style.fontWeight = 'bold';
                dayHeader.style.borderBottom = '1px solid #eee';
                dayHeader.style.marginTop = '10px';
                dayHeader.textContent = `${day.formatted_date} - Total: ${day.summary.formatted_duration}`;
                historyList.appendChild(dayHeader);
                
                // Pour chaque jour, ajouter les pointages
                day.records.forEach(record => {
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    
                    // Mapper les types d'enregistrement aux classes CSS
                    const statusMap = {
                        'IN': { class: 'status-in', text: 'Arrivée' },
                        'OUT': { class: 'status-out', text: 'Départ' },
                        'BREAK_START': { class: 'status-pause', text: 'Début Pause' },
                        'BREAK_END': { class: 'status-pause', text: 'Fin Pause' }
                    };
                    
                    const statusClass = statusMap[record.type]?.class || '';
                    const statusText = statusMap[record.type]?.text || record.type_display;
                    
                    // Formater l'heure (HH:MM)
                    const time = record.time.substring(0, 5);
                    
                    historyItem.innerHTML = `
                        <div class="history-date">${day.day_name}</div>
                        <div class="history-time">${time}</div>
                        <div><span class="history-status ${statusClass}">${statusText}</span></div>
                        <div class="history-duration">${record.note || '-'}</div>
                    `;
                    
                    historyList.appendChild(historyItem);
                });
            });
        }
    }
    
    // Mettre à jour la pagination
    updatePagination(
        state.attendanceHistory.data.current_page || 1, 
        state.attendanceHistory.data.total_pages || 1
    );
}

// Mettre à jour l'UI des demandes de congé
function updateLeaveRequestsUI() {
    if (!state.leaveRequests.data) return;
    
    // Mettre à jour les listes de demandes selon le statut
    const pendingList = document.getElementById('pendingRequestsList');
    const approvedList = document.getElementById('approvedRequestsList');
    const historyList = document.getElementById('historyRequestsList');
    
    // Masquer les spinners de chargement
    const loaders = document.querySelectorAll('.request-list .loading-spinner');
    loaders.forEach(loader => {
        loader.style.display = 'none';
    });
    
    // Vider les listes actuelles (sauf les loaders)
    [pendingList, approvedList, historyList].forEach(list => {
        if (list) {
            Array.from(list.children).forEach(child => {
                if (!child.classList.contains('loading-spinner')) {
                    child.remove();
                }
            });
        }
    });
    
    // Sélectionner la liste active selon le filtre
    let activeList;
    if (state.leaveRequests.filter === 'PENDING') {
        activeList = pendingList;
    } else if (state.leaveRequests.filter === 'APPROVED') {
        activeList = approvedList;
    } else {
        activeList = historyList;
    }
    
    // Ajouter les demandes à la liste active
    if (state.leaveRequests.data.leaves && activeList) {
        if (state.leaveRequests.data.leaves.length === 0) {
            // Aucune demande
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.style.padding = '2rem';
            emptyState.innerHTML = `
                <div class="empty-state-icon">📝</div>
                <div class="empty-state-text">Aucune demande trouvée</div>
                <div class="empty-state-subtext">
                    ${state.leaveRequests.filter === 'PENDING' ? 'Vous n\'avez pas de demande en attente' : 
                      state.leaveRequests.filter === 'APPROVED' ? 'Vous n\'avez pas de demande approuvée' : 
                      'Vous n\'avez pas de demande dans l\'historique'}
                </div>
            `;
            activeList.appendChild(emptyState);
        } else {
            // Ajouter chaque demande
            state.leaveRequests.data.leaves.forEach(leave => {
                const requestItem = document.createElement('div');
                requestItem.className = 'request-item';
                requestItem.setAttribute('data-request-id', leave.id);
                
                // Mapper les statuts aux classes CSS
                const statusMap = {
                    'PENDING': { class: 'status-pending', text: 'En attente' },
                    'APPROVED': { class: 'status-approved', text: 'Approuvé' },
                    'REJECTED': { class: 'status-rejected', text: 'Refusé' }
                };
                
                const statusClass = statusMap[leave.status]?.class || '';
                const statusText = statusMap[leave.status]?.text || leave.status_display;
                
                // Mapper les types de congé
                const typeMap = {
                    'VACATION': 'Congé annuel',
                    'SICK': 'Congé maladie',
                    'PERSONAL': 'Congé personnel',
                    'OTHER': 'Autre congé'
                };
                
                const typeText = typeMap[leave.type] || leave.type_display;
                
                requestItem.innerHTML = `
                    <div class="request-info">
                        <div class="request-type">${typeText}</div>
                        <div class="request-date">${leave.start_date_display} - ${leave.end_date_display} (${leave.duration} jour${leave.duration > 1 ? 's' : ''})</div>
                    </div>
                    <span class="request-status ${statusClass}">${statusText}</span>
                `;
                
                activeList.appendChild(requestItem);
            });
        }
        
        // Configurer les écouteurs d'événements pour les éléments de demande
        setupRequestItemListeners();
    }
}

// Mettre à jour l'UI des détails d'une demande
function updateLeaveRequestDetailUI() {
    if (!state.currentRequestDetail) return;
    
    const leave = state.currentRequestDetail;
    
    // Mettre à jour les champs du modal
    document.getElementById('detailType').textContent = leave.type_display;
    document.getElementById('detailPeriod').textContent = 
        `${leave.start_date_display} - ${leave.end_date_display} (${leave.duration} jour${leave.duration > 1 ? 's' : ''})`;
    document.getElementById('detailRequestDate').textContent = leave.request_date.split(' ')[0];
    
    // Statut
    const statusMap = {
        'PENDING': { class: 'status-pending', text: 'En attente' },
        'APPROVED': { class: 'status-approved', text: 'Approuvé' },
        'REJECTED': { class: 'status-rejected', text: 'Refusé' }
    };
    
    const statusClass = statusMap[leave.status]?.class || '';
    const statusText = statusMap[leave.status]?.text || leave.status_display;
    
    document.getElementById('detailStatus').innerHTML = `
        <span class="request-status ${statusClass}">${statusText}</span>
    `;
    
    // Motif
    document.getElementById('detailReason').textContent = leave.reason;
    
    // Informations de traitement (si applicable)
    const processingInfoGroup = document.getElementById('processingInfoGroup');
    const responseInfoGroup = document.getElementById('responseInfoGroup');
    
    if (leave.processed_by) {
        document.getElementById('detailProcessedBy').textContent = leave.processed_by;
        processingInfoGroup.style.display = 'flex';
    } else {
        processingInfoGroup.style.display = 'none';
    }
    
    if (leave.response_date) {
        document.getElementById('detailResponseDate').textContent = leave.response_date;
        responseInfoGroup.style.display = 'flex';
    } else {
        responseInfoGroup.style.display = 'none';
    }
    
    // Afficher/masquer le bouton d'annulation
    if (leave.can_cancel) {
        cancelRequestBtn.style.display = 'inline-block';
    } else {
        cancelRequestBtn.style.display = 'none';
    }
    
    // Mettre à jour la timeline
    updateStatusTimeline(leave.status);
}

// Mettre à jour la timeline de statut
function updateStatusTimeline(status) {
    const timelineIcons = document.querySelectorAll('.timeline-icon');
    const timelineLines = document.querySelectorAll('.timeline-line');
    
    // Réinitialiser
    timelineIcons.forEach(icon => icon.classList.remove('active'));
    timelineLines.forEach(line => line.classList.remove('active'));
    
    // Définir les étapes actives selon le statut
    if (status === 'PENDING') {
        // Étapes 1 et 2 actives (Soumise, En révision)
        if (timelineIcons[0]) timelineIcons[0].classList.add('active');
        if (timelineIcons[1]) timelineIcons[1].classList.add('active');
        if (timelineLines[0]) timelineLines[0].classList.add('active');
    } else if (status === 'APPROVED' || status === 'REJECTED') {
        // Toutes les étapes actives
        timelineIcons.forEach(icon => icon.classList.add('active'));
        timelineLines.forEach(line => line.classList.add('active'));
    }
}

// Mettre à jour la pagination
function updatePagination(currentPage = 1, totalPages = 1) {
    const pagination = document.querySelector('.pagination');
    if (!pagination) return;
    
    pagination.innerHTML = '';
    
    // Ajouter les boutons de pagination
    if (totalPages > 1) {
        // Page précédente
        if (currentPage > 1) {
            const prevBtn = document.createElement('div');
            prevBtn.className = 'page-item';
            prevBtn.textContent = '<';
            prevBtn.addEventListener('click', () => {
                // Charger la page précédente
                loadAttendanceHistoryPage(currentPage - 1);
            });
            pagination.appendChild(prevBtn);
        }
        
        // Pages numérotées
        const maxVisiblePages = 3;
        const startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('div');
            pageBtn.className = `page-item${i === currentPage ? ' active' : ''}`;
            pageBtn.textContent = i;
            
            if (i !== currentPage) {
                pageBtn.addEventListener('click', () => {
                    // Charger la page sélectionnée
                    loadAttendanceHistoryPage(i);
                });
            }
            
            pagination.appendChild(pageBtn);
        }
        
        // Page suivante
        if (currentPage < totalPages) {
            const nextBtn = document.createElement('div');
            nextBtn.className = 'page-item';
            nextBtn.textContent = '>';
            nextBtn.addEventListener('click', () => {
                // Charger la page suivante
                loadAttendanceHistoryPage(currentPage + 1);
            });
            pagination.appendChild(nextBtn);
        }
    }
}

// Charger une page spécifique de l'historique
function loadAttendanceHistoryPage(page) {
    // Modifier l'URL pour inclure le numéro de page
    let url = `/api/attendance/history/?period=${state.attendanceHistory.period}&page=${page}`;
    
    if (state.attendanceHistory.filter !== 'ALL') {
        url += `&record_type=${state.attendanceHistory.filter}`;
    }
    
    if (state.attendanceHistory.customStartDate && state.attendanceHistory.customEndDate) {
        url += `&start_date=${state.attendanceHistory.customStartDate}&end_date=${state.attendanceHistory.customEndDate}`;
    }
    
    // Charger les données
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors du chargement de l\'historique');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                state.attendanceHistory.data = data;
                updateAttendanceHistoryUI();
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Afficher une notification d'erreur
        });
}

// ====== UTILITIES ======

// Récupérer le token CSRF
function getCsrfToken() {
    const csrfCookie = document.cookie
        .split(';')
        .find(cookie => cookie.trim().startsWith('csrftoken='));
    
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    
    // Si pas de cookie, chercher dans un élément hidden du DOM
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        return csrfInput.value;
    }
    
    return '';
}

// Afficher une notification
function showNotification(message, type = 'info') {
    // Créer un élément de notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Ajouter au DOM
    document.body.appendChild(notification);
    
    // Animer l'entrée
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Supprimer après un délai
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Générer un QR code (fonction utilitaire si nécessaire)
function generateQRCode(data) {
    // Cette fonction peut être utilisée côté client si nécessaire,
    // mais dans notre cas c'est l'API qui fournit le QR code
    // On pourrait utiliser une bibliothèque comme qrcode.js
}