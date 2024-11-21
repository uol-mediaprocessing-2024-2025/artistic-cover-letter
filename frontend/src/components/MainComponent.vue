<script setup>
import { ref, watch } from 'vue';
import axios from 'axios';
import { store } from '../store'; // Import shared store to manage global state

// Reactive references
const fileBlob = ref(null); // Store the image as a Blob (either from upload or gallery)
const blurredImage = ref(null); // Stores the blurred image from the backend
const isLoading = ref(false);  // Boolean to show a loading spinner while the image is being processed
const displayedImage = ref(null); // Handles the image currently displayed (original/blurred)
const text = ref(null);
const errorMessage = ref(null);
const dropshadowintensity = ref(0);
const dropshadowradius = ref(0);

// Watch for changes in the selected image from the gallery
watch(
  () => store.selectedImage,
  async (newImage) => {
    if (newImage) {
      console.log("New image selected from gallery:", newImage);
      const response = await fetch(newImage);
      fileBlob.value = await response.blob();  // Convert gallery image to blob
      displayedImage.value = newImage; // Display the selected image
      blurredImage.value = null;
    }
  },
  { immediate: true }
);

// Handle image upload
const handleImageUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    fileBlob.value = file; // Store the uploaded file as a Blob
    displayedImage.value = URL.createObjectURL(file); // Display the uploaded image
    blurredImage.value = null;
    store.photoUrls.push(displayedImage.value); // Store the uploaded image in the global store
  }
};

// Send the uploaded image to the backend and apply a blur effect
const applyBlur = async () => {
  if (!fileBlob.value) return;

  // Show the loading spinner while the image is being processed
  isLoading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', fileBlob.value);  // Send the blob

    // Make a POST request to the backend API to apply the blur effect
    const response = await axios.post(`${store.apiUrl}/apply-blur`, formData, {
      responseType: 'blob'  // Expect binary data (blob)
    });

    // Update the blurred image
    blurredImage.value = URL.createObjectURL(response.data);
    displayedImage.value = blurredImage.value;
  } catch (error) {
    console.error('Failed to apply blur:', error);
  } finally {
    isLoading.value = false;
  }
};

// Trigger the file input dialog when the image field is clicked
const openFileDialog = () => document.querySelector('input[type="file"]').click();

// Toggle between original and blurred image
const toggleImage = () => {
  if (blurredImage.value && !isLoading.value) {
    displayedImage.value = displayedImage.value === blurredImage.value ? URL.createObjectURL(fileBlob.value) : blurredImage.value;
  }
};

// Reset image when 'X' is clicked
const resetImage = () => {
  fileBlob.value = null;
  blurredImage.value = null;
  displayedImage.value = null;
  document.querySelector('input[type="file"]').value = '';
};

const submitText = async () => {
  isLoading.value = true;
  try {
  const response = await axios.post(`${store.apiUrl}/submit-text`, text.valueOf().value, {
    headers: {
      'Content-Type': 'application/json',
    },
    responseType: 'blob'  // Expect binary data (blob)
  });
  blurredImage.value = URL.createObjectURL(response.data);
  displayedImage.value = blurredImage.value;
  errorMessage.value = null;
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error('Failure:', error);
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <!-- Main container to center the content on the screen -->
  <v-container class="d-flex flex-column align-center justify-center main-container">
    <!-- A card to contain the form and images -->
    <v-card elevation="2" class="pa-4 card-container">
      <!-- Card title -->
      <v-card-title class="justify-center">
        <h2>Artistic Cover Letter</h2>
      </v-card-title>
      <!-- Card content -->
      <v-text-field v-model="text" label="Enter your text" prepend-icon="mdi-format-text" @keyup.enter="submitText" :disabled="isLoading"></v-text-field>
      <v-card-text>
            <!-- Wrapper div for positioning the loading overlay -->
            <div class="image-wrapper">
              <v-img v-if="displayedImage" :src="displayedImage" max-height="300" contain @click.stop="toggleImage"
                  :class="{ 'clickable': blurredImage && !isLoading }">
                </v-img>
                <div class="d-flex align-center justify-center" v-else></div>
              <!-- Loading overlay with centered spinner -->
              <div v-if="isLoading" class="loading-overlay">
                <v-progress-circular indeterminate color="primary" size="50"></v-progress-circular>
              </div>
            </div>

      </v-card-text>
      <v-alert v-if="errorMessage && !isLoading" type="error"> {{ errorMessage }} </v-alert>
    </v-card>

    <!-- SETTINGS -->
    <v-card elevation="2" class="pa-4 card-container">
      <v-card-title>
        <h2>Settings (not functional)</h2>
      </v-card-title>

      <v-expansion-panels>
        <v-expansion-panel title="Dropshadow">
          <v-expansion-panel-text>
            <v-slider v-model="dropshadowintensity" label="Intensity" :max=100 :min=0>
              <template v-slot:append>
                <v-text-field v-model="dropshadowintensity" density="compact" style="width: 100px" type="number" hide-details single-line
                ></v-text-field>
              </template>
            </v-slider>
            <v-slider v-model="dropshadowradius" label="Radius" :max=100 :min=0>
              <template v-slot:append>
                <v-text-field v-model="dropshadowradius" density="compact" style="width: 100px" type="number" hide-details single-line
                ></v-text-field>
              </template>
            </v-slider>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card>
  </v-container>
</template>





<style scoped>
.main-container {
  height: 100vh;
}

.card-container {
  max-width: 800px;
  width: 100%;
}

.image-wrapper {
  position: relative;
}

.image-placeholder {
  cursor: pointer;
  height: 300px;
  background-color: #f5f5f5;
  border: 1px dashed #ccc;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #aaa;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
}

.reset-btn {
  position: absolute;
  top: 6px;
  right: 6px;
}

.clickable {
  cursor: pointer;
}

@media (max-width: 768px) {
  .image-placeholder {
    height: 200px;
  }
}
</style>