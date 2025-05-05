from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from gemini import generate_quiz_questions_with_gemini
import uvicorn

app = FastAPI()

# Statik dosyalar ve HTML şablonları
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS ayarı (gerekirse frontend ile entegre için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Giriş sayfası
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Quiz üretimi
@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    level: str = Form(...),
    topic: str = Form(...),
    numQuestions: int = Form(...)
):
    prompt_level = f"{level} {topic} konusunda {numQuestions} adet çoktan seçmeli soru üret."
    questions = generate_quiz_questions_with_gemini(topic=topic, num_questions=numQuestions, level=level)

    if not questions:
        return HTMLResponse(content="<h3>Quiz üretilemedi. Lütfen tekrar deneyin.</h3>", status_code=500)

    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "questions": questions,
    })

# Sonuç analizi
@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request):
    form = await request.form()
    correct = 0
    user_answers = {}
    question_data = []

    for key in form:
        if key.startswith("q_"):
            qid = key[2:]
            selected = form[key]
            correct_answer = form.get(f"c_{qid}", "")
            is_correct = selected == correct_answer
            if is_correct:
                correct += 1
            user_answers[qid] = {
                "selected": selected,
                "correct": correct_answer,
                "is_correct": is_correct
            }

            question_data.append({
                "question": form.get(f"text_{qid}"),
                "selected": selected,
                "correct": correct_answer,
                "is_correct": is_correct,
                "options": {
                    "A": form.get(f"opt_{qid}_A"),
                    "B": form.get(f"opt_{qid}_B"),
                    "C": form.get(f"opt_{qid}_C"),
                    "D": form.get(f"opt_{qid}_D"),
                }
            })

    total = len(user_answers)
    wrong = total - correct
    percent = round((correct / total) * 100, 2) if total > 0 else 0

    return templates.TemplateResponse("result.html", {
        "request": request,
        "correct": correct,
        "wrong": wrong,
        "percent": percent,
        "total": total,
        "questions": question_data
    })



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
