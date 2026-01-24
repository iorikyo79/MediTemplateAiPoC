# 🏥 MediTemplate AI

손그림 의료 폼 이미지를 구조화된 JSON으로 변환하고 실시간 미리보기를 제공하는 AI 기반 템플릿 생성 도구

## ✨ 주요 기능

- **이미지 → JSON 변환**: Gemini Vision API를 활용하여 손그림/스캔 폼을 구조화된 JSON으로 자동 변환
- **실시간 미리보기**: JSON 편집 시 즉시 Form UI로 렌더링
- **재귀적 섹션 지원**: 중첩된 Section 구조 표현 가능
- **직관적 UI**: 2-column 레이아웃으로 편집과 미리보기 동시 확인

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.9+ |
| 프레임워크 | Streamlit |
| AI 모델 | Gemini 3 Flash Preview |
| 데이터 검증 | Pydantic |

## 📦 지원 컴포넌트

| 타입 | 용도 |
|------|------|
| `section` | 그룹핑 컨테이너 (중첩 가능) |
| `row` | 가로 배치 컨테이너 (24-Column Grid) |
| `label` | 텍스트 라벨 (스타일링 지원) |
| `text_input` | 한 줄 입력 |
| `text_area` | 여러 줄 입력 |
| `radio_group` | 단일 선택 |
| `checkbox_group` | 다중 선택 |
| `image_annotation` | 이미지 기반 마킹 |

## 🚀 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/iorikyo79/MediTemplateAiPoC.git
cd MediTemplateAiPoC

# 의존성 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

브라우저에서 http://localhost:8501 접속

## 📖 사용 방법

1. **API 키 입력**: 사이드바에서 [Google AI Studio](https://aistudio.google.com/) API 키 입력
2. **이미지 업로드**: 손그림 또는 스캔된 폼 이미지(JPG/PNG) 업로드
3. **JSON 생성**: "🚀 JSON 생성" 버튼 클릭
4. **편집 및 확인**: 생성된 JSON을 편집하고 우측 미리보기에서 결과 확인

## 📐 JSON 스키마

```json
{
  "title": "템플릿 이름",
  "structure": [
    {
      "id": "고유 ID",
      "type": "section | row | label | text_input | text_area | radio_group | checkbox_group | image_annotation",
      "label": "표시 이름",
      "options": ["옵션1", "옵션2"],
      "placeholder": "플레이스홀더 (선택)",
      "layout": { "col_span": 24 },
      "style": { "font_weight": "bold", "border_style": "underline" },
      "image_source": "이미지 경로",
      "children": []
    }
  ]
}
```

> **Note**: `row` 타입은 **24-Column Grid System**을 기반으로 `layout.col_span`을 사용하여 너비를 정밀하게 제어합니다.

## 📁 프로젝트 구조

```
MediTemplateAiPoC/
├── app.py              # 메인 Streamlit 앱
├── requirements.txt    # Python 의존성
└── docs/
    ├── PRD.md          # 제품 요구사항 정의서
    └── SPEC.md         # 기술 스펙 문서
```

## 📄 문서

- [PRD (제품 요구사항 정의서)](docs/PRD.md)
- [Technical Specification (기술 스펙)](docs/SPEC.md)

## 📝 License

MIT License
