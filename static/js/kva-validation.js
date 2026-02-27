// Validation en temps réel du KVA dans les formulaires
document.addEventListener('DOMContentLoaded', function() {
    const kvaInputs = document.querySelectorAll('.kva-input');

    kvaInputs.forEach(input => {
        input.addEventListener('input', function() {
            validateKVAInput(this);
        });

        input.addEventListener('blur', function() {
            validateKVAInput(this, true);
        });
    });

    function validateKVAInput(inputElement, showError = false) {
        const value = inputElement.value.toUpperCase();
        const kvaMatch = value.match(/(\d+)\s*KVA/);

        if (kvaMatch) {
            const kva = parseInt(kvaMatch[1]);
            inputElement.style.borderColor = '#4CAF50';
            inputElement.style.backgroundColor = '#f8fff8';

            // Afficher le prix prévisionnel
            let prix = 0;
            if (kva <= 3) prix = 15000;
            else if (kva <= 5) prix = 20000;
            else if (kva <= 8) prix = 30000;
            else if (kva <= 16) prix = 35000;
            else prix = 45000;

            // Afficher ou mettre à jour l'info-bulle
            let tooltip = inputElement.parentNode.querySelector('.kva-tooltip');
            if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.className = 'kva-tooltip';
                tooltip.style.cssText = 'font-size: 12px; color: #4CAF50; margin-top: 5px;';
                inputElement.parentNode.appendChild(tooltip);
            }
            tooltip.innerHTML = `✓ ${kva}KVA détecté → Prix intervention: ${prix.toLocaleString()} FCFA`;
        } else {
            inputElement.style.borderColor = '#f44336';
            inputElement.style.backgroundColor = '#fff8f8';

            if (showError && value.trim() !== '') {
                let tooltip = inputElement.parentNode.querySelector('.kva-tooltip');
                if (!tooltip) {
                    tooltip = document.createElement('div');
                    tooltip.className = 'kva-tooltip';
                    tooltip.style.cssText = 'font-size: 12px; color: #f44336; margin-top: 5px;';
                    inputElement.parentNode.appendChild(tooltip);
                }
                tooltip.innerHTML = '✗ Format KVA non détecté. Ex: "5KVA" ou "3 KVA"';
            }
        }
    }
});