async function getPrediction() {
    const payload = {
        x: parseFloat(document.getElementById('x').value),
        y: parseFloat(document.getElementById('y').value),
        t: parseFloat(document.getElementById('t').value)
    };
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Server error');
        
        const data = await response.json();
        document.getElementById('tempValue').innerText = data.predicted_temperature.toFixed(6);
        document.getElementById('resultBox').style.display = 'block';
    } catch (error) {
        alert('Error reaching the inference engine.');
    }
}