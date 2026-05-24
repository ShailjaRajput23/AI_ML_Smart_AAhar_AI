const imageUpload = document.getElementById('image-upload');
const previewArea = document.getElementById('preview-area');
const analyzeButton = document.getElementById('analyze-button');
const dishName = document.getElementById('dish-name');
const calorieCount = document.getElementById('calorie-count');
const swapSuggestion = document.getElementById('swap-suggestion');
const recommendationList = document.getElementById('recommendation-list');
const confidenceFill = document.getElementById('confidence-fill');

if (imageUpload) {
  imageUpload.addEventListener('change', handleFileSelect);
}

if (analyzeButton) {
  analyzeButton.addEventListener('click', runPrediction);
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  const url = URL.createObjectURL(file);
  previewArea.innerHTML = `<img src="${url}" alt="Uploaded meal image" />`;
}

function runPrediction() {
  if (!imageUpload || !imageUpload.files.length) {
    previewArea.textContent = 'Please select an image to analyze.';
    return;
  }

  const formData = new FormData();
  formData.append('image', imageUpload.files[0]);

  analyzeButton.disabled = true;
  analyzeButton.textContent = 'Analyzing...';
  recommendationList.innerHTML = '<p>Analyzing image with model...</p>';

  fetch('/predict', {
    method: 'POST',
    body: formData
  })
    .then(async (response) => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || 'Prediction failed.');
      }
      return data;
    })
    .then((data) => {
      const confidence = ((data.confidence || 0) * 100);
      const isFood = data.is_food !== false;
      dishName.textContent = isFood ? (data.prediction || '-') : 'Unknown / Non-food';
      calorieCount.textContent = `${confidence.toFixed(2)}%`;
      if (confidenceFill) {
        confidenceFill.style.width = `${Math.min(Math.max(confidence, 0), 100)}%`;
      }
      swapSuggestion.textContent = data.suggestions?.[0] || 'Try smaller portion sizes and add vegetables.';
      const details = isFood ? (data.food_details || {}) : {};
      const detailLines = [
        details.calories ? `Calories: ${details.calories}` : null,
        details.protein ? `Protein: ${details.protein}` : null,
        details.fat ? `Fat: ${details.fat}` : null,
        details.benefits ? `Benefits: ${details.benefits}` : null,
        details.healthy_alternative ? `Healthy Alternative: ${details.healthy_alternative}` : null
      ].filter(Boolean);
      const topPredictions = (data.top_predictions || [])
        .map((item) => `<li>${item.label}: ${(item.confidence * 100).toFixed(2)}%</li>`)
        .join('');
      recommendationList.innerHTML = `
        <ul>
          ${!isFood ? `<li><strong>${data.message || 'Image does not look like supported food.'}</strong></li>` : ''}
          ${detailLines.map(item => `<li>${item}</li>`).join('')}
          ${(data.suggestions || [
            'Prediction generated from uploaded image.',
            'Confidence score indicates model certainty.',
            'Use multiple clear photos for better results.'
          ]).map(item => `<li>${item}</li>`).join('')}
          ${topPredictions ? `<li><strong>Top predictions:</strong><ul>${topPredictions}</ul></li>` : ''}
          ${data.labels_aligned === false ? '<li><strong>Warning:</strong> Model output classes do not match API label list.</li>' : ''}
        </ul>
      `;
    })
    .catch((error) => {
      if (confidenceFill) {
        confidenceFill.style.width = '0%';
      }
      if ((error.message || '').toLowerCase().includes('login')) {
        window.location.href = '/login';
        return;
      }
      recommendationList.innerHTML = `<p>${error.message}</p>`;
    })
    .finally(() => {
      analyzeButton.disabled = false;
      analyzeButton.textContent = 'Analyze';
    });
}
