// static/js/qrcodescanner.js

// Assurez-vous que l'objet window.kiosk est disponible
if (!window.kiosk) {
    console.error("kiosk_main.js n'est pas chargé ou window.kiosk n'est pas défini.");
}

const QRScanner = (function () {
    const qrReaderElementId = "qr-reader"; // ID de l'élément où le scanner sera rendu
    const qrScanFeedbackEl = document.getElementById('qr-scan-feedback');
    const cameraSelectEl = document.getElementById('camera-select');
    const startQrScanBtn = document.getElementById('start-qr-scan-btn'); // Déjà défini dans kiosk_main, mais on peut le référencer

    let html5QrCode = null; // Instance de la bibliothèque html5-qrcode
    let currentCameraId = null;
    let isScannerActive = false;

    // Configuration du scanner QR
    const qrConfig = {
        fps: 10, // Images par seconde pour le scan
        qrbox: function(viewfinderWidth, viewfinderHeight) {
            // Calcule la taille de la boîte de scan (le carré au centre)
            // Inspiré de 2.JPG, une grande boîte carrée
            let minEdgePercentage = 0.7; // 70% de la plus petite dimension (largeur ou hauteur)
            let minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight);
            let qrboxSize = Math.floor(minEdgeSize * minEdgePercentage);
            return {
                width: qrboxSize,
                height: qrboxSize
            };
        },
        rememberLastUsedCamera: true,
        supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
        // experimentalFeatures: { शाहीद: true } // Pourrait être utile pour certaines optimisations
    };


    // Callback en cas de succès de scan
    const qrCodeSuccessCallback = async (decodedText, decodedResult) => {
        if (isScannerActive) {
            stop(); // Arrêter le scan pour éviter les lectures multiples
            setFeedback("QR Code détecté ! Traitement en cours...", "success");
            console.log(`QR Code détecté: ${decodedText}`, decodedResult);

            // Vibrer si l'API est disponible (feedback haptique)
            if (navigator.vibrate) {
                navigator.vibrate(200); // Vibration de 200ms
            }

            // Envoyer les données du QR code au backend
            try {
                const csrfToken = window.kiosk.getCSRFToken();
                const response = await fetch('/api/authenticate-card/', { // Assurez-vous que l'URL est correcte
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({ qr_code: decodedText }),
                });

                const data = await response.json();

                if (data.success) {
                    setFeedback("Authentification réussie !", "success");
                    // Appeler la fonction de kiosk_main.js pour gérer la suite
                    if (window.kiosk && typeof window.kiosk.handleAuthenticationSuccess === 'function') {
                        window.kiosk.handleAuthenticationSuccess(data);
                    } else {
                        console.error("window.kiosk.handleAuthenticationSuccess n'est pas disponible.");
                        setFeedback("Erreur interne: impossible de poursuivre.", "error");
                    }
                } else {
                    setFeedback(`Erreur: ${data.error || 'QR code non valide ou employé non trouvé.'}`, "error");
                     // Permettre un nouveau scan après un délai
                    setTimeout(() => {
                        if (document.getElementById(qrReaderElementId).offsetParent !== null) { // Si l'écran QR est toujours actif
                           startScanner(currentCameraId); // Redémarre avec la même caméra
                        }
                    }, 2000);
                }
            } catch (error) {
                console.error('Erreur lors de l’authentification par QR code:', error);
                setFeedback("Erreur de communication avec le serveur.", "error");
                setTimeout(() => {
                    if (document.getElementById(qrReaderElementId).offsetParent !== null) {
                       startScanner(currentCameraId);
                    }
                }, 2000);
            }
        }
    };

    // Callback en cas d'erreur de scan (pas nécessairement une erreur fatale, juste pas de QR trouvé)
    const qrCodeErrorCallback = (errorMessage) => {
        // console.warn(`Erreur de scan QR (souvent normal): ${errorMessage}`);
        // On pourrait afficher un feedback subtil ici, mais attention à ne pas surcharger l'utilisateur
        // setFeedback("Recherche de QR code...", "info"); // Peut être trop verbeux
    };

    // Met à jour le message de feedback sous le scanner
    function setFeedback(message, type = "info") { // type peut être 'info', 'success', 'error'
        if (qrScanFeedbackEl) {
            qrScanFeedbackEl.textContent = message;
            qrScanFeedbackEl.className = 'scan-feedback ' + type; // Pour styler différemment
        }
    }

    // Peuple le sélecteur de caméras
    function populateCameraSelect(cameras) {
        if (cameraSelectEl && cameras && cameras.length) {
            cameraSelectEl.innerHTML = ''; // Vider les anciennes options
            cameras.forEach(camera => {
                const option = document.createElement('option');
                option.value = camera.id;
                option.textContent = camera.label || `Caméra ${camera.id}`;
                cameraSelectEl.appendChild(option);
            });

            // Sélectionner la caméra précédemment utilisée ou la première par défaut
            if (currentCameraId && cameras.find(c => c.id === currentCameraId)) {
                cameraSelectEl.value = currentCameraId;
            } else {
                currentCameraId = cameras[0].id;
                cameraSelectEl.value = currentCameraId;
            }
            cameraSelectEl.style.display = 'inline-block'; // Afficher le sélecteur

            cameraSelectEl.removeEventListener('change', handleCameraChange); // Eviter les doublons
            cameraSelectEl.addEventListener('change', handleCameraChange);
        } else if (cameraSelectEl) {
            cameraSelectEl.style.display = 'none';
        }
    }

    // Gère le changement de caméra
    function handleCameraChange() {
        currentCameraId = cameraSelectEl.value;
        if (isScannerActive) {
            stopScanner().then(() => { // S'assurer que le scanner est arrêté avant de redémarrer
                startScanner(currentCameraId);
            }).catch(err => console.error("Erreur lors du changement de caméra", err));
        }
    }


    // Fonction pour démarrer le scan
    async function start() {
        if (isScannerActive) {
            console.log("Le scanner QR est déjà actif.");
            return;
        }

        setFeedback("Initialisation du scanner...", "info");

        // Créer une nouvelle instance si elle n'existe pas
        if (!html5QrCode) {
            html5QrCode = new Html5Qrcode(qrReaderElementId, { verbose: false });
        }


        try {
            const cameras = await Html5Qrcode.getCameras();
            if (cameras && cameras.length) {
                populateCameraSelect(cameras);
                // Si currentCameraId n'est pas encore défini, prendre la première caméra
                if (!currentCameraId && cameras.length > 0) {
                   currentCameraId = cameras[0].id; // Ou utiliser html5QrCode.getRunningTrackCameraId() si déjà actif
                }

                // Démarrer le scan avec la caméra sélectionnée (ou la dernière utilisée/par défaut)
                await html5QrCode.start(
                    currentCameraId || { facingMode: "environment" }, // Préférer la caméra arrière par défaut
                    qrConfig,
                    qrCodeSuccessCallback,
                    qrCodeErrorCallback
                );
                isScannerActive = true;
                setFeedback("Scanner activé. Placez le QR code dans le cadre.", "info");
                if (startQrScanBtn) startQrScanBtn.style.display = 'none'; // Cacher le bouton "Démarrer Scan"

                // Activer la ligne de scan animée (si vous l'avez en CSS)
                const qrReaderContainer = document.getElementById('qr-reader-container');
                if (qrReaderContainer) qrReaderContainer.classList.add('scanning');


            } else {
                setFeedback("Aucune caméra trouvée sur cet appareil.", "error");
                console.error("Aucune caméra trouvée.");
                if (startQrScanBtn) startQrScanBtn.style.display = 'block'; // Réafficher si erreur
            }
        } catch (err) {
            setFeedback(`Erreur lors du démarrage du scanner: ${err.message || err}`, "error");
            console.error("Erreur lors du démarrage du scanner QR: ", err);
            if (startQrScanBtn) startQrScanBtn.style.display = 'block'; // Réafficher si erreur
        }
    }

    // Fonction pour arrêter le scan
    async function stop() {
        if (html5QrCode && isScannerActive) {
            try {
                await html5QrCode.stop();
                console.log("Scanner QR arrêté.");
                isScannerActive = false;
                setFeedback("Scanner arrêté.", "info");

                // Désactiver la ligne de scan animée
                const qrReaderContainer = document.getElementById('qr-reader-container');
                if (qrReaderContainer) qrReaderContainer.classList.remove('scanning');

                if (startQrScanBtn) startQrScanBtn.style.display = 'block'; // Afficher le bouton pour redémarrer

            } catch (err) {
                console.error("Erreur lors de l'arrêt du scanner QR: ", err);
                setFeedback("Erreur lors de l'arrêt du scanner.", "error");
            }
        } else {
            console.log("Le scanner QR n'est pas actif ou n'est pas initialisé.");
        }
    }

    // Exposer les fonctions start et stop pour être appelées depuis kiosk_main.js ou d'autres parties
    // window.QRScanner est déjà créé implicitement par la structure (function() { ... })()
    // mais on peut l'assigner explicitement pour plus de clarté si on le souhaite.
    // Ou, mieux, écouter des événements personnalisés ou que kiosk_main appelle directement ces fonctions.
    // Pour l'instant, `kiosk_main.js` appelle `QRScanner.startScanner()` via `window.QRScanner`.
    return {
        startScanner: start,
        stopScanner: stop,
        isScannerActive: () => isScannerActive
    };

})();

// Pour que `kiosk_main.js` puisse appeler QRScanner.startScanner() et QRScanner.stopScanner()
window.QRScanner = QRScanner;

