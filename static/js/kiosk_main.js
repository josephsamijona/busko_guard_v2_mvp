// static/js/kiosk_main.js

document.addEventListener('DOMContentLoaded', function () {
    // Éléments de l'interface
    const screens = {
        initial: document.getElementById('initial-screen'),
        qrScanner: document.getElementById('qr-scanner-screen'),
        nfcScanner: document.getElementById('nfc-scanner-screen'),
        employeeActions: document.getElementById('employee-actions-screen'),
    };
    const modals = {
        confirmation: document.getElementById('confirmation-modal'),
    };

    // Boutons de navigation principaux
    const showQrScannerBtn = document.getElementById('show-qr-scanner-btn');
    const showNfcScannerBtn = document.getElementById('show-nfc-scanner-btn');
    const backToInitialFromQrBtn = document.getElementById('back-to-initial-from-qr');
    const cancelNfcScanBtn = document.getElementById('cancel-nfc-scan-btn');
    const cancelEmployeeActionBtn = document.getElementById('cancel-employee-action-btn');
    const startQrScanBtn = document.getElementById('start-qr-scan-btn'); // Pour démarrer explicitement le scan

    // Éléments d'affichage
    const currentTimeEl = document.getElementById('current-time');
    const currentDateEl = document.getElementById('current-date');
    const employeeNameDisplay = document.getElementById('employee-name-display');
    const currentDatetimeActionDisplay = document.getElementById('current-datetime-action');
    const attendanceActionButtonsContainer = document.getElementById('attendance-action-buttons');

    // Éléments de la modale de confirmation
    const confirmationModal = document.getElementById('confirmation-modal');
    const closeConfirmationModalBtn = document.getElementById('close-confirmation-modal');
    const closeConfirmationDetailsBtn = document.getElementById('close-confirmation-details-btn');
    const confirmationIconEl = document.getElementById('confirmation-icon');
    const confirmationTitleEl = document.getElementById('confirmation-title');
    const confirmationDetailsEl = document.getElementById('confirmation-details');

    // Token CSRF (essentiel pour les requêtes POST vers Django)
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    // --- Gestion de l'affichage des écrans ---
    function showScreen(screenName) {
        // Cacher tous les écrans
        for (const key in screens) {
            if (screens[key]) {
                screens[key].classList.remove('active');
            }
        }
        // Afficher l'écran demandé
        if (screens[screenName]) {
            screens[screenName].classList.add('active');
        } else {
            console.error(`Screen "${screenName}" not found.`);
        }
    }

    // --- Gestion de l'horloge et de la date ---
    function updateDateTime() {
        const now = new Date();
        if (currentTimeEl) {
            currentTimeEl.textContent = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
        if (currentDateEl) {
            currentDateEl.textContent = now.toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        }
        if (currentDatetimeActionDisplay.offsetParent !== null) { // Check if visible
             currentDatetimeActionDisplay.textContent = `${now.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })} | ${now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
        }
    }

    // --- Gestion des Modales ---
    function showModal(modalName) {
        if (modals[modalName]) {
            modals[modalName].classList.add('active');
        }
    }

    function hideModal(modalName) {
        if (modals[modalName]) {
            modals[modalName].classList.remove('active');
        }
    }

    // Fonction pour afficher la modale de confirmation (inspiré de 4.JPG)
    function showConfirmationMessage(isSuccess, title, employeeName, recordDate, recordTime) {
        confirmationIconEl.innerHTML = isSuccess ?
            '<i class="fas fa-check-circle" style="color: var(--green-accent);"></i>' :
            '<i class="fas fa-times-circle" style="color: var(--red-accent);"></i>';
        confirmationTitleEl.textContent = title;

        let detailsHTML = '';
        if (employeeName) detailsHTML += `<p><strong>Employé:</strong> ${employeeName}</p>`;
        if (recordDate) detailsHTML += `<p><strong>Date:</strong> ${recordDate}</p>`;
        if (recordTime) detailsHTML += `<p><strong>Heure:</strong> ${recordTime}</p>`;
        confirmationDetailsEl.innerHTML = detailsHTML;

        confirmationModal.classList.add('active');
    }

    // --- Logique d'authentification et d'actions ---

    // Simule la réception des données de l'employé et des actions disponibles
    // Cette fonction sera appelée après une authentification réussie (QR ou NFC)
    function handleAuthenticationSuccess(employeeData) {
        // employeeData devrait contenir: { name, employee_id, department, role, available_actions }
        // (tel que retourné par votre vue Django `authenticate_card`)

        if (employeeNameDisplay) employeeNameDisplay.textContent = employeeData.name;
        // Vous pouvez ajouter l'affichage de l'ID, département, rôle si nécessaire ici
        // document.getElementById('employee-id-display').textContent = employeeData.employee_id;
        // document.getElementById('employee-department').textContent = employeeData.department;
        // document.getElementById('employee-role').textContent = employeeData.role;

        updateActionButtons(employeeData.available_actions, employeeData.employee_id);
        showScreen('employeeActions');
        updateDateTime(); // Mettre à jour l'heure sur l'écran des actions
    }

    // Met à jour les boutons d'action de présence (Arrivée, Départ, Pause)
    function updateActionButtons(actions, employeeId) {
        attendanceActionButtonsContainer.innerHTML = ''; // Vider les anciens boutons
        if (actions && actions.length > 0) {
            actions.forEach(action => {
                const button = document.createElement('button');
                button.classList.add('action-btn');
                // Ajout de classes spécifiques pour le style (doivent correspondre au CSS)
                let iconClass = 'fa-question-circle'; // Icône par défaut
                switch (action.value) {
                    case 'IN':
                        button.classList.add('arrival');
                        iconClass = 'fa-sign-in-alt';
                        break;
                    case 'OUT':
                        button.classList.add('departure');
                        iconClass = 'fa-sign-out-alt';
                        break;
                    case 'BREAK_START':
                        button.classList.add('break_start');
                        iconClass = 'fa-coffee';
                        break;
                    case 'BREAK_END':
                        button.classList.add('break_end');
                        iconClass = 'fa-mug-hot'; // ou fa-coffee
                        break;
                }
                button.innerHTML = `<i class="fas ${iconClass}"></i> ${action.label}`;
                button.dataset.action = action.value; // Ex: 'IN', 'OUT'
                button.dataset.employeeId = employeeId; // Stocker l'ID de l'employé pour la requête
                button.addEventListener('click', handleAttendanceAction);
                attendanceActionButtonsContainer.appendChild(button);
            });
        } else {
            attendanceActionButtonsContainer.innerHTML = '<p>Aucune action disponible pour le moment.</p>';
        }
    }

    // Gère le clic sur un bouton d'action de présence
    async function handleAttendanceAction(event) {
        const button = event.currentTarget;
        const recordType = button.dataset.action;
        const employeeId = button.dataset.employeeId;

        // Afficher un feedback de chargement (optionnel)
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';

        try {
            const response = await fetch('/api/record-attendance/', { // Assurez-vous que l'URL est correcte
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    employee_id: employeeId,
                    record_type: recordType,
                    // 'location' et 'note' peuvent être ajoutés ici si nécessaire
                }),
            });

            const data = await response.json();

            if (data.success) {
                // Parse timestamp: "14/05/2025 23:30:05" -> date and time parts
                const [respDate, respTime] = data.timestamp.split(' ');
                showConfirmationMessage(true, `Pointage '${data.record_type}' enregistré !`, data.employee_name, respDate, respTime);
                // Mettre à jour les actions disponibles après un pointage réussi
                if (data.available_actions) {
                    updateActionButtons(data.available_actions, employeeId);
                } else {
                    // Si pas d'actions, peut-être retourner à l'accueil ou afficher un message
                    showScreen('initial');
                }
            } else {
                showConfirmationMessage(false, "Erreur de Pointage", data.error || "Une erreur est survenue.", null, null);
                // Réactiver le bouton si erreur pour permettre une nouvelle tentative
                button.disabled = false;
                // Rétablir le texte original du bouton (nécessite de le stocker ou de le reconstruire)
                const iconClass = button.querySelector('i').className.replace('fas fa-spinner fa-spin', '').trim();
                button.innerHTML = `<i class="${iconClass}"></i> ${recordTypeToLabel(recordType)}`;
            }
        } catch (error) {
            console.error('Erreur lors de l’enregistrement du pointage:', error);
            showConfirmationMessage(false, "Erreur de Communication", "Impossible de contacter le serveur.", null, null);
            button.disabled = false;
            const iconClass = button.querySelector('i').className.replace('fas fa-spinner fa-spin', '').trim();
            button.innerHTML = `<i class="${iconClass}"></i> ${recordTypeToLabel(recordType)}`;
        }
    }

    // Fonction utilitaire pour convertir record_type en label (simplifié)
    function recordTypeToLabel(recordType) {
        switch (recordType) {
            case 'IN': return 'Arrivée';
            case 'OUT': return 'Départ';
            case 'BREAK_START': return 'Pause';
            case 'BREAK_END': return 'Fin de Pause';
            default: return recordType;
        }
    }


    // --- Initialisation et Écouteurs d'événements ---
    function init() {
        // Afficher l'écran initial au chargement
        showScreen('initial');

        // Mettre à jour l'horloge toutes les secondes
        updateDateTime();
        setInterval(updateDateTime, 1000);

        // Navigation
        if (showQrScannerBtn) {
            showQrScannerBtn.addEventListener('click', () => {
                showScreen('qrScanner');
                // Initialiser le scanner QR (sera dans qrcodescanner.js)
                // Par exemple: window.QRScanner.startScanner();
                // Pour l'instant, on simule le bouton "Démarrer Scan"
                if (startQrScanBtn) startQrScanBtn.style.display = 'block';
            });
        }

        if (showNfcScannerBtn) {
            showNfcScannerBtn.addEventListener('click', () => {
                showScreen('nfcScanner');
                // Initialiser le lecteur NFC (sera dans NFCReader.js)
                // Par exemple: window.NFCReader.startScan();
            });
        }

        if (backToInitialFromQrBtn) {
            backToInitialFromQrBtn.addEventListener('click', () => {
                // Arrêter le scanner QR si actif (sera dans qrcodescanner.js)
                // Par exemple: window.QRScanner.stopScanner();
                showScreen('initial');
            });
        }
        if (startQrScanBtn) {
             startQrScanBtn.addEventListener('click', () => {
                if (window.QRScanner && typeof window.QRScanner.startScanner === 'function') {
                    window.QRScanner.startScanner();
                    startQrScanBtn.style.display = 'none'; // Cacher après démarrage
                } else {
                    console.warn("QRScanner.startScanner non disponible. Le scan démarrera peut-être automatiquement.");
                }
            });
        }


        if (cancelNfcScanBtn) {
            cancelNfcScanBtn.addEventListener('click', () => {
                // Arrêter le scan NFC si actif (sera dans NFCReader.js)
                // Par exemple: window.NFCReader.stopScan();
                showScreen('initial');
            });
        }

        if (cancelEmployeeActionBtn) {
            cancelEmployeeActionBtn.addEventListener('click', () => {
                showScreen('initial');
                // Optionnel: déconnecter l'utilisateur ou vider les données de session employé
            });
        }

        // Fermeture de la modale de confirmation
        if (closeConfirmationModalBtn) {
            closeConfirmationModalBtn.addEventListener('click', () => confirmationModal.classList.remove('active'));
        }
        if (closeConfirmationDetailsBtn) {
            closeConfirmationDetailsBtn.addEventListener('click', () => confirmationModal.classList.remove('active'));
        }
        // Fermer la modale si on clique en dehors du contenu
        window.addEventListener('click', (event) => {
            if (event.target === confirmationModal) {
                confirmationModal.classList.remove('active');
            }
        });


        // Exposer des fonctions globalement si elles doivent être appelées par d'autres scripts (QR, NFC)
        window.kiosk = {
            handleAuthenticationSuccess: handleAuthenticationSuccess,
            showScreen: showScreen,
            getCSRFToken: () => csrfToken,
            showConfirmationMessage: showConfirmationMessage
            // ... d'autres fonctions si nécessaire
        };

    }

    // Lancer l'initialisation
    init();
});