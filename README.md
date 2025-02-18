# Artistic Cover Letter

This software generates artistic combinations of letters and images.

This project utilizes the moondream AI model, which is licensed under the Apache 2.0 license. See the LICENSE file for more information.

## Prerequisites

- **Node.js** (for the frontend) - [Download here](https://nodejs.org/en/download/)
- **Python 3.10+** (for the backend) - [Download here](https://www.python.org/downloads/)
- **Conda** (for environment management) - [Install here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

---

## Setup Instructions

### 1. Backend Setup

1. **Navigate to the backend folder:**
   ```sh
   cd backend
   ```

2. **Set up the Python environment:**
   If you're using Conda, create and activate the environment:
   ```sh
   conda create --name simple-webapp python=3.10
   conda activate simple-webapp
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Run the backend server:**
   ```sh
   cd src
   python main.py
   ```

   Your backend should now be running at `http://localhost:8000`.

---

### 2. Frontend Setup

1. **Navigate to the frontend folder:**
   ```sh
   cd frontend
   ```

2. **Install the dependencies:**
   ```sh
   npm install
   ```

3. **Start the development server:**
   ```sh
   npm run dev
   ```

   Your frontend should now be running at `http://localhost:[PORT]`.

---

## Useful links
- **Vue3 Introduction:** https://vuejs.org/guide/introduction.html
- **Vuetify Documentation:** https://vuetifyjs.com/en/components/buttons/#usage
- **FastAPI Examples:** https://fastapi.tiangolo.com/tutorial/first-steps/