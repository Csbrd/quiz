import os
import json
from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

# 1. 설정값 로드
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# DB 접속 (한글 설정 포함)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. Gemini API 설정 (사용하시던 모델명 유지)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- DB 모델 정의 ---
class SolvedQuestion(db.Model):
    __tablename__ = 'solved_questions'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False) # JSON 문자열로 저장
    correct_answer = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text, nullable=False)

class UserResult(db.Model):
    __tablename__ = 'user_results'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    score = db.Column(db.Integer)

# --- 라우트 로직 ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    user_name = request.form.get('user_name')
    session['user_name'] = user_name
    
    # 1. 중복 방지: 최근 저장된 문제 20개 가져오기
    past_questions = SolvedQuestion.query.order_by(SolvedQuestion.id.desc()).limit(20).all()
    past_texts = [q.question_text for q in past_questions]

    prompt = f"""
    너는 정보처리기사 및 네트워크관리사 출제 위원이야.
    중복 금지 목록: {past_texts}
    
    다음 주제에 대해 CS 기술면접 질문으로 나올 법한 객관식 문제 10개를 JSON 형식으로 생성해줘.
    주제: TCP/IP, OSI 7계층, 라우팅, 보안 인프라, 클라우드 가상화.

    응답 형식:
    [
      {{
        "question": "문제 내용",
        "options": ["보기1", "보기2", "보기3", "보기4"],
        "answer": "정답 내용(보기 중 하나와 완전히 일치해야 함)",
        "explanation": "해당 정답의 이유와 오답들에 대한 상세한 설명"
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        text = response.text
        # JSON 추출 로직 (마크다운 태그 제거)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        quiz_data = json.loads(text.strip())

        # [핵심] 생성된 문제를 DB에 먼저 저장하고 ID만 세션에 담기
        current_quiz_ids = []
        for q in quiz_data:
            new_q = SolvedQuestion(
                question_text=q['question'],
                options=json.dumps(q['options'], ensure_ascii=False),
                correct_answer=q['answer'],
                explanation=q['explanation']
            )
            db.session.add(new_q)
            db.session.flush()  # DB에 반영하여 ID 생성
            current_quiz_ids.append(new_q.id)
        
        db.session.commit()
        session['quiz_ids'] = current_quiz_ids # 무거운 데이터 대신 ID 리스트만 저장 (4KB 제한 해결)
        
        return render_template('quiz.html', quiz=quiz_data)
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in start_quiz: {e}")
        return f"문제 생성 중 오류가 발생했습니다: {str(e)}"

@app.route('/submit', methods=['POST'])
def submit():
    user_name = session.get('user_name', '알 수 없는 사용자')
    quiz_ids = session.get('quiz_ids')
    
    # 세션에 데이터가 없으면 다시 메인으로
    if not quiz_ids:
        print("세션에 퀴즈 ID가 없습니다.")
        return redirect(url_for('index'))

    # DB에서 저장해둔 문제 데이터들을 불러오기
    questions = SolvedQuestion.query.filter(SolvedQuestion.id.in_(quiz_ids)).all()
    
    # 쿼리 결과를 ID 순서대로 재정렬 (IN 절은 순서를 보장하지 않음)
    questions_map = {q.id: q for q in questions}
    quiz_data = [questions_map[qid] for qid in quiz_ids]

    score = 0
    detail_results = []

    for i, q in enumerate(quiz_data):
        user_ans = request.form.get(f'q_{i}')
        # DB 객체이므로 q['answer'] 대신 q.correct_answer 사용
        is_correct = (str(user_ans).strip() == str(q.correct_answer).strip())
        
        if is_correct:
            score += 1
        
        detail_results.append({
            'question': q.question_text,
            'user_answer': user_ans or "미선택",
            'correct_answer': q.correct_answer,
            'explanation': q.explanation,
            'is_correct': is_correct
        })
    
    # 유저 점수 결과 저장
    db.session.add(UserResult(user_name=user_name, score=score))
    db.session.commit()

    return render_template('result.html', name=user_name, score=score, detail_results=detail_results)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)