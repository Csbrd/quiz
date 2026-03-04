## AI를 이용한 네트워크 인프라 Quiz Service
Gemini API를 활용하여 CS 기초 및 네트워크 인프라 지식을 학습할 수 있는 웹 애플리케이션
## 구현 계기
자신이 알고 있는 지식이어도 정확히 아는 것과 애매하게 아는 것의 차이가 분명히 존재하는데, 단순 문제 풀이가 아닌 문제 풀이가 끝난 후 상세한 해설을 제공함으로써 CS 기술면접 대비 실력을 기를 수 있다.
## 주요 기능 및 특징
1. **문제 생성**: 사용자가 접속할 때마다 Gemini가 실시간으로 CS 문제 생성
2. **중복 방지 시스템**: DB를 조회하여 이전에 풀었던 문제와 겹치지 않는 새로운 문제 출제
3. **해설 제공**: 정답 확인 뿐만 아니라, 왜 정답인지에 대한 AI 해설 제공
4. **오답 노트**: 내가 선택한 답과 실제 정답을 비교하여 시각적 표현
5. **보안 및 설정 관리**:
- `Secret`을 통한 DB 비밀번호 및 Gemini API Key 암호화 관리.
- `ConfigMap`을 활용한 환경 변수 분리
6. **고가용성(High Availability)**
- Flask 웹 서버의 Replicas를 통한 부하 분산.

## 구성 환경
- **Backend**: Python 3.14+, Flask
- **DataBase**: MySQL(Docker 구동)
- **API**: Google Gemini
- **Orchestration**: Kubernetes (AKS)
- **Ingress/Gateway**: Traefik Gateway API
- **Storage**: Azure Disk(PVC)

## 시작하기
### API 키 발급
[Google AI Studio](https://aistudio.google.com/api-keys)에서 Gemini API 키 발급
### 저장소 복제
`git clone https://github.com/Csbrd/quiz.git`
### 환경변수 설정
`.envexample` 파일을 `.env`로 변경 후 안에 있는 설정값 수정
### 라이브러리 설치
`pip install -r requirements.txt`
### 실행하기
`python3 app.py`
## k8s 배포
Azure 클라우드에서 클러스터 구
## 시스템 아키텍
<img width="1314" height="736" alt="image" src="https://github.com/user-attachments/assets/4f998a5e-18d3-46a6-b847-9d6200386123" />
## 폴더 구조 및 YAML 리소스

```
.
├── k8s/
│   ├── secret.yaml                  # DB 및 API 키 보안 설정
│   ├── configmap.yaml               # DB 연결 정보
│   ├── pvc.yaml                     # 영구 저장소(PVC) 정의
│   ├── backend-deployment.yaml      # MariaDB 배포 및 PVC 마운트
│   ├── frontend-deployment.yaml     # Flask 웹 서버 배포
│   ├── gateway.yaml                 # Traefik Gateway 설정
│   └── httproute.yaml               # 경로 기반 라우팅 규칙
└── app/                             # Flask 소스 코드
```
## 배포 방법
1. 네임스페이스 생성
```
kubectl create namespace cs-quiz-app
```

3. 설정 및 보안 적용
```
kubectl apply -f k8s/cs-db-secret.yaml
kubectl apply -f k8s/cs-db-configmap.yaml
```

4. 데이터베이스 및 스토리지 배포
```
kubectl apply -f k8s/db-pvc.yaml
kubectl apply -f k8s/db-deployment.yaml
kubectl apply -f k8s/db-service.yaml
```

6. 웹 서버 배포
```
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-service.yaml
```

8. Gateway API 적용
```
kubectl apply -f k8s/gateway.yaml
kubectl apply -f k8s/http-route.yaml
```
## 트러블슈팅
- DB 서버 파드 생성 시 메모리 부족(OOMKilled) 현상으로 인해 계속 재시작
  - Azure 클라우드에서 오토 스케일링을 통해 메모리 문제 해결
- ConfigMap, Secret 파일 설정 후 환경 변수 설정할 때 어떤 키-밸류 값을 어디에 사용해야 하는지
- Gateway API 설정 시 Traefik 사용 -> Gateway 상태 Unknown
  - 포트 번호 8000번, 이름 web 사용 해도 Unknown 상태로 지속되다가 갑자기 True
- DB 서버 테이블 생성 미생성으로 인해 ProgrammingError 발생
  - Deployment 재실행 후 해결(DB 서버보다 먼저 실행되서 발생한 오류)
