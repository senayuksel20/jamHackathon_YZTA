import google.generativeai as genai
from typing import List, Dict, Any
import re

genai.configure(api_key="write your api key") 
model = genai.GenerativeModel("gemini-2.0-flash")  # flash yerine pro da olabilir

def generate_quiz_questions_with_gemini(level: str, topic: str, num_questions: int) -> List[Dict[str, Any]]:
    prompt = f"""{level.capitalize()} düzeyinde {topic} konusunda {num_questions} adet çoktan seçmeli soru üret. Her soruya 4 seçenek (A, B, C, D) ekle ve doğru cevabı belirt. Format tam olarak şöyle olsun:

1. Soru metni?
A) Şık 1
B) Şık 2
C) Şık 3
D) Şık 4
Doğru Cevap: B

2. ...
"""

    try:
        response = model.generate_content(prompt)
        text_response = ""

        # Gemini cevabını yakala
        if hasattr(response, "text"):
            text_response = response.text
        else:
            text_response = response.candidates[0].content.parts[0].text

        print("Gemini çıktısı:\n", text_response)  # ← BURAYI log olarak ekle

        return _parse_gemini_output(text_response)
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        return []

def _parse_gemini_output(response_text: str) -> List[Dict[str, Any]]:
    questions = []
    blocks = response_text.strip().split("\n\n")

    for block in blocks:
        try:
            lines = block.strip().split("\n")
            question_line = lines[0].strip()
            question_text = re.sub(r"^\d+\.\s*", "", question_line)
            options = {}
            correct_option = ""

            for line in lines[1:]:
                if re.match(r"^[A-Da-d]\)", line):
                    opt_key = line[0].upper()
                    opt_value = line[2:].strip()
                    options[opt_key] = opt_value
                elif "Doğru Cevap" in line:
                    correct_option = line.split(":")[-1].strip().upper()

            if question_text and options and correct_option in options:
                questions.append({
                    "question": question_text,
                    "options": options,
                    "correct_option": correct_option
                })
        except Exception as e:
            print("Parse hatası:", e)
            continue

    return questions
