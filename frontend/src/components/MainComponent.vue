<script setup>
import {ref, watch} from 'vue';
import axios from 'axios';
import {store} from '../store'; // Import shared store to manage global state

// Reactive references
const fileBlob = ref(null); // Store the image as a Blob (either from upload or gallery)
const blurredImage = ref(null); // Stores the blurred image from the backend
const isLoading = ref(false);  // Boolean to show a loading spinner while the image is being processed
const displayedImage = ref(null); // Handles the image currently displayed (original/blurred)
const text = ref("Text");
const errorMessage = ref(null);
const resolution = ref("200");
const dropshadowintensity = ref(0);
const dropshadowradius = ref(10);
const dropshadowcolor = ref("#000000");
const bleedintensity = ref(0);
const bleedradius = ref(15);
const shadowradius = ref(15);
const shadowintensity = ref(0);
const shadowcolor = ref("#000000");

const fullImage = ref(null); //
const layer_0 = ref(null); //
const layer_1 = ref(null); //
const layer_2 = ref(null); //
const layer_3 = ref(null); //
const layer_4 = ref(null); //

const newlyUploadedFiles = ref([]);
const uploadedPhotos = ref([])


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
  errorMessage.value = null;
  if (!text.valueOf().value) return;
  if (resolution.valueOf().value > 1000) resolution.value = 1000;
  if (resolution.valueOf().value < 100) resolution.value = 100;
  try {
    const formData = new FormData();
    formData.append('text', text.valueOf().value);
    formData.append('resolution', resolution.valueOf().value);
    formData.append('dropshadow_radius', dropshadowradius.valueOf().value);
    formData.append('dropshadow_intensity', dropshadowintensity.valueOf().value);
    formData.append('dropshadow_color', dropshadowcolor.valueOf().value);
    formData.append('bleed_radius', bleedradius.valueOf().value);
    formData.append('bleed_intensity', bleedintensity.valueOf().value);
    formData.append('shadow_radius', shadowradius.valueOf().value);
    formData.append('shadow_intensity', shadowintensity.valueOf().value);
    formData.append('shadow_color', shadowcolor.valueOf().value);
    //  We need to send the uploaded photos here, but I can't get it to work
    const response = await axios.post(`${store.apiUrl}/submit-text`, formData, {});
  const imageArray = response.data;
  updateImages(imageArray);
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error('Failure:', error);
  } finally {
    isLoading.value = false;
  }
}

const updateImages = (imageArray) => {
  const blobArray = [];
  imageArray.forEach((base64Image, index) => {
      const binary = atob(base64Image);
      const array = [];
      for (let i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
      }
      const blob = new Blob([new Uint8Array(array)], { type: 'image/png' });
      blobArray[index] = URL.createObjectURL(blob);
    });
  fullImage.value = blobArray[0];
  layer_0.value = blobArray[1];
  layer_1.value = blobArray[2];
  layer_2.value = blobArray[3];
  layer_3.value = blobArray[4];
  layer_4.value = blobArray[5];
}

const changeDropshadow = async () => {
  if (resolution.valueOf().value > 200) {
    isLoading.value = true;
  }
  errorMessage.value = null;
  try {
    const formData = new FormData();
    formData.append('radius', dropshadowradius.valueOf().value);
    formData.append('intensity', dropshadowintensity.valueOf().value);
    formData.append('color', dropshadowcolor.valueOf().value);
    formData.append('resolution', resolution.valueOf().value);
    // Convert Images to blobs
    formData.append('layer0_blob', await fetch(layer_0.value).then(res => res.blob()));
    formData.append('layer2_blob', await fetch(layer_2.value).then(res => res.blob()));
    formData.append('layer3_blob', await fetch(layer_3.value).then(res => res.blob()));
    formData.append('layer4_blob', await fetch(layer_4.value).then(res => res.blob()));

    const response = await axios.post(`${store.apiUrl}/dropshadow`, formData, {});
    const imageArray = response.data;
    updateImages(imageArray);
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error("Failure:", error);
  } finally {
    isLoading.value = false;
  }
}

const changeBackgroundBleed = async () => {
  if (resolution.valueOf().value > 200){
    isLoading.value = true;
  }
  errorMessage.value = null;
  try {
    const formData = new FormData();
    formData.append('radius', bleedradius.valueOf().value);
    formData.append('intensity', bleedintensity.valueOf().value);
    formData.append('resolution', resolution.valueOf().value);
    // Convert Images to blobs
    formData.append('layer1_blob', await fetch(layer_1.value).then(res => res.blob()));
    formData.append('layer2_blob', await fetch(layer_2.value).then(res => res.blob()));
    formData.append('layer3_blob', await fetch(layer_3.value).then(res => res.blob()));
    formData.append('layer4_blob', await fetch(layer_4.value).then(res => res.blob()));

    const response = await axios.post(`${store.apiUrl}/background-bleed`, formData, {});
    const imageArray = response.data;
    updateImages(imageArray);
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error("Failure:", error);
  } finally {
    isLoading.value = false;
  }
}

const changeInnerShadow = async () => {
  if (resolution.valueOf().value > 200){
    isLoading.value = true;
  }
  errorMessage.value = null;
  try {
    const formData = new FormData();
    formData.append('radius', shadowradius.valueOf().value);
    formData.append('intensity', shadowintensity.valueOf().value);
    formData.append('resolution', resolution.valueOf().value);
    formData.append('color', shadowcolor.valueOf().value);
    formData.append('layer0_blob', await fetch(layer_0.value).then(res => res.blob()));
    formData.append('layer1_blob', await fetch(layer_1.value).then(res => res.blob()));
    formData.append('layer2_blob', await fetch(layer_2.value).then(res => res.blob()));
    formData.append('layer4_blob', await fetch(layer_4.value).then(res => res.blob()));

    const response = await axios.post(`${store.apiUrl}/inner-shadow`, formData, {});
    const imageArray = response.data;
    updateImages(imageArray);
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error("Failure:", error);
  } finally {
    isLoading.value = false;
  }
}

const downloadImage = async () => {
  if (fullImage.value){
    const link = document.createElement('a');
    link.href = fullImage.value;
    link.download = 'fullImage.png';
    link.click();
  }
}

const saveToGallery = async () => {
  store.photoUrls.push(fullImage.value)
}

const handleFileUpload = async() => {
  newlyUploadedFiles.value.forEach(file => {
    uploadedPhotos.value.push(new Blob([file], { type: 'image/jpeg' }));
  });
  try {
    await submitText()
  } finally {
    newlyUploadedFiles.value = null;
  }
}
</script>

<script>
  export default {
    data () {
      return {
        tickLabels: {
          200: 'Low Quality',
          400: 'Standard Quality',
          600: 'High Quality',
        },
      }
    },
  }
</script>

<template>
  <!-- Main container to center the content on the screen -->
  <v-container class="d-flex flex-column align-center justify-center main-container">
    <!-- A card to contain the form and images -->
    <v-card elevation="2" class="pa-4 card-container">
      <!-- Card title -->
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-pencil</v-icon>
        <h2>Create</h2>
      </v-card-title>
      <!-- Card content -->
      <v-text-field v-model="text" label="Enter your text" prepend-icon="mdi-format-text" @keyup.enter="submitText" :disabled="isLoading"></v-text-field>
      <v-file-input v-model="newlyUploadedFiles" label="Upload Images" multiple accept="image/*" @change="handleFileUpload" prepend-icon="mdi-upload" :disabled="isLoading"></v-file-input>
      <v-card-text>
            <!-- Wrapper div for positioning the loading overlay -->
            <div class="image-wrapper">
              <v-img v-if="fullImage" :src="fullImage" max-height="500">
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

    <!-- EFFECTS -->
    <v-card elevation="2" class="pa-4 card-container">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-creation</v-icon>
        <h2>Effects</h2>
      </v-card-title>
      <v-expansion-panels>
        <v-expansion-panel title="Dropshadow">
          <v-expansion-panel-text>
            <v-slider v-model="dropshadowintensity" label="Intensity" :step="1" :max=100 :min=0 @end="changeDropshadow" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="dropshadowintensity" density="compact" style="width: 100px" type="number" hide-details single-line @change="changeDropshadow" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-slider v-model="dropshadowradius" label="Radius" :step="1" :max=30 :min=1 @end="changeDropshadow" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="dropshadowradius" density="compact" style="width: 100px" type="number" hide-details single-line @change="changeDropshadow" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-color-picker v-model="dropshadowcolor" hide-canvas @change="changeDropshadow" class="ma-2" :disabled="isLoading"></v-color-picker>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <v-expansion-panel title="Bleed into background">
          <v-expansion-panel-text>
            <v-slider v-model="bleedintensity" label="Intensity" :step="1" :max=100 :min=0 @end="changeBackgroundBleed" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="bleedintensity" density="compact" style="width: 100px" type="number" hide-details single-line @change="changeBackgroundBleed" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-slider v-model="bleedradius" label="Radius" :step="1" :max=35 :min=1 @end="changeBackgroundBleed" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="bleedradius" density="compact" style="width: 100px" type="number" hide-details single-line @change="changeBackgroundBleed" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <v-expansion-panel title="Inner shadow">
          <v-expansion-panel-text>
            <v-slider v-model="shadowintensity" label="Intensity" :step="1" :max=100 :min=0 @end="changeInnerShadow" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="shadowintensity" density="compact" style="width: 100px" type="number" hide-details single-line @change="changeInnerShadow" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-slider v-model="shadowradius" label="Radius" :step="1" :max=30 :min=1 @end="changeInnerShadow" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="shadowradius" density="compact" style="width: 100px" type="number" hide-details single-line @change="changeInnerShadow" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-color-picker v-model="shadowcolor" hide-canvas @change="changeInnerShadow" class="ma-2" :disabled="isLoading"></v-color-picker>
          </v-expansion-panel-text>
        </v-expansion-panel>

      </v-expansion-panels>
      <!-- Layers for debugging
      <v-expansion-panels>
        <v-expansion-panel title="Layers (Debug)">
          <v-expansion-panel-text>
              layer0:
              <v-img v-if="layer_0" :src="layer_0" max-height="150"></v-img>
              layer1:
              <v-img v-if="layer_1" :src="layer_1" max-height="150"></v-img>
              layer2:
              <v-img v-if="layer_2" :src="layer_2" max-height="150"></v-img>
              layer3:
              <v-img v-if="layer_3" :src="layer_3" max-height="150"></v-img>
              layer4:
              <v-img v-if="layer_4" :src="layer_4" max-height="150"></v-img>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      -->
    </v-card>
    <v-card elevation="2" class="pa-4 card-container">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-export</v-icon>
        <h2>Export</h2>
      </v-card-title>
      <v-slider :min="200" :max="600" v-model="resolution" :ticks="tickLabels" show-ticks="always" step="200" tick-size="4" @end="submitText" :disabled="isLoading">
        <template v-slot:append>
          <v-text-field v-model="resolution" density="compact" style="width: 100px" type="number" hide-details single-line @change="submitText" :disabled="isLoading"
          ></v-text-field>
        </template>
      </v-slider>
      <v-btn @click="downloadImage">Download Image</v-btn>
      <v-btn @click="saveToGallery">Save to Gallery</v-btn>
    </v-card>
  </v-container>
</template>





<style scoped>
.main-container {
  height: 100vh;
}

.card-container {
  max-width: 1500px;
  width: 100%;
  margin-bottom: 3px;
  margin-top: 3px;
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
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .image-placeholder {
    height: 200px;
  }
}
</style>