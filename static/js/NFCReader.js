// static/js/NFCReader.js

if (!window.kiosk) {
    console.error("kiosk_main.js n'est pas chargé ou window.kiosk n'est pas défini.");
}

const NFCReader = (function () {
    const nfcStatusMessageEl = document.getElementById('nfc-status-message');
    const nfcAnimationEl = document.querySelector('#nfc-scanner-screen .nfc-icon-container'); // Pour l'animation

    let ndef = null; // Instance NDEFReader
    let abortController = null; // Pour pouvoir annuler le scan
    let isNFCAvailable = false;
    let isScanningNFC = false;

    function setNFCStatus(message, type = "info") { // type peut être 'info', 'success', 'error', 'scanning'
        if (nfcStatusMessageEl) {
            nfcStatusMessageEl.textContent = message;
            nfcStatusMessageEl.className = 'nfc-status ' + type; // Pour styler
        }
        if (nfcAnimationEl) {
            if (type === 'scanning') {
                nfcAnimationEl.style.display = 'flex'; // Assurez-vous que l'icône est visible
                nfcAnimationEl.classList.add('pulsing'); // Classe pour animation CSS
            } else {
                nfcAnimationEl.classList.remove('pulsing');
            }
        }
    }

    async function checkNFCPermission() {
        try {
            const permissionStatus = await navigator.permissions.query({ name: "nfc" });
            // permissionStatus.state peut être 'granted', 'denied', ou 'prompt'
            // 'granted': L'utilisateur a déjà donné la permission.
            // 'denied': L'utilisateur a refusé la permission.
            // 'prompt': L'utilisateur sera invité à donner la permission lorsque .scan() est appelé.
            console.log(`Statut de la permission NFC: ${permissionStatus.state}`);
            return permissionStatus.state;
        } catch (error) {
            console.error("Erreur lors de la vérification de la permission NFC:", error);
            setNFCStatus("Impossible de vérifier la permission NFC.", "error");
            return 'denied'; // Supposer refusé en cas d'erreur
        }
    }


    async function startScan() {
        if (!('NDEFReader' in window)) {
            setNFCStatus("L'API Web NFC n'est pas supportée par ce navigateur ou cet appareil.", "error");
            console.warn("Web NFC n'est pas supporté.");
            isNFCAvailable = false;
            // Optionnel : Cacher le bouton NFC dans kiosk_main.js si non supporté au chargement
            // document.getElementById('show-nfc-scanner-btn').style.display = 'none';
            return;
        }
        isNFCAvailable = true;

        if (isScanningNFC) {
            console.log("Scan NFC déjà en cours.");
            return;
        }

        const permissionState = await checkNFCPermission();
        if (permissionState === 'denied') {
            setNFCStatus("Permission NFC refusée. Veuillez l'activer dans les paramètres du navigateur.", "error");
            return;
        }

        try {
            if (!ndef) {
                ndef = new NDEFReader();
            }
            abortController = new AbortController(); // Créer un nouveau contrôleur pour chaque session de scan

            setNFCStatus("Approchez votre badge NFC...", "scanning");
            isScanningNFC = true;

            await ndef.scan({ signal: abortController.signal });
            console.log("Scan NFC démarré. En attente d'un tag...");

            ndef.addEventListener("readingerror", () => {
                if (isScanningNFC) { // Vérifier si on est toujours en mode scan
                    setNFCStatus("Erreur de lecture du tag NFC. Réessayez.", "error");
                    console.error("Erreur de lecture du tag NFC.");
                }
            });

            ndef.addEventListener("reading", async ({ message, serialNumber }) => {
                if (!isScanningNFC) return; // Si le scan a été annulé entre-temps

                isScanningNFC = false; // Arrêter de considérer comme en scan actif pour éviter lectures multiples
                abortController.abort(); // Arrêter le scan NFC actif après une lecture réussie

                const nfcId = serialNumber || extractNFCIdFromMessage(message); // Prioriser serialNumber si disponible

                if (nfcId) {
                    setNFCStatus(`Badge NFC détecté: ${nfcId}. Traitement...`, "success");
                    console.log(`Numéro de série: ${serialNumber}`);
                    message.records.forEach(record => {
                        console.log(`  Type de Record: ${record.recordType}`);
                        console.log(`  Type de Média: ${record.mediaType}`);
                        console.log(`  ID du Record: ${record.id}`);
                        if (record.recordType === "text") {
                            const textDecoder = new TextDecoder(record.encoding);
                            console.log(`  Texte: ${textDecoder.decode(record.data)}`);
                        }
                    });

                    // Vibrer si l'API est disponible
                    if (navigator.vibrate) {
                        navigator.vibrate(200);
                    }

                    // Envoyer l'ID NFC au backend
                    try {
                        const csrfToken = window.kiosk.getCSRFToken();
                        const response = await fetch('/api/authenticate-card/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken,
                            },
                            body: JSON.stringify({ nfc_id: nfcId }),
                        });
                        const data = await response.json();

                        if (data.success) {
                            setNFCStatus("Authentification NFC réussie !", "success");
                            if (window.kiosk && typeof window.kiosk.handleAuthenticationSuccess === 'function') {
                                window.kiosk.handleAuthenticationSuccess(data);
                            } else {
                                console.error("window.kiosk.handleAuthenticationSuccess n'est pas disponible.");
                                setNFCStatus("Erreur interne: impossible de poursuivre.", "error");
                            }
                        } else {
                            setNFCStatus(`Erreur: ${data.error || 'Badge NFC non valide ou employé non trouvé.'}`, "error");
                            // Permettre un nouveau scan après un délai si l'utilisateur est toujours sur l'écran NFC
                             setTimeout(() => {
                                if (document.getElementById('nfc-scanner-screen').classList.contains('active')) {
                                   startScan();
                                }
                            }, 2000);
                        }
                    } catch (error) {
                        console.error('Erreur lors de l’authentification par NFC:', error);
                        setNFCStatus("Erreur de communication avec le serveur.", "error");
                        setTimeout(() => {
                            if (document.getElementById('nfc-scanner-screen').classList.contains('active')) {
                               startScan();
                            }
                        }, 2000);
                    }

                } else {
                    setNFCStatus("Impossible d'extraire l'ID du badge NFC.", "error");
                    setTimeout(() => { // Permettre un nouveau scan
                        if (document.getElementById('nfc-scanner-screen').classList.contains('active')) {
                           startScan();
                        }
                    }, 2000);
                }
            });

        } catch (error) {
            console.error(`Erreur lors du démarrage du scan NFC: ${error}`);
            setNFCStatus(`Erreur NFC: ${error.message || error}`, "error");
            isScanningNFC = false;
            // Si l'erreur est due au fait que l'utilisateur a annulé la permission, ne pas redémarrer automatiquement.
            if (error.name === 'NotAllowedError') {
                setNFCStatus("Permission NFC refusée par l'utilisateur.", "error");
            } else {
                // Pour d'autres erreurs, on pourrait envisager un redémarrage
            }
        }
    }

    // Fonction pour extraire un ID NFC d'un message NDEF (simplifié)
    // Vous devrez adapter ceci à la structure de vos données sur les tags NFC
    function extractNFCIdFromMessage(message) {
        if (message && message.records) {
            for (const record of message.records) {
                if (record.recordType === "text") {
                    const textDecoder = new TextDecoder(record.encoding || 'utf-8');
                    return textDecoder.decode(record.data);
                }
                // Ajouter d'autres types de record si nécessaire (ex: "opaque", "url")
                // Pour les badges qui ne stockent pas en texte simple, il faudra une logique plus complexe
                // Souvent, le numéro de série du tag (serialNumber) est un bon identifiant unique.
            }
        }
        // Si aucun record textuel n'est trouvé, ou si vous utilisez le numéro de série comme ID principal,
        // et que serialNumber n'était pas disponible, vous pourriez retourner null.
        return null;
    }


    function stopScan() {
        if (abortController) {
            abortController.abort(); // Envoie un signal d'arrêt au scan en cours
            console.log("Tentative d'arrêt du scan NFC.");
        }
        isScanningNFC = false;
        setNFCStatus("Scan NFC arrêté.", "info");
    }

    // Initialisation : vérifier la disponibilité de l'API au chargement.
    // (kiosk_main.js appellera startScan() lorsque l'utilisateur clique sur le bouton NFC)
    function checkAvailability() {
        if (!('NDEFReader' in window)) {
            console.warn("Web NFC n'est pas supporté sur cet appareil/navigateur.");
            isNFCAvailable = false;
            // Optionnel: désactiver le bouton NFC dans kiosk.html
            const nfcButton = document.getElementById('show-nfc-scanner-btn');
            if (nfcButton) {
                // nfcButton.disabled = true;
                // nfcButton.title = "NFC non supporté sur cet appareil.";
                // Ou cacher le bouton: nfcButton.style.display = 'none';
            }
        } else {
            isNFCAvailable = true;
            console.log("Web NFC est potentiellement supporté.");
        }
    }
    // Exécuter la vérification une fois que le DOM est chargé
    // document.addEventListener('DOMContentLoaded', checkAvailability);
    // Ou appeler depuis kiosk_main si on veut gérer l'UI en fonction.
    // Pour l'instant, startScan() fera la vérification principale.


    return {
        startScan: startScan,
        stopScan: stopScan,
        isNFCAvailable: () => isNFCAvailable,
        isScanning: () => isScanningNFC
    };

})();

window.NFCReader = NFCReader;