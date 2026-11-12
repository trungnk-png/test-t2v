#!/usr/bin/env python3
"""
MiniMax H3 Universal Silent Prompt Node for ComfyUI
- Auto-detects context:
  * Landscape / Scenery (Không cảnh: biển, núi, thành phố, thiên nhiên) -> im lặng, không nhắc môi/miệng
  * Character / Human (Người: bất kỳ giới tính, phi giới tính) -> khóa cứng khẩu hình "lips remain firmly closed and motionless"
  * Animals, Objects, Tech -> im lặng hoàn toàn, không nhắc cơ miệng
- Automatically appends official silent schema:
  overall_soundscape: N/A
  non_diegetic_music: N/A
- User only needs to enter a normal prompt!
"""

import re
from typing import Dict, Any, Tuple

class MiniMaxH3SilentPrompt:
    HUMAN_KEYWORDS = [
        "girl", "girls", "boy", "boys", "child", "children", "kid", "kids", "baby", "babies",
        "toddler", "toddlers", "teen", "teenager", "teens", "youth", "student", "students",
        "pupil", "pupils", "man", "men", "woman", "women", "person", "people", "human", "humans",
        "individual", "individuals", "character", "characters", "figure", "figures", "face", "faces",
        "portrait", "portraits", "crowd", "crowds", "pedestrian", "pedestrians", "walker", "walkers",
        "someone", "somebody", "anyone", "stranger", "strangers", "passenger", "passengers",
        "worker", "workers", "athlete", "athletes", "dancer", "dancers", "model", "models",
        "monk", "monks", "priest", "priests", "soldier", "soldiers", "warrior", "warriors",
        "knight", "knights", "astronaut", "astronauts", "traveler", "travelers", "wanderer", "wanderers",
        "nomad", "nomads", "couple", "family", "parent", "parents", "mother", "father", "son", "daughter",
        "chef", "scientist", "pilot", "mage", "wizard", "hero", "villain", "protagonist", "subject", "subjects",
        "người", "cô gái", "chàng trai", "phụ nữ", "đàn ông", "nam giới", "nữ giới",
        "trẻ em", "em bé", "bé gái", "bé trai", "học sinh", "sinh viên", "nhân vật",
        "khuôn mặt", "chân dung", "lữ khách", "đám đông", "người đi bộ", "hành khách", "công nhân"
    ]

    ANIMAL_KEYWORDS = [
        "cat", "dog", "bird", "eagle", "owl", "wolf", "tiger", "lion", "horse",
        "dragon", "creature", "animal", "fox", "deer", "whale", "dolphin", "hawk",
        "chim", "chó", "mèo", "hổ", "sư tử", "ngựa", "đại bàng", "rồng", "thú"
    ]

    LANDSCAPE_KEYWORDS = [
        "mountain", "lake", "forest", "ocean", "sea", "river", "city", "street",
        "landscape", "scenery", "sky", "clouds", "sunset", "sunrise", "dawn", "dusk",
        "desert", "valley", "waterfall", "beach", "horizon", "nature", "woods",
        "ruins", "field", "canyon", "cyberpunk city", "scenic", "view",
        "phong cảnh", "thiên nhiên", "núi", "biển", "rừng", "hoàng hôn", "bình minh", "thành phố"
    ]

    OBJECT_KEYWORDS = [
        "car", "vehicle", "spaceship", "sword", "clock", "watch", "robot", "drone",
        "building", "house", "cabin", "castle", "temple", "crystal", "jewelry",
        "xe", "tàu", "ô tô", "vũ khí", "tòa nhà", "công nghệ"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                        "default": "A peaceful mountain lake at sunrise with drifting mist",
                        "tooltip": "Nhập prompt bình thường (tiếng Anh hoặc tiếng Việt). Node sẽ tự động format chuẩn MiniMax H3 và áp dụng cơ chế im lặng phù hợp với từng đối tượng."
                    }
                ),
                "mode": (
                    ["auto", "landscape (scenery)", "character (closed lips)", "animal (silent)", "object (silent)"],
                    {
                        "default": "auto",
                        "tooltip": "Auto tự động nhận diện phong cảnh, người, động vật hoặc đồ vật."
                    }
                ),
            },
            "optional": {
                "style": (
                    "STRING",
                    {
                        "default": "Cinematic, photorealistic 8k, live-action",
                        "tooltip": "Phong cách hình ảnh"
                    }
                ),
                "camera_motion": (
                    "STRING",
                    {
                        "default": "The camera pushes in with small amplitude at slow speed",
                        "tooltip": "Chuyển động camera tự nhiên"
                    }
                )
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("formatted_prompt", "category")
    FUNCTION = "process"
    CATEGORY = "MiniMax-H3"

    def process(self, prompt: str, mode: str = "auto", style: str = "Cinematic, photorealistic 8k, live-action", camera_motion: str = "The camera pushes in with small amplitude at slow speed"):
        text = prompt.strip()

        # If user already wrote a full 3-field MiniMax prompt, enforce silent soundscape
        if "integrated_multimodal_description:" in text:
            desc = text.split("overall_soundscape:")[0].strip()
            final_p = f"{desc}\n\noverall_soundscape: N/A\n\nnon_diegetic_music: N/A"
            return (final_p, "custom_schema")

        # Determine category
        if mode != "auto":
            category = mode.split()[0]
        else:
            t = text.lower()
            def match_any(keywords):
                pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
                return bool(re.search(pattern, t, re.IGNORECASE))

            if match_any(self.HUMAN_KEYWORDS):
                category = "character"
            elif match_any(self.ANIMAL_KEYWORDS):
                category = "animal"
            elif match_any(self.LANDSCAPE_KEYWORDS):
                category = "landscape"
            elif match_any(self.OBJECT_KEYWORDS):
                category = "object"
            else:
                category = "general"

        if category == "landscape":
            # 1. Cảnh vật / Không cảnh: Im lặng, chuyển động sương khói/môi trường, KHÔNG nhắc môi miệng
            body = (
                f"[Shot 1] {style}, a breathtaking wide scenic view frames {text}. "
                f"Natural atmospheric depth with subtle environmental motion—gentle breezes, shifting soft light, "
                f"and drifting mist across the vista. {camera_motion}, revealing rich textures, natural depth, "
                f"and serene photographic balance across the composition."
            )
        elif category == "character":
            # 2. Người (1 người như 'a girl' hoặc nhiều người như 'children goto school by walk'):
            # Khóa cứng khẩu hình closed lips, hoàn toàn không mấp máy miệng hay cử động môi
            body = (
                f"[Shot 1] {style}, a high-detail cinematic shot capturing {text}. "
                f"All individuals and subjects depicted maintain composed, contemplative expressions "
                f"with subtle, natural micro-movements in their posture and gaze. "
                f"Their lips remain firmly closed, perfectly motionless, with zero mouth, speaking, or lip movement throughout the entire shot. "
                f"{camera_motion}, keeping crisp focus on the subjects while the background softly blurs."
            )
        elif category == "animal":
            # 3. Động vật: Im lặng, cử động tự nhiên, không gán tiếng nói con người
            body = (
                f"[Shot 1] {style}, a detailed naturalistic shot frames {text}. "
                f"The creature exhibits lifelike biological presence, with alert subtle head shifts, "
                f"gentle natural breathing, and pristine fur or feather detail under organic natural lighting. "
                f"{camera_motion}, capturing the majestic essence and stillness of the subject."
            )
        elif category == "object":
            # 4. Vật thể / Xe cộ: Ánh sáng, chất liệu, khối lượng
            body = (
                f"[Shot 1] {style}, an exquisitely framed cinematic showcase of {text}. "
                f"Studio-grade or atmospheric lighting accentuates the refined surfaces, metallic or organic textures, "
                f"and precise structural craftsmanship. {camera_motion}, highlighting the silhouette, reflections, "
                f"and three-dimensional volume against an aesthetically harmonious environment."
            )
        else:
            # 5. Khác: Im lặng hoàn toàn, đảm bảo bất kỳ nhân vật hay sinh vật nào cũng khóa môi
            body = (
                f"[Shot 1] {style}, a compelling cinematic composition capturing {text}. "
                f"Rich visual fidelity, atmospheric lighting, and fluid spatial balance. "
                f"Any subjects or individuals present keep their lips firmly closed, perfectly motionless, without any mouth or lip movement throughout the entire shot. "
                f"{camera_motion}, preserving elegant visual pacing."
            )

        formatted_prompt = (
            f"integrated_multimodal_description: {body}\n\n"
            "overall_soundscape: N/A\n\n"
            "non_diegetic_music: N/A"
        )

        return (formatted_prompt, category)


NODE_CLASS_MAPPINGS = {
    "MiniMaxH3SilentPrompt": MiniMaxH3SilentPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxH3SilentPrompt": "MiniMax H3 Silent Universal Prompt",
}
