import os
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
import requests
from PIL import Image
from io import BytesIO
import uuid
import base64

 
 
# Remplacez par votre propre clé API Hugging Face
HUGGING_FACE_API_KEY = "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"

app = FastAPI()

# Définir le répertoire pour sauvegarder les images
IMAGES_DIR = "generated_images"

# Créer le répertoire s'il n'existe pas
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)



@app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <html>
        <head>
            <title>Générateur d'Images avec Stable Diffusion</title>
            <script>
                async function generateImage(event) {
                    event.preventDefault();
                    const form = event.target;
                    const formData = new FormData(form);

                    // Afficher le spinner de chargement
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('result').style.display = 'none';
                    document.getElementById('error').style.display = 'none';
                    document.getElementById('preview').style.display = 'none';

                    try {
                        const response = await fetch('/generate', {
                            method: 'POST',
                            body: formData
                        });

                        if (response.ok) {
                            const blob = await response.blob();
                            const imageUrl = URL.createObjectURL(blob);
                            document.getElementById('generated-image').src = imageUrl;
                            document.getElementById('result').style.display = 'block';
                        } else {
                            const error = await response.json();
                            document.getElementById('error').textContent = error.error || 'Erreur lors de la génération';
                            document.getElementById('error').style.display = 'block';
                        }
                    } catch (error) {
                        document.getElementById('error').textContent = 'Erreur lors de la requête';
                        document.getElementById('error').style.display = 'block';
                    } finally {
                        document.getElementById('loading').style.display = 'none';
                    }
                }

                function previewImage(event) {
                    const file = event.target.files[0];
                    if (file) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            document.getElementById('preview-image').src = e.target.result;
                            document.getElementById('preview').style.display = 'block';
                        }
                        reader.readAsDataURL(file);
                    }
                }
            </script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .input-group {
                    margin: 20px 0;
                }
                #loading {
                    display: none;
                    margin: 20px 0;
                    color: #2196F3;
                    font-weight: bold;
                }
                .spinner {
                    width: 50px;
                    height: 50px;
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #2196F3;
                    border-radius: 50%;
                    margin: 20px auto;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                #error {
                    display: none;
                    margin: 20px 0;
                    color: #f44336;
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #ffebee;
                }
                #result, #preview {
                    display: none;
                    margin: 20px 0;
                }
                img {
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                textarea {
                    width: 100%;
                    max-width: 500px;
                    margin: 10px 0;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    resize: vertical;
                }
                button {
                    padding: 12px 24px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: background-color 0.3s;
                }
                button:hover {
                    background-color: #45a049;
                }
                input[type="file"] {
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Générateur d'Images avec Stable Diffusion</h1>
                <form onsubmit="generateImage(event)">
                    <div class="input-group">
                        <label for="image">Image source (optionnelle) :</label><br>
                        <input type="file" id="image" name="image" accept="image/*" onchange="previewImage(event)">
                    </div>

                    <div id="preview">
                        <h3>Aperçu de l'image source :</h3>
                        <img id="preview-image" alt="Aperçu">
                    </div>

                    <div class="input-group">
                        <label for="prompt">Entrez votre description :</label><br>
                        <textarea 
                            id="prompt" 
                            name="prompt" 
                            rows="4" 
                            placeholder="Décrivez l'image que vous souhaitez générer..." 
                            required
                            minlength="3"
                            maxlength="1000"
                        ></textarea>
                    </div>

                    <button type="submit">Générer l'image</button>
                </form>

                <div id="loading">
                    <p>Génération de l'image en cours...</p>
                    <div class="spinner"></div>
                </div>

                <div id="error"></div>

                <div id="result">
                    <h3>Image générée :</h3>
                    <img id="generated-image" alt="Image générée">
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/generate")
async def generate_image(prompt: str = Form(...), image: UploadFile = File(None)):

    if image is not None and image.filename != "":
        print("Image reçue avec succès :", image.filename)
    else:
        print("Aucune image reçue")
        return

    contents = await image.read()
    img = Image.open(BytesIO(contents)).convert("RGB").resize((512, 512))
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    payload = {
        "inputs": prompt,
        "num_inference_steps": 50,  # Plus d'étapes pour améliorer la qualité
        "strength": 0.65,  # Pour un compromis entre l'image de base et la transformation
        "guidance_scale": 8.0,  # Un guidage plus fort pour obtenir un meilleur résultat par rapport au prompt
        "init_image": img_base64,  # L'image initiale sous forme de base64
        "seed": 42,  # Un seed pour la génération, permettant de reproduire les résultats
        "width": 512,  # Taille de l'image générée (largeur)
        "height": 768,  # Taille de l'image générée (hauteur)
        "style": "fashion, realism",  # Style artistique pour plus de réalisme
        "quality": "high",  # Qualité de l'image générée (plus élevé pour plus de détails)
    }

    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        # Vérifier si le contenu est une image
        content_type = response.headers.get('Content-Type')

        if response.status_code == 200 and 'image' in content_type:
            image_data = response.content
            try:
                image = Image.open(BytesIO(image_data))

                # Générer un nom de fichier unique avec timestamp
                file_name = f"image_{uuid.uuid4().hex}.png"

                # Créer le chemin complet du fichier
                file_path = os.path.join(IMAGES_DIR, file_name)

                # Sauvegarder l'image
                image.save(file_path)

                # Retourner le fichier
                return FileResponse(file_path, media_type="image/png")

            except Exception as e:
                return {"error": f"Erreur lors du traitement de l'image : {str(e)}"}

        elif 'json' in content_type:
            # Si la réponse est du JSON, afficher le message d'erreur
            error_message = response.json()
            return {
                "error": "Erreur API",
                "details": error_message
            }
        else:
            return {"error": "Contenu inattendu reçu depuis l'API"}

    except requests.exceptions.Timeout:
        return {"error": "La génération a dépassé le temps limite"}
    except Exception as e:
        return {"error": f"Erreur lors de la requête : {str(e)}"}



# Ajouter une route pour accéder aux images générées
@app.get("/images/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join(IMAGES_DIR, image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    return {"error": "Image non trouvée"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

    #tester ca marche
