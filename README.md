# 🔍 Vector Database Search Project

텍스트, 이미지, 영상을 업로드하고 Elasticsearch를 사용한 벡터 검색을 수행하는 예제 프로젝트입니다.

## ✨ 주요 기능

- **다양한 파일 타입 지원**: 텍스트, 이미지, 영상 파일 업로드
- **벡터 임베딩 생성**: BERT (텍스트), CLIP (이미지/영상) 모델 사용
- **NoSQL 데이터베이스**: MongoDB에 파일 메타데이터 저장
- **벡터 검색**: Elasticsearch를 사용한 고성능 유사도 검색
- **웹 인터페이스**: 직관적인 사용자 인터페이스 제공
- **RESTful API**: 완전한 API 문서 제공

## 🏗️ 프로젝트 구조

```
vectordb/
├── main.py              # FastAPI 메인 애플리케이션
├── config.py            # 설정 관리
├── models.py            # Pydantic 데이터 모델
├── database.py          # MongoDB/Elasticsearch 연결 관리
├── embedding.py         # 벡터 임베딩 생성
├── utils.py             # 유틸리티 함수
├── run.py               # 애플리케이션 실행 스크립트
├── requirements.txt     # Python 의존성
├── docker-compose.yml   # Docker 서비스 설정
├── static/
│   └── index.html       # 웹 인터페이스
├── sample_files/        # 테스트용 샘플 파일들
└── uploads/             # 업로드된 파일 저장소
```

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 실행 (Docker 사용)

```bash
# MongoDB와 Elasticsearch 실행
docker-compose up -d

# 또는 개별 실행
docker run -d -p 27017:27017 --name mongodb mongo:latest
docker run -d -p 9200:9200 -p 9300:9300 --name elasticsearch \
  -e "discovery.type=single-node" -e "xpack.security.enabled=false" \
  elasticsearch:8.11.0
```

### 3. 애플리케이션 실행

```bash
# 방법 1: run.py 스크립트 사용
python run.py

# 방법 2: uvicorn 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 웹 인터페이스 접속

브라우저에서 `http://localhost:8000/static/index.html` 접속

## 📚 API 엔드포인트

### 파일 업로드
```bash
POST /upload
Content-Type: multipart/form-data

# 텍스트 파일 업로드
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -F "file=@sample.txt"

# 이미지 파일 업로드
curl -X POST "http://localhost:8000/upload" \
  -F "file=@image.jpg"
```

### 벡터 검색
```bash
GET /search?query=검색어&file_type=text&limit=10

# 예시
curl "http://localhost:8000/search?query=인공지능&limit=5"
```

### 파일 목록 조회
```bash
GET /files?limit=100

curl "http://localhost:8000/files"
```

### 파일 삭제
```bash
DELETE /files/{file_id}

# 예시
curl -X DELETE "http://localhost:8000/files/your-file-id"
```

### 헬스 체크
```bash
GET /health

curl "http://localhost:8000/health"
```

## 🔧 설정

환경 변수를 통해 설정을 변경할 수 있습니다:

```bash
# .env 파일 생성 (선택사항)
MONGODB_URI=mongodb://localhost:27017
ELASTICSEARCH_URL=http://localhost:9200
UPLOAD_DIR=./uploads
DATABASE_NAME=vectordb
COLLECTION_NAME=files
ELASTICSEARCH_INDEX=files
```

## 📁 지원 파일 형식

### 텍스트 파일
- `.txt`, `.md`, `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`, `.csv`

### 이미지 파일
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`

### 영상 파일
- `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.mkv`

## 🧠 기술 스택

- **Backend**: FastAPI, Python 3.8+
- **Database**: MongoDB (메타데이터), Elasticsearch (벡터 검색)
- **ML Models**: 
  - BERT (sentence-transformers/all-MiniLM-L6-v2) - 텍스트 임베딩
  - CLIP (openai/clip-vit-base-patch32) - 이미지/영상 임베딩
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Container**: Docker, Docker Compose

## 🔍 사용 예제

### 1. 텍스트 파일 업로드 및 검색

```python
import requests

# 파일 업로드
with open('sample.txt', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/upload', files=files)
    print(response.json())

# 벡터 검색
response = requests.get('http://localhost:8000/search?query=머신러닝')
results = response.json()
for result in results['results']:
    print(f"파일: {result['filename']}, 점수: {result['score']}")
```

### 2. 이미지 검색

```python
# 이미지 업로드
with open('image.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/upload', files=files)

# 텍스트로 이미지 검색
response = requests.get('http://localhost:8000/search?query=고양이&file_type=image')
```

## 🛠️ 개발 및 테스트

### 로컬 개발 환경

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 실행
docker-compose up -d

# 애플리케이션 실행
python run.py
```

### 테스트

```bash
# 샘플 파일로 테스트
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample_files/sample.txt"

curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample_files/python_code.py"

# 검색 테스트
curl "http://localhost:8000/search?query=벡터&limit=5"
```

## 📊 모니터링

- **Kibana**: `http://localhost:5601` (Elasticsearch 관리)
- **API 문서**: `http://localhost:8000/docs` (Swagger UI)
- **헬스 체크**: `http://localhost:8000/health`

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

MIT License

## 🆘 문제 해결

### 일반적인 문제들

1. **MongoDB 연결 실패**
   ```bash
   # MongoDB 상태 확인
   docker ps | grep mongodb
   ```

2. **Elasticsearch 메모리 부족**
   ```bash
   # Docker Compose에서 메모리 제한 설정
   ES_JAVA_OPTS="-Xms512m -Xmx512m"
   ```

3. **모델 다운로드 실패**
   ```bash
   # 캐시 삭제 후 재시도
   rm -rf ~/.cache/huggingface/
   ```

### 로그 확인

```bash
# 애플리케이션 로그
tail -f logs/app.log

# Docker 로그
docker logs vectordb-mongodb
docker logs vectordb-elasticsearch
``` 