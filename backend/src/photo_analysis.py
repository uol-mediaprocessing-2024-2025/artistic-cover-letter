import threading
from concurrent.futures import ThreadPoolExecutor
import os
import moondream as md
import psutil
import requests



# Bing AI helped me fix this model loading issue
class ModelLoader:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ModelLoader, cls).__new__(cls)
                    cls._instance.model = None
        return cls._instance

    def load_model(self, model_path):
        if self.model is None:
            print("Loading Moondream model...")
            self.model = md.vl(model=model_path)
        return self.model

def getSubjects(images):
    encoded_images = []
    if not os.path.isfile("backend/src/models/moondream-2b-int8.mf.gz"):
        print("Moondream model not found, downloading...")
        download_model(
            "https://huggingface.co/vikhyatk/moondream2/resolve/9dddae84d54db4ac56fe37817aeaeb502ed083e2/moondream-2b-int8.mf.gz?download=true",
            "backend/src/models/moondream-2b-int8.mf.gz"
        )
    model_loader = ModelLoader()
    model = model_loader.load_model("backend/src/models/moondream-2b-int8.mf.gz")

    def encode_image(image):
        return model.encode_image(image)
    def query(encoded_image):
        return model.query(encoded_image, "Please tell me the name of this place, if you can.")["answer"]

    # adjust workers to avoid using up all system memory
    available_memory = psutil.virtual_memory().available / 1024 / 1024 / 1024
    if available_memory <= 2: available_memory = 2
    encoding_workers = int(available_memory / 0.275)
    querying_workers = int(available_memory / 2)

    print("Encoding... (up to " + str(encoding_workers) + " workers)")
    with ThreadPoolExecutor(max_workers=encoding_workers) as executor:
        results = list(executor.map(encode_image, images))
    encoded_images.extend(results)
    print("Querying... (up to " + str(querying_workers) + " workers)")
    with ThreadPoolExecutor(max_workers=querying_workers) as executor:
        answers = list(executor.map(query, encoded_images))
    print("Done")
    print("Raw results: " + str(answers))
    results = []
    for answer in answers:
        if answer not in results:
            words = answer.split()
            if len(words) < 5:
                results.append(answer)
    return results

# Bing AI code
def download_model(url, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"Model downloaded successfully and saved to {save_path}")
    else:
        print(f"Failed to download model. Status code: {response.status_code}")

if __name__ == '__main__':
    main()