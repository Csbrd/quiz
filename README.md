## AI를 이용한 네트워크 인프라 Quiz Service
Gemini API를 활용하여 CS 기초 및 네트워크 인프라 지식을 학습할 수 있는 웹 애플리케이션
## 주요 기능
**문제 생성**: 사용자가 접속할 때마다 Gemini가 실시간으로 CS 문제 생성

**중복 방지 시스템**: DB를 조회하여 이전에 풀었던 문제와 겹치지 않는 새로운 문제 출제

**해설 제공**: 정답 확인 뿐만 아니라, 왜 정답인지에 대한 AI 해설 제공

**오답 노트**: 내가 선택한 답과 실제 정답을 비교하여 시각적 표현

## 구성 환경
**Backend**: Python 3.14+, Flask

**DataBase**: MySQL(Docker 구동)

**API**: Google Gemini

## 시작하기
### 저장소 복제
`git clone https://github.com/Csbrd/quiz.git`
### 라이브러리 설치
`pip install -r requirements.txt`
### 실행하기
`python3 app.py`
