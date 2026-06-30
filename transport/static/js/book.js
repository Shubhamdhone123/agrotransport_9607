
   document.addEventListener('DOMContentLoaded', function () {
    const manualDistance = document.getElementById('manualDistance');
    const goodsTypeSelect = document.querySelector('select:first-of-type');
    const calculatedAmount = document.getElementById('calculatedAmount');

    // Define base rates for different goods types
    const rates = {
        'furniture': { rate: 40, name: 'Furniture' },
        'electronics': { rate: 50, name: 'Electronics' },
        'perishable': { rate: 60, name: 'Perishable Goods' },
        'construction': { rate: 45, name: 'Construction Materials' }
    };

    function calculateTotal() {
        const distance = parseFloat(manualDistance.value) || 0;
        const selectedGoodsType = goodsTypeSelect.value;
        const goodsInfo = rates[selectedGoodsType];

        if (!distance || !goodsInfo) {
            calculatedAmount.value = 'Please fill in all required fields';
            return;
        }

        // Calculate total cost
        const totalCost = distance * goodsInfo.rate;

        // Display total with breakdown
        calculatedAmount.value = `₹${totalCost.toFixed(2)} (${distance}km × ₹${goodsInfo.rate}/km)`;
    }

    // Add event listeners for real-time calculation
    [manualDistance, goodsTypeSelect].forEach(element => {
        element.addEventListener('input', calculateTotal);
    });

    // Add validation for distance
    manualDistance.addEventListener('input', function () {
        if (this.value < 0) this.value = 0;
    });

    // Add styles for calculated amount field
    const style = document.createElement('style');
    style.textContent = `
        #calculatedAmount {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            background-color: #f8f9fa;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            width: 100%;
            margin-top: 5px;
            text-align: right;
        }

        #calculatedAmount:read-only {
            cursor: default;
            background-color: #f8f9fa;
        }

        .rates-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border: 1px solid #ddd;
        }

        .rates-info h4 {
            color: #333;
            margin-bottom: 10px;
        }

        .rates-info ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .rates-info li {
            margin-bottom: 5px;
            font-size: 14px;
            color: #666;
        }

        .form-group label {
            font-weight: 500;
            color: #333;
            margin-bottom: 8px;
            display: block;
        }
    `;
    document.head.appendChild(style);
});

