import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont  # pyre-ignore[21]
import random
import textwrap
import os
import io

import config
from huggingface_hub import InferenceClient  # pyre-ignore[21]

class CoverGenerator:
    """Generates book covers using Hugging Face Inference API with a professional local fallback."""

    # Upgrade to FLUX.1-dev for "serious" professional quality
    DEFAULT_MODEL = getattr(config, "IMAGE_MODEL", "black-forest-labs/FLUX.1-dev")

    @staticmethod
    async def generate(title: str, genre: str, output_path: Path) -> Path:
        """Generates an extreme-quality cover image using Hugging Face Inference API."""
        
        token = os.getenv("HF_TOKEN", config.HF_TOKEN)
        
        if not token:
            print("   ⚠️ No HF_TOKEN found. Using premium local render.")
            return CoverGenerator._generate_local_fallback(title, genre, output_path)

        # Extreme Quality Visual Archetypes
        archetypes = {
            "business": {
                "direction": "Serious Executive Minimalist. Highly structured architectural abstraction.",
                "details": "Brutalism style, sharp geometric shapes, glass and steel textures. Deep navy and matte silver colors. Low-angle perspective, massive scale.",
                "mood": "Authoritative, stable, ultra-modern, elite, corporate excellence."
            },
            "self-help": {
                "direction": "Ethereal Conceptual Photography. Symbolic high-end art.",
                "details": "Clean composition, single powerful symbolic object in soft dramatic spotlight. Pastel and neutral Earth tones. Shallow depth of field.",
                "mood": "Aspirational, serene, clarity, wisdom, high-value editorial."
            },
            "mystery": {
                "direction": "Atmospheric Noir. Suspenseful cinematic enigma.",
                "details": "Chiaroscuro lighting, deep obsidian shadows, high grain texture, mysterious blurred figure or silhouette. Crimson and deep shadow palette.",
                "mood": "Suspenseful, enigmatic, dark premium, psychological thriller."
            },
            "romance": {
                "direction": "Luxury Painterly Fine-Art. Sophisticated emotional depth.",
                "details": "Heavy impasto texture, sweeping fluid lighting, bokeh of golden light. Rich velvet textures, deep burgundy and gold palette.",
                "mood": "Elegant, passionate, timeless, soul-stirring, masterpiece gallery quality."
            },
            "sci-fi": {
                "direction": "Hyper-Detailed Futuristic Realism. Hard sci-fi aesthetic.",
                "details": "Macro photography of advanced circuits or cosmic phenomena, intricate textures of carbon fiber and obsidian. Neon cyan and deep space black.",
                "mood": "Complex, intellectual, vast, futuristic, precision-engineered."
            },
            "fantasy": {
                "direction": "Mythic Dark Realism. Grounded high-fantasy.",
                "details": "Ancient stone carvings, mossy textures, dim firelight, ominous misty landscapes. Emerald and weathered copper palette.",
                "mood": "Legendary, immersive, mythic, ancient, high-stakes adventure."
            },
            "non-fiction": {
                "direction": "Powerful Documentary Stills. Stark authoritative realism.",
                "details": "Documentary photography style, high contrast, powerful human element or historical relic. Monochrome or desaturated tones.",
                "mood": "Serious, factual, impactful, raw, historical significance."
            }
        }

        art = archetypes.get(genre.lower(), archetypes["non-fiction"])
        
        # Layering prompt for extreme results
        prompt = (
            f"PROFESSIONAL PUBLICATION COVER ART: {art['direction']}. "
            f"Visual Details: {art['details']}. "
            f"Mood: {art['mood']}. "
            f"Style: Cinematic High-End Photography, 8k, sharp focus, masterpiece composition. "
            "FRONT VIEW 2D ONLY. NO 3D mockups. NO text, letters, or numbers."
        )

        try:
            # TIER 1: FLUX.1-dev (Highest Quality, "Serious" professional output)
            print(f"   🎨 Tier 1: Generating ELITE cover via {CoverGenerator.DEFAULT_MODEL}...")
            client_dev = InferenceClient(model=CoverGenerator.DEFAULT_MODEL, token=token)
            
            try:
                # 45s timeout for the heavy model
                image = await asyncio.to_thread(
                    client_dev.text_to_image,
                    prompt,
                    guidance_scale=4.5,
                    num_inference_steps=28,
                    timeout=45
                )  # pyre-ignore[6]
                image.save(output_path)
                print(f"   ✅ [TIER 1] Elite Cover generated at {output_path}")
                return output_path
            except Exception as tier1_err:
                print(f"   ⚠️ [TIER 1] Failed or timed out: {tier1_err}")

            # TIER 2: FLUX.1-schnell (High Quality, very reliable)
            print(f"   🎨 Tier 2: Falling back to FLUX.1-schnell...")
            client_fast = InferenceClient(model="black-forest-labs/FLUX.1-schnell", token=token)
            image = await asyncio.to_thread(
                client_fast.text_to_image,
                prompt,
                guidance_scale=3.5,
                num_inference_steps=20
            )  # pyre-ignore[6]
            image.save(output_path)
            print(f"   ✅ [TIER 2] High-Quality Cover generated at {output_path}")
            return output_path

        except Exception as e:
            print(f"   ❌ Visual Engine Critical Failure: {e}. Executing Pillow fallback.")
            
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
