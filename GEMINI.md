# MediTemplate AI - Gemini 프로젝트 컨텍스트

## 프로젝트 개요

**MediTemplate AI**는 병원 의료진의 비정형 요구사항(손그림, 스캔 문서)을 AI로 정형화된 JSON으로 변환하고, 웹에서 즉시 렌더링하여 검증하는 PoC 도구입니다.

### 핵심 가치
- 템플릿 기획-구현 간 간극 축소
- UI 구조화 시간 단축
- 실시간 미리보기로 즉각적인 피드백

---

## 기술 스택

- **Python 3.9+** / **Streamlit**
- **Gemini 3 Flash Preview** (Vision API)
- **Pydantic** (데이터 검증)

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│  🏥 MediTemplate AI                              [Sidebar]  │
├─────────────────────────────────────────────────────────────┤
│                                                │ API Key    │
│  ┌─────────────────────┐  ┌─────────────────┐ │ Input      │
│  │   Image Uploader    │  │  Live Preview   │ └────────────┘
│  ├─────────────────────┤  │  (Rendered UI)  │               
│  │   JSON Editor       │  │                 │               
│  └─────────────────────┘  └─────────────────┘               
│         Column 1                Column 2                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 사용자 플로우

1. **Upload** → 손그림 이미지(JPG/PNG) 업로드
2. **AI Analysis** → Gemini Vision이 이미지 분석하여 JSON 생성
3. **JSON Editor** → 생성된 JSON 직접 수정 가능
4. **Live Preview** → JSON이 실시간으로 Form UI로 렌더링

---

## JSON 스키마

```json
{
  "title": "템플릿 이름",
  "structure": [
    {
      "id": "고유 UUID",
      "type": "section | row | label | text_input | text_area | radio | checkbox | image_annotation",
      "label": "표시 이름",
      "layout": { "col_start": 3, "col_width": 10 },
      "style": { "font_weight": "bold", "border_style": "underline" },
      "options": ["예"], // radio/checkbox의 경우 선택값
      "group_id": "smoking", // radio/checkbox 그룹핑용 ID
      "placeholder": "플레이스홀더",
      "children": [{ "재귀적 Component" }]
    }
  ]
}
```

### 컴포넌트 타입

| Type | 용도 | options 필수 | children 허용 |
|------|------|:------------:|:-------------:|
| `section` | 그룹핑 컨테이너 | ❌ | ✅ |
| `row` | 가로 배치 컨테이너 | ❌ | ✅ |
| `label` | 텍스트 표시 | ❌ | ❌ |
| `text_input` | 한 줄 입력 | ❌ | ❌ |
| `text_area` | 여러 줄 입력 | ❌ | ❌ |
| `radio`, `checkbox` | 개별 선택 옵션 | ✅ | ❌ |
| `image_annotation` | 이미지 마킹 | ❌ | ❌ |

> **Note**: `layout`의 `col_start`와 `col_width`로 절대 위치 지정 (1-24 grid)

---

## 핵심 함수

### `analyze_image_with_gemini(image_data, api_key)`
이미지를 Gemini Vision API로 전송하여 JSON 구조 생성

### `render_component(component, depth)`
JSON 컴포넌트를 Streamlit 위젯으로 재귀적 렌더링

### `validate_json(json_str)`
JSON 문자열 파싱 및 구조 검증

---

## 파일 구조

```
MediTemplateAiPoC/
├── app.py              # 메인 Streamlit 앱
├── requirements.txt    # Python 의존성
├── README.md           # 프로젝트 소개
├── GEMINI.md           # Gemini 컨텍스트 (이 파일)
└── docs/
    ├── PRD.md          # 제품 요구사항 정의서
    └── SPEC.md         # 기술 스펙 문서
```

---

## 개발 가이드라인

### 코드 스타일
- Python 타입 힌트 사용
- Docstring으로 함수 문서화
- Streamlit 컴포넌트는 `st.` 프리픽스 사용

### 에러 처리
- API 키 미입력 → 사이드바 경고
- API 호출 실패 → 에러 메시지 표시
- JSON 파싱 오류 → 미리보기 영역에 표시
- 미지원 컴포넌트 → 경고 후 스킵

### 확장 포인트
- 새 컴포넌트 타입: `render_component()` 함수에 elif 추가
- 입력 형식 확장: 텍스트/마크다운 지원 모듈 추가 가능
