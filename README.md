# Image Caption Generator

![Image Caption Generator](https://img.shields.io/badge/Status-Active-brightgreen)  
Generate engaging captions for your images using the ViT-GPT2 model! This project provides a user-friendly web interface built with Gradio, allowing you to upload an image, choose a vibe (e.g., Fun, Funny, Serious), and add an optional prompt to create a customized caption.

The app is deployed on Hugging Face Spaces: [Image Caption Generator](https://huggingface.co/spaces/<your-username>/Image-Caption-Generator).

## Features
- **Image Captioning**: Uses the `nlpconnect/vit-gpt2-image-captioning` model to generate captions for uploaded images.
- **Vibe Selection**: Choose from six vibes (Fun, Funny, Serious, Cute, Happy, Sad) to customize the tone of the caption.
- **Additional Prompt**: Add an optional prompt to further personalize the caption.
- **Dark/Light Mode**: Toggle between dark and light themes for better usability.
- **Mobile Responsive**: Optimized for both desktop and mobile devices.
- **Enhanced Captions**: Captions are enhanced with vibe-specific prefixes, emojis, and descriptive words for a more engaging output.

## Demo
Try the app live on Hugging Face Spaces: [Image Caption Generator](https://huggingface.co/spaces/kamesh14/Image-Caption-Generator).

### Screenshots
#### Desktop View
![Desktop View](Screenshots/Desktop_view.PNG)


## Installation
To run the project locally, follow these steps:

### Prerequisites
- Python 3.8 or higher
- Git (optional, for cloning the repository)

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/kamesh1410/Image-Caption-Generator.git
   cd Image-Caption-Generator
