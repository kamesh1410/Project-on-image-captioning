# app.py
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
from PIL import Image
import gradio as gr
import torch
import time
import threading
import random
import re

# Model setup (CPU-friendly)
model_name = "nlpconnect/vit-gpt2-image-captioning"
try:
    feature_extractor = ViTImageProcessor.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = VisionEncoderDecoderModel.from_pretrained(model_name)
except Exception as e:
    raise Exception(f"Failed to load model: {str(e)}")

# Define vibe prefixes with 10 variations each
vibe_prefixes = {
    "Fun": [
        ("Let’s party! ", "🎉🎈"),
        ("Having a blast! ", "🚀😄"),
        ("So much fun! ", "🎊🤗"),
        ("Living it up! ", "🌟🎶"),
        ("What a wild time! ", "🎡😜"),
        ("Non-stop fun! ", "🎮🎉"),
        ("Here for the vibes! ", "✨🎈"),
        ("Can’t stop the fun! ", "🎸😄"),
        ("This is epic! ", "🔥🎊"),
        ("Fun times ahead! ", "🏄‍♂️🌈")
    ],
    "Funny": [
        ("LOL, check this out: ", "😂🤣"),
        ("This is hilarious! ", "😆🤪"),
        ("I can’t stop laughing! ", "🤣😂"),
        ("What a goofy moment! ", "😜🤡"),
        ("This cracks me up! ", "😂😅"),
        ("Too funny to handle! ", "🤪😆"),
        ("Haha, look at this! ", "😄🤣"),
        ("This is a riot! ", "🤡😂"),
        ("Oh my gosh, so funny! ", "😅🤪"),
        ("Laughing so hard! ", "😂😜")
    ],
    "Serious": [
        ("Reflecting on this moment: ", "🤔🌌"),
        ("A deep thought: ", "📖🌙"),
        ("In quiet contemplation: ", "🕊️🌠"),
        ("This feels profound: ", "🌍💭"),
        ("A moment of clarity: ", "🧘‍♂️🌟"),
        ("Lost in thought: ", "📜🌌"),
        ("A serious reflection: ", "🖼️🤔"),
        ("Pondering life: ", "🌳💡"),
        ("This speaks to me: ", "📘🌙"),
        ("A thoughtful pause: ", "⏳🌠")
    ],
    "Cute": [
        ("Aww, so adorable! ", "🐾💖"),
        ("Too cute to handle! ", "🐻💕"),
        ("This melts my heart! ", "🐱💞"),
        ("So sweet and cute! ", "🐶💗"),
        ("Adorableness overload! ", "🐼💖"),
        ("This is precious! ", "🐾💓"),
        ("Cutest thing ever! ", "🐰💕"),
        ("Aww, look at this! ", "🐻💞"),
        ("So much cuteness! ", "🐱💗"),
        ("Heart-melting moment! ", "🐶💖")
    ],
    "Happy": [
        ("Feeling on top of the world! ", "😊🌟"),
        ("Pure joy right here! ", "🌈✨"),
        ("Happiness overload! ", "🎉😄"),
        ("So happy to be here! ", "🌞💖"),
        ("This brings me joy! ", "😊🌟"),
        ("Smiling from ear to ear! ", "🌈✨"),
        ("A happy moment captured! ", "🎉😄"),
        ("Feeling so blessed! ", "🌞💖"),
        ("This makes me so happy! ", "😊🌟"),
        ("Joyful vibes only! ", "🌈✨")
    ],
    "Sad": [
        ("A bittersweet moment: ", "😢💔"),
        ("Feeling a little blue: ", "🌧️😔"),
        ("This breaks my heart: ", "💔😢"),
        ("A touch of sadness: ", "🌙😔"),
        ("Missing this moment: ", "🕊️😢"),
        ("A heavy heart today: ", "💔🌧️"),
        ("This feels so sad: ", "😔🌙"),
        ("A moment of sorrow: ", "🌧️😢"),
        ("Feeling down: ", "💔😔"),
        ("A sad memory: ", "🕊️🌙")
    ]
}

# Vibe-specific descriptive words to enhance captions
vibe_descriptors = {
    "Fun": {
        "adjectives": ["vibrant", "lively", "energetic", "wild", "playful"],
        "phrases": ["having the time of their life", "dancing like nobody’s watching", "living their best moment"]
    },
    "Funny": {
        "adjectives": ["silly", "goofy", "hilarious", "wacky", "zany"],
        "phrases": ["making everyone laugh", "being a total clown", "pulling off a funny stunt"]
    },
    "Serious": {
        "adjectives": ["thoughtful", "majestic", "profound", "serene", "contemplative"],
        "phrases": ["lost in deep thought", "capturing a quiet moment", "reflecting on life’s beauty"]
    },
    "Cute": {
        "adjectives": ["fluffy", "adorable", "precious", "charming", "lovely"],
        "phrases": ["stealing my heart", "being the cutest ever", "melting everyone’s heart"]
    },
    "Happy": {
        "adjectives": ["joyful", "radiant", "cheerful", "blissful", "delighted"],
        "phrases": ["beaming with happiness", "spreading pure joy", "living a happy moment"]
    },
    "Sad": {
        "adjectives": ["melancholic", "touching", "heartfelt", "somber", "poignant"],
        "phrases": ["feeling a bit down", "capturing a tender moment", "lost in a sad memory"]
    }
}

# Dictionary for replacing generic words with more descriptive ones
word_replacements = {
    "dog": ["pup", "pooch", "furry friend"],
    "cat": ["kitty", "feline", "whiskered pal"],
    "sitting": ["lounging", "resting", "chilling"],
    "standing": ["posing", "gazing", "watching"],
    "grass": ["meadow", "field", "lawn"]
}

# Timeout wrapper to prevent hanging
def timeout_handler(func, args=(), kwargs={}, timeout_duration=30, default="Generation timed out. Please try again."):
    result = [default]
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            result[0] = f"Error during generation: {str(e)}"
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_duration)
    return result[0]

def enhance_caption(caption, vibe):
    # Step 1: Replace generic words with more descriptive ones
    for generic, replacements in word_replacements.items():
        if generic in caption.lower():
            replacement = random.choice(replacements)
            caption = re.sub(r'\b' + generic + r'\b', replacement, caption, flags=re.IGNORECASE)
    
    # Step 2: Add a vibe-specific adjective
    if vibe in vibe_descriptors:
        adjective = random.choice(vibe_descriptors[vibe]["adjectives"])
        # Find the first noun in the caption to add the adjective before it
        words = caption.split()
        for i, word in enumerate(words):
            if word.lower() in ["dog", "pup", "pooch", "cat", "kitty", "feline", "person", "child", "baby", "group", "scene"]:
                words[i] = f"{adjective} {word}"
                break
        caption = " ".join(words)
    
    # Step 3: Replace generic phrases with vibe-specific phrases
    generic_phrases = ["sitting on the grass", "standing in the field", "in the image"]
    for phrase in generic_phrases:
        if phrase in caption.lower():
            if vibe in vibe_descriptors:
                vibe_phrase = random.choice(vibe_descriptors[vibe]["phrases"])
                caption = caption.replace(phrase, vibe_phrase)
    
    return caption

def generate_caption(image, vibe, prompt=""):
    if image is None:
        return "Please upload an image to generate a caption."
    
    # Process the image
    try:
        pixel_values = feature_extractor(images=image, return_tensors="pt").pixel_values
    except Exception as e:
        return f"Error processing image: {str(e)}"
    
    # Generate caption with timeout
    def generate():
        with torch.no_grad():
            output_ids = model.generate(
                pixel_values,
                max_length=30,
                num_beams=3,
                early_stopping=True
            )
        caption = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return caption
    
    caption = timeout_handler(generate, timeout_duration=30)
    if "timed out" in caption or "Error" in caption:
        return caption
    
    # Enhance the caption
    caption = enhance_caption(caption, vibe)
    
    # Randomly select a vibe prefix and emojis
    if vibe in vibe_prefixes:
        prefix, emojis = random.choice(vibe_prefixes[vibe])
        caption = f"{prefix}{caption} {emojis}"
    
    # Incorporate prompt if provided (case-insensitive handling)
    if prompt:
        # Store the original prompt for display, but process it as lowercase for consistency
        prompt_display = prompt.strip()
        caption = f"{caption} ({prompt_display})"
    
    return caption

# Custom CSS and JavaScript
custom_css = """
/* Reset and base styles */
html, body {
    margin: 0;
    padding: 0;
    min-height: 100vh;
    font-family: 'Arial', sans-serif;
    overflow-x: hidden;
}

/* Main container */
.container {
    max-width: 90%;
    width: 600px;
    margin: 10px auto 0 auto; /* Minimal top margin */
    padding: 0; /* Remove padding */
    text-align: center;
    box-sizing: border-box;
}

/* Heading container with logo */
.heading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 0; /* Ensure no margin */
}

/* Gradient heading */
.gradient-text {
    background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-size: 2.5rem;
    font-weight: bold;
    position: relative;
    display: inline-block;
    margin: 0; /* Ensure no margin */
}
.gradient-text::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
}

/* Logo placeholder */
.logo-placeholder {
    font-size: 2rem;
    opacity: 0.7;
    margin: 0; /* Ensure no margin */
}

/* Description */
#desc {
    font-size: 1rem;
    margin: 2px 0 2px; /* Minimal margin */
    font-weight: 300;
}
body.dark-mode #desc {
    color: #e0e0e0;
}
body.light-mode #desc {
    color: #444;
}

/* Input area */
.input-area {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 15px;
    margin: 0; /* No margin */
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
body.light-mode .input-area {
    background: rgba(0, 0, 0, 0.1);
}

/* Vibe selection dropdown */
.vibe-select {
    margin: 5px 0; /* Reduced margin */
}
.vibe-select select {
    padding: 8px;
    font-size: 1rem;
    border-radius: 5px;
    border: 1px solid #ccc;
    width: 100%;
    max-width: 300px;
    background: #fff;
    color: #333;
    cursor: pointer;
}

/* Prompt input */
.prompt-input {
    margin: 5px 0; /* Reduced margin */
}
.prompt-input input {
    padding: 8px;
    font-size: 1rem;
    border-radius: 5px;
    border: 1px solid #ccc;
    width: 100%;
    max-width: 300px;
}

/* Buttons */
#toggle-mode, .gr-button-primary {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background 0.3s;
    margin: 5px; /* Reduced margin */
    font-size: 1rem;
}
#toggle-mode {
    background: #666;
    color: white;
}
#toggle-mode:hover {
    background: #888;
}
.gr-button-primary {
    background: #4CAF50;
    color: white;
}
.gr-button-primary:hover {
    background: #45a049;
}

/* Output area */
.output-area {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 15px;
    margin: 0; /* No margin */
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
body.light-mode .output-area {
    background: rgba(0, 0, 0, 0.1);
}

/* Override Gradio default styles */
.gradio-container, .gr-row, .gr-column {
    margin: 0 !important;
    padding: 0 !important;
}
.gr-input, .gr-textbox, .gr-file-upload {
    width: 100%;
    box-sizing: border-box;
    margin: 0 !important;
}
.gr-file-upload {
    border: 2px dashed #ccc;
    padding: 15px;
    border-radius: 5px;
}

/* Responsive design for mobile */
@media (max-width: 768px) {
    .container {
        margin: 5px auto 0 auto;
        padding: 0;
    }
    .gradient-text {
        font-size: 1.5rem; /* Further reduced for mobile */
    }
    .logo-placeholder {
        font-size: 1.2rem; /* Further reduced for mobile */
    }
    #desc {
        font-size: 0.8rem; /* Slightly smaller for mobile */
        margin: 1px 0 1px;
    }
    .input-area {
        padding: 10px; /* Reduced padding for mobile */
    }
    .vibe-select {
        margin: 2px 0; /* Further reduced margin */
    }
    .vibe-select select {
        font-size: 0.9rem;
        padding: 6px;
        max-width: 100%; /* Full width on mobile */
    }
    .prompt-input {
        margin: 2px 0; /* Further reduced margin */
    }
    .prompt-input input {
        font-size: 0.9rem;
        padding: 6px;
        max-width: 100%; /* Full width on mobile */
    }
    #toggle-mode, .gr-button-primary {
        padding: 10px 20px; /* Larger padding for touch */
        font-size: 0.9rem;
        margin: 3px; /* Reduced margin */
    }
    .output-area {
        padding: 10px; /* Reduced padding for mobile */
        margin: 0;
    }
}

/* Smooth transitions for better performance */
* {
    transition: background 0.3s ease, color 0.3s ease;
}

/* Loading spinner */
.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #fff;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 1s linear infinite;
    margin-left: 5px;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
"""

custom_js = """
document.addEventListener('DOMContentLoaded', () => {
    // Set default to dark mode and ensure class is applied to body
    console.log("Page loaded, applying dark-mode to body");
    if (!document.body.classList.contains('light-mode')) {
        document.body.classList.add('dark-mode');
    }

    // Fade-in animation for title
    const title = document.querySelector('.gradient-text');
    if (title) {
        title.style.opacity = '0';
        setTimeout(() => {
            title.style.transition = 'opacity 1s';
            title.style.opacity = '1';
        }, 100);
    }

    // Add loading spinner
    const submitBtn = document.querySelector('.gr-button-primary');
    if (submitBtn) {
        submitBtn.addEventListener('click', () => {
            submitBtn.innerHTML = 'Generating... <span class="spinner"></span>';
            submitBtn.disabled = true;
        });
    }

    // Debug toggle button
    const toggleBtn = document.querySelector('#toggle-mode');
    if (toggleBtn) {
        console.log("Toggle button found");
        toggleBtn.addEventListener('click', () => {
            console.log("Toggle button clicked");
        });
    } else {
        console.log("Toggle button not found");
    }
});

function toggleMode() {
    console.log("toggleMode function called");
    document.body.classList.toggle('dark-mode');
    document.body.classList.toggle('light-mode');
    console.log("Current classes on body:", document.body.classList);
}
"""

# Gradio Blocks Interface
with gr.Blocks(css=custom_css) as demo:
    with gr.Column(elem_classes="container"):
        # Heading and logo using Markdown
        gr.Markdown("""
            <div class="heading-container">
                <h1><span class="gradient-text">Image Caption Generator</span></h1>
                <div class="logo-placeholder">📸</div>
            </div>
            <p id="desc">Create engaging captions for your images using the ViT-GPT2 model</p>
        """)
        
        # Input section
        with gr.Group(elem_classes="input-area"):
            image_input = gr.Image(type="pil", label="Upload Image")
            vibe_input = gr.Dropdown(
                choices=["Fun", "Funny", "Serious", "Cute", "Happy", "Sad"],
                label="Choose a Vibe",
                value="Happy",
                elem_classes="vibe-select"
            )
            prompt_input = gr.Textbox(
                label="Additional Prompt (Optional)",
                placeholder="Add a hint for the caption...",
                elem_classes="prompt-input"
            )
        
        # Buttons
        submit_btn = gr.Button("Generate Caption", variant="primary")
        toggle_btn = gr.Button("Toggle Dark/Light Mode", elem_id="toggle-mode")
        
        # Output section
        with gr.Group(elem_classes="output-area"):
            caption_output = gr.Textbox(label="Generated Caption")
    
    # Event handlers
    submit_btn.click(fn=generate_caption, inputs=[image_input, vibe_input, prompt_input], outputs=caption_output)
    toggle_btn.click(fn=None, js="toggleMode", inputs=None, outputs=None)

if __name__ == "__main__":
    demo.launch(share=True)