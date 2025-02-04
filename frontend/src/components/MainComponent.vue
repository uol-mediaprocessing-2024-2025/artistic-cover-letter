<script setup>
import {onMounted, ref, reactive, watch} from 'vue';
import axios from 'axios';
import {store} from '../store';
import {themeState} from "@/views/theme.js"; // Import shared store to manage global state
import EditorComponent from "@/components/EditorComponent.vue";
import {green, red} from "vuetify/util/colors";
import {Photo} from "@/photo.js";

// Reactive references
const isLoading = ref(false);  // Boolean to show a loading spinner while the image is being processed

const errorMessage = ref(null); // String that holds an error message
const alertMessage = ref(null); // String that holds an alert message


const resolution = ref("250"); // Image resolution setting

// Dropshadow
const dropshadowintensity = ref(50);
const dropshadowradius = ref(15);
const dropshadowcolor = ref("#FFFFFF");
const dropshadowcolorauto = ref(true);
// Background bleed
const bleedintensity = ref(50);
const bleedradius = ref(15);
// Inner shadow
const shadowradius = ref(15);
const shadowintensity = ref(50);
const shadowcolor = ref("#000000");
const shadowcolorauto = ref(true);
// Outlines
const outlinewidth = ref(0);
const outlinecolor = ref("#000000");

// Text options
const text = ref("Text");
const selectedFont = ref("Impact");
const availableFonts = ref([]);
const weight = ref("bold");
const textSuggestions = ref(["Holiday","Vacation"]);
const fontSuggestions = ref(["Antonio", "Impact", "Bahnschrift", "Harvest", "Helvetica", "Raleway", "Tahoma", "Yu Gothic"])

// Image layers
const letterLayer = ref(null);
const fullImage = ref(null);


// Photo uploads
const newlyUploadedFiles = ref([]);
const uploadedPhotos = ref([])
const selectedPhotos = ref([]);

// UI elements
const photoPanel = ref(null);
const colorSchemePanel = ref(null);
const backgroundcolor = ref("#FFFFFF");
const suggestedbackgroundcolors = ref(["#222222","#666666","#BBBBBB"]);
const editorDialog = ref(null);
const editorIndex = ref(null);

// Color schemes and photo groups
const colorSchemes = ref([]);
const photoGroups = ref([]);
const selectedScheme = ref(0);

// onMounted is run when the page gets mounted in order to retrieve available fonts.
onMounted(async () => {
  await updatebackground()
  try {
    const response = await axios.post(`${store.apiUrl}/retrieve-fonts`, "", {});
    availableFonts.value = response.data
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error('Failure:', error);
  }
});

const analyzePhotos = async () => {
  if (uploadedPhotos.value.length === 0){
    alertMessage.value = "Please upload some photos to continue.";
    return;
  }
    isLoading.value = true;
    errorMessage.value = null;
    try {
      const formData = new FormData();
      for (const [index, URL] of uploadedPhotos.value.entries()) {
        const response = await fetch(URL._proxyURL);
        const blob = await response.blob();
        formData.append('photos', blob, `image.jpg`)
      }
      const response = await axios.post(`${store.apiUrl}/analyze-photos`, formData, {});
      const data = response.data
      colorSchemes.value = []
      photoGroups.value = []
      for (let i = 0; i < (data.length/2); i++) {
        colorSchemes.value.push(data[i])
        photoGroups.value.push(data[i+(data.length/2)])
      }
      colorSchemePanel.value = 0
    } catch (error) {
      errorMessage.value = "Internal server error.";
      console.error('Failure:', error);
    } finally {
    isLoading.value = false;
    alertMessage.value = null;
    selectedScheme.value = 0
    await updateColorScheme()
  }
}

const updateColorScheme = async () => {
  selectedPhotos.value.fill(false)
  const photoGroup = photoGroups.value[selectedScheme.valueOf().value]
  for (const [index, URL] of photoGroup.valueOf().entries()) {
    selectedPhotos.value[photoGroup.valueOf()[index]] = true;
  }
  await submitText()
  suggestedbackgroundcolors.value = colorSchemes.value[selectedScheme.value];
}

// Submits text to be processed by the backend
const submitText = async () => {
    if (!text.valueOf().value){
    alertMessage.value = "Please type in your text.";
    return;
  }
  if (uploadedPhotos.value.length === 0){
    alertMessage.value = "Please upload some photos to continue.";
    return;
  }
  if (selectedPhotos.value.every(value => value === false)){
    alertMessage.value = "Please select some photos to continue.";
    return
  }
  isLoading.value = true;
  errorMessage.value = null;
  if (resolution.valueOf().value > 1600) resolution.value = 1600;
  if (resolution.valueOf().value < 100) resolution.value = 100;
  if (resolution.valueOf().value > 750) alertMessage.value = "This might take a while, please wait.";
  try {
    const formData = new FormData();
    formData.append('text', text.valueOf().value);
    formData.append('font', selectedFont.valueOf().value);
    formData.append('resolution', resolution.valueOf().value);
    formData.append('dropshadow_radius', dropshadowradius.valueOf().value);
    formData.append('dropshadow_intensity', dropshadowintensity.valueOf().value);
    formData.append('dropshadow_color', dropshadowcolor.valueOf().value);
    formData.append('bleed_radius', bleedradius.valueOf().value);
    formData.append('bleed_intensity', bleedintensity.valueOf().value);
    formData.append('shadow_radius', shadowradius.valueOf().value);
    formData.append('shadow_intensity', shadowintensity.valueOf().value);
    formData.append('shadow_color', shadowcolor.valueOf().value);
    formData.append('outline_width', outlinewidth.valueOf().value);
    formData.append('outline_color', outlinecolor.valueOf().value);
    // I got it to work, yay
    for (const [index, URL] of uploadedPhotos.value.entries()) {
      if (selectedPhotos.value[index]){
        let response;
        if (resolution.valueOf().value <= 300) {
          response = await fetch(URL._proxyURL);
        } else {
          response = await fetch(URL._originalURL);
        }
        const blob = await response.blob();
        formData.append('photos', blob, `image.jpg`)
      }
    }
    const response = await axios.post(`${store.apiUrl}/submit-text`, formData, {});
  const imageArray = response.data;
  updateImages(imageArray);
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error('Failure:', error);
  } finally {
    isLoading.value = false;
    alertMessage.value = null;
  }
}

// Updates all images, called after receiving processed images from backend
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
  letterLayer.value = blobArray[0];
  fullImage.value = blobArray[1];
}

const applyEffects = async () => {
  if (uploadedPhotos.value.length === 0){
    alertMessage.value = "Please upload some photos to continue.";
    return;
  }
  if (resolution.valueOf().value > 250) {
    isLoading.value = true;
  }
  errorMessage.value = null;
  try {
    const formData = new FormData();
    formData.append('bleed_radius', bleedradius.valueOf().value);
    formData.append('bleed_intensity', bleedintensity.valueOf().value);
    formData.append('dropshadow_radius', dropshadowradius.valueOf().value);
    formData.append('dropshadow_intensity', dropshadowintensity.valueOf().value);
    formData.append('dropshadow_color', dropshadowcolor.valueOf().value);
    formData.append('shadow_radius', shadowradius.valueOf().value);
    formData.append('shadow_intensity', shadowintensity.valueOf().value);
    formData.append('shadow_color', shadowcolor.valueOf().value);
    formData.append('outline_width', outlinewidth.valueOf().value);
    formData.append('outline_color', outlinecolor.valueOf().value);
    formData.append('resolution', resolution.valueOf().value);
    // Convert Images to blobs
    formData.append('letter_layer_blob', await fetch(letterLayer.value).then(res => res.blob()));
    const response = await axios.post(`${store.apiUrl}/apply-effects`, formData, {});
    const imageArray = response.data;
    updateImages(imageArray);
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error("Failure:", error);
  } finally {
    isLoading.value = false;
  }
}

const updateTextSuggestions = async () => {
  if (selectedPhotos.value.every(value => value === false)){
    alertMessage.value = "Please select some photos to continue.";
    return
  }
  isLoading.value = true;
  errorMessage.value = null;
  alertMessage.value = "This might take a while, please wait.";
  try {
    const formData = new FormData();
    for (const [index, URL] of uploadedPhotos.value.entries()) {
      if (selectedPhotos.value[index]){
        const response = await fetch(URL._originalURL);
        const blob = await response.blob();
        formData.append('photos', blob, `image.jpg`)
      }
    }
    const response = await axios.post(`${store.apiUrl}/generate-suggestions`, formData, {});
    const suggestionsArray = response.data;
    textSuggestions.value = suggestionsArray;
  } catch (error) {
    errorMessage.value = "Internal server error.";
    console.error('Failure:', error);
  } finally {
    isLoading.value = false;
    alertMessage.value = null;
  }
}

const downloadImage = async () => {
  const link = document.createElement('a');
  link.href = fullImage.value;
  link.download = 'fullImage.png';
  link.click();
}

const saveToGallery = async () => {
  store.photoUrls.push(fullImage.value)
  alertMessage.value ="Image saved to gallery."
}

const handleFileUpload = async() => {
  try {
    isLoading.value = true;
    alertMessage.value = "Uploading photos...";
    const formData = new FormData();
    for (const file of newlyUploadedFiles.value) {
      formData.append('photos', file, `image.jpg`)
    }
    const response = await axios.post(`${store.apiUrl}/scale-images`, formData, {});
    const imageArray = response.data;
    const blobArray = [];
    imageArray.forEach((base64Image, index) => {
      const binary = atob(base64Image);
      const array = [];
      for (let i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
      }
      blobArray[index] = new Blob([new Uint8Array(array)], {type: 'image/png'});
    });
    blobArray.forEach((lowResBlob, index) => {
      const hiResBlob = new Blob([newlyUploadedFiles.value[index]], {type: 'image/jpeg'});
      uploadedPhotos.value.push(new Photo(hiResBlob, lowResBlob));
    })
    selectedPhotos.value.push(true);
  } catch (error) {
    errorMessage.value = "Internal server error.";
  } finally {
    isLoading.value = false;
    newlyUploadedFiles.value = null;
  }
  alertMessage.value = "Analyzing colors... Please wait.";
  await analyzePhotos()
}

const deleteAllPhotos = async () => {
  uploadedPhotos.value = []
  photoPanel.value = null;
  colorSchemePanel.value = null;
  fullImage.value = null;
  colorSchemes.value = null;
  photoGroups.value = null;
  await submitText()
}

const onWheel = async (event) => {
  if (!fullImage.value){
    event.preventDefault();
    event.stopPropagation();
    const index = availableFonts.value.indexOf(selectedFont.value)
    if (event.deltaY > 0) {
      selectedFont.value = availableFonts.value[(index+1)%availableFonts.value.length];
    } else {
      selectedFont.value = availableFonts.value[(index+availableFonts.value.length-1)%availableFonts.value.length];
    }
    await submitText();
  }
}

const updatebackground = async () => {
  const hex = backgroundcolor.valueOf().value.replace(/^#/, '');
  const r = parseInt(hex.slice(0, 2), 16)
  const g = parseInt(hex.slice(2, 4), 16)
  const b = parseInt(hex.slice(4, 6), 16)
  if (r < 140 & g < 140 & b < 140){
    if (!themeState.isDark){
      themeState.isDark = true;
      await updateShadows();
    }
  } else {
    if (themeState.isDark){
      themeState.isDark = false;
      await updateShadows();
    }
  }
}

const keyDown = async (event) => {
  const index = availableFonts.value.indexOf(selectedFont.value)
  if (event.key === 'ArrowRight') {
      selectedFont.value = availableFonts.value[(index+1)%availableFonts.value.length];
  }
  if (event.key === 'ArrowLeft'){
    selectedFont.value = availableFonts.value[(index+availableFonts.value.length-1)%availableFonts.value.length];
  }
}

async function updateShadows() {
  let update = false
  if (themeState.isDark) {
    if (dropshadowcolorauto){
      dropshadowcolor.value = "#000000"
      update = true
    }
    if (shadowcolorauto){
      shadowcolor.value = "#FFFFFF"
      update = true
    }
  } else {
    if (dropshadowcolorauto){
      shadowcolor.value = "#000000"
      update = true
    }
    if (shadowcolorauto){
      dropshadowcolor.value = "#FFFFFF"
      update = true
    }
  }
  if (update){
    await applyEffects()
  }
}

function deletePhoto(index){
  console.log("Delete Photo called");
  uploadedPhotos.value.splice(index, 1);
  selectedPhotos.value.splice(index, 1);
  console.log(uploadedPhotos);
  console.log(selectedPhotos);
}

function selectAllPhotos(boolean){
  selectedPhotos.value.fill(boolean);
  submitText();
}

function editPhoto(index){
  editorIndex.valueOf().value = index;
  editorDialog.valueOf().value = true;
}
</script>

<script>
  export default {
    data () {
      return {
        tickLabels: {
          250: 'Low Quality',
          500: 'Standard Quality',
          750: 'High Quality',
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
        <v-icon class="mr-2">mdi-format-font</v-icon>
        <h3>&nbsp;Text</h3>
      </v-card-title>
      <!-- Card content -->
      <v-text-field v-model="text" label="Enter your text" prepend-icon="mdi-format-text" @keyup.enter="submitText" :disabled="isLoading"></v-text-field>
      <v-row>
        <v-col>
          <v-btn @click="updateTextSuggestions" :disabled=isLoading prepend-icon="mdi-creation">Generate suggestions</v-btn>
          <v-btn v-for="suggestion in textSuggestions" @click="() =>{text = suggestion; submitText()}" :text=suggestion :disabled=isLoading> </v-btn>
        </v-col>
      </v-row>
      <v-select label="Select font" prepend-icon="mdi-format-font" :items="availableFonts" v-model="selectedFont" @wheel="onWheel" @keydown="keyDown" @update:modelValue="submitText" :disabled="isLoading"></v-select>
      <v-row>
        <v-col>
          <span v-for="suggestion in fontSuggestions" >
            <v-btn v-if="availableFonts.indexOf(suggestion) !== -1" @click="() =>{selectedFont = suggestion;submitText()}" :text=suggestion :disabled=isLoading></v-btn>
          </span>
        </v-col>
      </v-row>
      <!-- Bing AI helped me find the right style settings for the p tag.-->
      <div v-if="!fullImage"><p :style="{ margin: '12px', fontWeight: weight, fontFamily: selectedFont, fontSize: '5vw', maxHeight: '450px', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' , backgroundColor: backgroundcolor.valueOf()}"> {{text}} </p></div>
      <v-menu location="bottom" :close-on-content-click="false">
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" :disabled=isLoading prepend-icon="mdi-border-color"> Pick background color </v-btn>
        </template>
        <v-color-picker v-model="backgroundcolor" @update:model-value="updatebackground" class="ma-2" :disabled="isLoading" show-swatches mode="rgb" :swatches="[['#000000', '#FFFFFF']]"></v-color-picker>
      </v-menu>
      <v-btn @click="() =>{backgroundcolor = '#FFFFFF'; updatebackground() }" :disabled=isLoading> Set <div class="color-swatch" :style="{ backgroundColor: '#FFFFFF' }"></div></v-btn>
      <v-btn @click="() =>{backgroundcolor = '#000000'; updatebackground() }" :disabled=isLoading> Set <div class="color-swatch" :style="{ backgroundColor: '#000000' }"></div></v-btn>
      <v-btn
          v-for="suggestedbackgroundcolor in suggestedbackgroundcolors"
          @click="() =>{backgroundcolor = suggestedbackgroundcolor; updatebackground() }" :disabled=isLoading> Set
          <div class="color-swatch" :style="{ backgroundColor: suggestedbackgroundcolor }"></div>
      </v-btn>
    </v-card>
    <!-- PHOTOS -->
    <v-card elevation="2" class="pa-4 card-container">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-image-multiple</v-icon>
        <h3>&nbsp;Photos</h3>
      </v-card-title>
      <v-file-input v-model="newlyUploadedFiles" label="Upload photos" multiple accept="image/*" @change="handleFileUpload" prepend-icon="mdi-upload" :disabled="isLoading"></v-file-input>
      <v-expansion-panels v-model="photoPanel">
        <v-expansion-panel :title="'All photos (' + uploadedPhotos.length + ')'">
          <v-expansion-panel-text>
            <v-btn @click="selectAllPhotos(true)" :disabled="isLoading">Select all photos</v-btn>
            <v-btn @click="selectAllPhotos(false)" :disabled="isLoading">Deselect all photos</v-btn>
            <v-btn @click="deleteAllPhotos" :disabled="isLoading" color="error">Delete all photos</v-btn>
            <v-container>
              <v-row>
                <v-col  v-for="(photo, index) in uploadedPhotos" :key="index" md="2">
                  <v-card :class="{'deselected': !selectedPhotos[index]}" :disabled="isLoading">
                    <v-img :src="photo._proxyURL">
                      <v-btn icon density="compact" class="reset-btn ma-2" @click="deletePhoto(index)" color="error">
                        <v-icon small>mdi-close</v-icon>
                      </v-btn>
                      <v-btn icon density="compact" class="edit-btn ma-2" @click="editPhoto(index)" color="accent">
                        <v-icon small>mdi-image-edit</v-icon>
                      </v-btn>
                      <v-checkbox v-model="selectedPhotos[index]" @change="submitText" class="toggle ma-2" hide-details :disabled="isLoading"></v-checkbox>
                    </v-img>
                  </v-card>
                </v-col>
              </v-row>
            </v-container>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      <v-expansion-panels v-model="colorSchemePanel">
        <v-expansion-panel title="Color Schemes">
          <v-expansion-panel-text>
            <v-radio-group v-model="selectedScheme" @update:model-value="updateColorScheme" :disabled="isLoading">
              <v-row v-for="(scheme, index) in colorSchemes">
                <v-col cols="auto">
                  <v-radio :value=index ></v-radio>
                </v-col>
                <v-col>
                  <div style="display:flex; align-items: center;">
                    <div v-for="(color, colorIndex) in scheme" class="color-swatch-2" :key="colorIndex" :style="{ backgroundColor: color}"></div>
                  </div>
                </v-col>
              </v-row>
            </v-radio-group>
            <v-btn @click="analyzePhotos" :disabled="isLoading" prepend-icon="mdi-creation">Analyze Photo colors</v-btn>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card>
    <!-- VIEWPORT -->
    <v-card elevation="2" class="pa-4 card-container">
        <!-- Wrapper div for positioning the loading overlay -->
        <div class="image-wrapper">
          <v-img v-if="fullImage" :src="fullImage" max-height="450" :disabled="!fullImage" :style="{ backgroundColor: backgroundcolor.valueOf()}">
          </v-img>
          <div class="d-flex align-center justify-center" v-else></div>
          <!-- Loading overlay with centered spinner -->
          <div class="loading-overlay">
            <v-progress-circular v-if="isLoading" indeterminate color="primary" size="40"></v-progress-circular>
          </div>
          <div v-if="isLoading" class="loading-overlay" :style="{ backgroundColor: backgroundcolor.valueOf(), opacity: 0.4}">
          </div>
        </div>
      <v-alert v-if="alertMessage" type="info"> {{ alertMessage }}</v-alert>
      <v-alert v-if="errorMessage && !isLoading" type="error"> {{ errorMessage }} </v-alert>
    </v-card>
    <!-- EFFECTS -->
    <v-card elevation="2" class="pa-4 card-container">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-creation</v-icon>
        <h3>&nbsp;Effects</h3>
      </v-card-title>
      <v-expansion-panels>
        <v-expansion-panel title="Dropshadow">
          <v-expansion-panel-text>
            <v-slider v-model="dropshadowintensity" label="Intensity" :step="1" :max=100 :min=0 @end="applyEffects" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="dropshadowintensity" density="compact" style="width: 100px" type="number" hide-details single-line @change="applyEffects" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-slider v-model="dropshadowradius" label="Radius" :step="1" :max=30 :min=1 @end="applyEffects" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="dropshadowradius" density="compact" style="width: 100px" type="number" hide-details single-line @change="applyEffects" :disabled="isLoading"></v-text-field>
              </template>
            </v-slider>
            <v-checkbox v-model="dropshadowcolorauto" @update:model-value="updateShadows()" label="Adjust color to background"></v-checkbox>
            <v-color-picker v-model="dropshadowcolor" @update:model-value="applyEffects" class="ma-2" :disabled="isLoading || dropshadowcolorauto" hide-canvas :show-swatches="!dropshadowcolorauto" :hide-inputs="dropshadowcolorauto" mode="rgb" :swatches="[['#000000', '#FFFFFF']]"></v-color-picker>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <v-expansion-panel title="Bleed colors into background">
          <v-expansion-panel-text>
            <v-slider v-model="bleedintensity" label="Intensity" :step="1" :max=100 :min=0 @end="applyEffects" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="bleedintensity" density="compact" style="width: 100px" type="number" hide-details single-line @change="applyEffects" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-slider v-model="bleedradius" label="Radius" :step="1" :max=30 :min=1 @end="applyEffects" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="bleedradius" density="compact" style="width: 100px" type="number" hide-details single-line @change="applyEffects" :disabled="isLoading"></v-text-field>
              </template>
            </v-slider>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <v-expansion-panel title="Inner shadow">
          <v-expansion-panel-text>
            <v-slider v-model="shadowintensity" label="Intensity" :step="1" :max=100 :min=0 @end="applyEffects" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="shadowintensity" density="compact" style="width: 100px" type="number" hide-details single-line @change="applyEffects" :disabled="isLoading"></v-text-field>
              </template>
            </v-slider>
            <v-slider v-model="shadowradius" label="Radius" :step="1" :max=30 :min=1 @end="applyEffects" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="shadowradius" density="compact" style="width: 100px" type="number" hide-details single-line @change="applyEffects" :disabled="isLoading"
                ></v-text-field>
              </template>
            </v-slider>
            <v-checkbox v-model="shadowcolorauto" @update:model-value="updateShadows()" label="Adjust color to background"></v-checkbox>
            <v-color-picker v-model="shadowcolor" @update:model-value="applyEffects" class="ma-2" :disabled="isLoading || shadowcolorauto" hide-canvas :show-swatches="!shadowcolorauto" :hide-inputs="shadowcolorauto" mode="rgb" :swatches="[['#000000', '#FFFFFF']]"></v-color-picker>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <v-expansion-panel title="Outline">
          <v-expansion-panel-text>
            <v-slider v-model="outlinewidth" label="Width" :step="1" :max=100 :min=0 @end="applyEffects" :disabled="isLoading">
              <template v-slot:append>
                <v-text-field v-model="outlinewidth" density="compact" style="width: 100px" type="number" hide-details single-line @change="applyEffects" :disabled="isLoading"></v-text-field>
              </template>
            </v-slider>
            <v-color-picker v-model="outlinecolor" hide-canvas @update:model-value="applyEffects" class="ma-2" :disabled="isLoading" show-swatches mode="rgb" :swatches="[['#000000', '#FFFFFF']]"></v-color-picker>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card>
    <v-card elevation="2" class="pa-4 card-container">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-export</v-icon>
        <h3>&nbsp;Export</h3>
      </v-card-title>
      <v-slider :min="250" :max="750" v-model="resolution" :ticks="tickLabels" show-ticks="always" step="250" tick-size="4" @end="submitText" :disabled="isLoading">
        <template v-slot:append>
          <v-text-field v-model="resolution" density="compact" style="width: 100px" type="number" hide-details single-line @change="submitText" :disabled="isLoading"
          ></v-text-field>
        </template>
      </v-slider>
      <v-btn @click="downloadImage" :disabled="!fullImage">Download Image</v-btn>
      <v-btn @click="saveToGallery" :disabled="!fullImage">Save to Gallery</v-btn>
    </v-card>
  </v-container>

  <v-dialog v-model="editorDialog" max-width="600px">
    <v-card>
      <v-card-title class="headline">Image Editor</v-card-title>
        <v-card-text>
          <EditorComponent  :image-blob="uploadedPhotos[editorIndex]"/>
        </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="green darken-1" @click="editorDialog = false">Close</v-btn> </v-card-actions> </v-card>
  </v-dialog>
</template>





<style scoped>

.main-container {
  overflow: auto;
}

.card-container {
  max-width: 1200px;
  width: 100%;
  margin-bottom: 5px;
  margin-top: 5px;
  border-radius: 15px;
}

.v-expansion-panel{
  border-radius: 15px;
}

.image-wrapper {
  position: relative;
}

.v-slider{
  padding-left: 15px;
  padding-right: 15px;
  padding-top: 3px;
  padding-bottom: 3px;
}

.v-expansion-panels {
  margin-top: 5px
}

.v-card-title{
  padding-bottom:20px;
}

.v-btn{
  margin: 5px;
  border-radius: 15px;
}

.v-select{
  margin-top: 20px;
}

.color-swatch {
  width: 20px;
  height: 20px;
  margin-left: 8px;
  border: 1px solid #000000;
}

.color-swatch-2 {
  width: 30px;
  height: 24px;
  margin-top: 7px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 4px;
}

.reset-btn {
  position: absolute;
  top: 6px;
  right: 6px;
}

.toggle {
  position: absolute;
  bottom: -10px;
  left: 0px;
  padding-bottom: 0px;
  margin-bottom: 0px;
  color: #FFFFFF;
}

.deselected {
  opacity: 0.2;
}

.v-img {
  border-radius: 4px;
}

@media (max-width: 768px) {
  .image-placeholder {
    height: 200px;
  }
}
</style>