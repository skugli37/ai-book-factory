import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont  # pyre-ignore[21]
import random
import textwrap
import os
import io

from config import HF_TOKEN  # pyre-ignore[21]
from huggingface_hub import InferenceClient  # pyre-ignore[21]

class CoverGenerator:
    """Generates book covers using Hugging Face Inference API with a professional local fallback."""

    # Fast and high-quality model for book covers
    # 'black-forest-labs/FLUX.1-schnell' is excellent for detail
    # 'stabilityai/stable-diffusion-xl-base-1.0' is a reliable alternative
    # Stable Diffusion XL is often better at following 'No Text' and '2D Flat' instructions
    DEFAULT_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

    @staticmethod
    async def generate(title: str, genre: str, output_path: Path) -> Path:
        """Generates a high-quality cover image using Hugging Face Inference API."""
        
        token = os.getenv("HF_TOKEN", HF_TOKEN)
        
        if not token:
            print("   ⚠️ No HF_TOKEN found in environment or config. Using premium local render.")
            return CoverGenerator._generate_local_fallback(title, genre, output_path)

        # Genre-specific style mapped to prompt templates
        style_map = {
            "self-help": "Conceptual photography, high-end minimalist design, aspirational mood, soft morning light, symbolic professional object, premium typography layout, clean white space, 8k",
            "romance": "Ethereal painterly style, elegant composition, sweeping emotional lighting, bokeh effect, soft textures, sophisticated color palette, cinematic romance",
            "mystery": "Low-key lighting, dramatic silhouettes, atmospheric fog, noir aesthetic, high contrast, sharp details, mysterious enigmatic visual metaphor, cinematic thriller",
            "business": "Architectural abstraction, glass and steel textures, geometric precision, corporate high-end aesthetic, royal blue and silver palette, authoritative and modern, 8k",
            "sci-fi": "Cyberpunk or space-opera aesthetic, hyper-detailed technology, glowing neon accents, vast scale, futuristic world-building, digital art masterpiece",
            "fantasy": "Mythic illustration, magical realism, epic landscape, glowing particles, rich textures, storybook high-fantasy art style, cinematic adventure",
            "non-fiction": "Deeply evocative photo-journalistic style or minimalist graphic design, stark lighting, powerful symbolic object, editorial quality, authoritative and sober, high-end magazine aesthetic"
        }

        style_prompt = style_map.get(genre.lower(), style_map["non-fiction"])
        
        # We prompt for blank space where the text will be overlaid by the KDP system or the local renderer
        # CRITICAL: We forbid text and 3D mockups to avoid hallucinations and "book-on-a-table" shots
        # We also avoid passing the title directly to the 'image' prompt if it's non-English to prevent the model from 'trying' to spell it.
        # Using 'Isolated flat graphic' and 'Symmetrical design' to force 2D and avoid 3D mockups.
        prompt = (
            f"Minimalist isolated flat graphic illustration on a plain solid background. {genre} theme. style: {style_prompt}. "
            "FRONT VIEW 2D ONLY. NO 3D, NO shadows, NO books, NO mockups, NO tables. "
            "ABSOLUTELY NO TEXT, NO LETTERS. "
            "Clean graphic design, professional publication quality."
        )

        try:
            print(f"   🎨 Generating AI cover via Hugging Face ({CoverGenerator.DEFAULT_MODEL})...")
            
            # Using the official InferenceClient for maximum reliability
            client = InferenceClient(model=CoverGenerator.DEFAULT_MODEL, token=token)
            
            # Generate image (Sync call in huggingface_hub, so we run in executor)
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(
                None, 
                lambda: client.text_to_image(prompt, guidance_scale=1.1, num_inference_steps=4)  # pyre-ignore[6]
            )
            
            # Save the image
            image.save(output_path)
            print(f"   ✅ AI Cover successfully generated at {output_path}")
            return output_path

        except Exception as e:
            print(f"   ⚠️ Hugging Face generation failed: {e}. Trying fallback...")
            
        # Fallback to high-quality Local Render (Pillow)
        return CoverGenerator._generate_local_fallback(title, genre, output_path)

    @staticmethod
    def _generate_local_fallback(title: str, genre: str, output_path: Path) -> Path:
        """Generates a premium-looking typography-based cover using Pillow."""
        width, height = 1600, 2560
        
        # Premium Palettes (Main, Accent, Text)
        palettes = {
            "self-help": ((25, 42, 86), (50, 67, 111), (255, 255, 255)),    # Midnight Blue
            "romance": ((120, 20, 50), (180, 40, 80), (255, 240, 245)),     # Deep Crimson
            "mystery": ((10, 10, 15), (30, 30, 45), (200, 200, 220)),      # Nightshade
            "business": ((0, 30, 60), (0, 50, 100), (240, 240, 240)),       # Executive Blue
            "sci-fi": ((0, 0, 20), (0, 40, 80), (0, 255, 255)),             # Electric Space
            "fantasy": ((40, 10, 60), (80, 20, 120), (255, 215, 0)),        # Royal Purple & Gold
            "non-fiction": ((30, 30, 30), (60, 60, 60), (255, 255, 255))    # Obsidian
        }
        
        c1, c2, text_color = palettes.get(genre.lower(), palettes["non-fiction"])
        
        # Create base image with a sophisticated vertical gradient
        base = Image.new('RGB', (width, height), c1)
        draw = ImageDraw.Draw(base)
        
        for y in range(height):
            r = int(c1[0] + (c2[0] - c1[0]) * (y / height))
            g = int(c1[1] + (c2[1] - c1[1]) * (y / height))
            b = int(c1[2] + (c2[2] - c1[2]) * (y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Load Premium Fonts (with fallbacks)
        try:
            # Serif for authority
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
            if not Path(font_path).exists():
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            
            title_font = ImageFont.truetype(font_path, 160)
            author_font = ImageFont.truetype(font_path, 85)
        except:
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()

        # Wrap and Draw Title with premium spacing
        title_lines = textwrap.wrap(title.upper(), width=14)
        
        current_y = height // 4
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            # Draw subtle drop shadow for depth
            draw.text(((width - w) / 2 + 4, current_y + 4), line, font=title_font, fill=(0, 0, 0, 120))
            draw.text(((width - w) / 2, current_y), line, font=title_font, fill=text_color)
            current_y += h + 40
            
        # Add a decorative line
        line_y = current_y + 60
        draw.line([(width//2 - 200, line_y), (width//2 + 200, line_y)], fill=text_color, width=8)

        # Footer Branding
        author_text = "AI BOOK FACTORY | PREMIUM COLLECTION"
        abox = draw.textbbox((0, 0), author_text, font=author_font)
        aw, ah = abox[2] - abox[0], abox[3] - abox[1]
        draw.text(((width - aw) / 2, height - 400), author_text, font=author_font, fill=text_color)

        # Draw a strong professional border
        border_width = 60
        draw.rectangle([border_width, border_width, width-border_width, height-border_width], outline=text_color, width=4)

        base.save(output_path, "PNG")
        print(f"   ✅ Premium Typography Cover generated at {output_path}")
        return output_path
