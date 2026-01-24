# MediTemplate AI - Technical Specification

## 1. 기술 스택

| 구분 | 기술 |
|------|------|
| **언어** | Python 3.9+ |
| **프레임워크** | Streamlit |
| **AI 연동** | Google Generative AI SDK |
| **데이터 검증** | Pydantic |

---

## 2. JSON 스키마 정의

AI 모델의 System Prompt에 제공되는 스키마 구조:

```json
{
  "title": "리포트 템플릿 이름",
  "structure": [
    {
      "id": "고유 UUID",
      "type": "section | row | label | text_input | text_area | radio_group | checkbox_group | image_annotation",
      "label": "표시 이름",
      "layout": {
        "col_span": 24,
        "offset": 0
      },
      "style": {
        "font_size": "header | body | caption",
        "font_weight": "bold | regular",
        "text_align": "left | center | right",
        "border_style": "box | underline"
      },
      "options": ["옵션1", "옵션2"],
      "placeholder": "플레이스홀더 (선택)",
      "image_source": "이미지 경로 (image_annotation용)",
      "children": [
        { "재귀적 Component 구조" }
      ]
    }
  ]
}
```

### 컴포넌트 타입 정의

| Type | 용도 | options 필수 | children 허용 | layout/style |
|------|------|:------------:|:-------------:|:------------:|
| `section` | 그룹핑 컨테이너 | ❌ | ✅ | ❌ |
| `row` | 가로 배치 컨테이너 | ❌ | ✅ | ✅ |
| `label` | 텍스트 표시 | ❌ | ❌ | ✅ |
| `text_input` | 한 줄 입력 | ❌ | ❌ | ✅ |
| `text_area` | 여러 줄 입력 | ❌ | ❌ | ✅ |
| `radio_group` | 단일 선택 | ✅ | ❌ | ✅ |
| `checkbox_group` | 다중 선택 | ✅ | ❌ | ✅ |
| `image_annotation` | 이미지 위 마킹 | ❌ | ❌ | ✅ |

> **Note**: `row`는 24-Column Grid 시스템을 기반으로 `col_span`을 사용하여 너비를 지정합니다.

---

## 3. System Prompt 전략

```
Role: Expert Medical UI/UX Designer & Data Structurer

Instructions:
1. 제공된 의료 리포트 폼 이미지를 분석하라.
2. 논리적 구조와 컴포넌트를 추출하라.
3. 제공된 JSON Schema에 엄격히 맞춰 매핑하라.
4. 순수 장식 요소는 무시하고 데이터 입력 필드와 섹션에 집중하라.
5. 불명확한 손글씨는 "[Unclear Text]" 플레이스홀더 사용.
6. 폰트 크기, 굵기, 정렬 상태를 분석하여 `style` 속성에 매핑하라.
7. 입력 필드의 형태(박스형 vs 밑줄형)를 `border_style`로 구분하라.
8. 신체 모형이나 이미지가 포함된 경우 `image_annotation` 컴포넌트를 사용하라.
9. JSON만 출력. 마크다운 블록이나 설명 텍스트 없이.
```

---

## 4. UI 레이아웃 설계

```
┌─────────────────────────────────────────────────────────────┐
│  🏥 MediTemplate AI                              [Sidebar]  │
├─────────────────────────────────────────────────────────────┤
│                                                │ API Key    │
│  ┌─────────────────────┐  ┌─────────────────┐ │ Input      │
│  │                     │  │                 │ │            │
│  │   Image Uploader    │  │  Live Preview   │ └────────────┘
│  │                     │  │                 │               
│  ├─────────────────────┤  │  ┌───────────┐  │               
│  │                     │  │  │ Section 1 │  │               
│  │   JSON Editor       │  │  ├───────────┤  │               
│  │   (text_area)       │  │  │ Input...  │  │               
│  │                     │  │  │ Radio...  │  │               
│  │                     │  │  └───────────┘  │               
│  └─────────────────────┘  └─────────────────┘               
│         Column 1                Column 2                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 핵심 함수 설계

### 5.1 이미지 분석

```python
def analyze_image_with_gemini(image_data: bytes, api_key: str) -> str:
    """
    이미지를 Gemini Vision API로 전송하여 JSON 구조 생성.
    
    Args:
        image_data: 업로드된 이미지 바이트
        api_key: Google AI Studio API 키
    
    Returns:
        생성된 JSON 문자열
    """
```

### 5.2 재귀적 컴포넌트 렌더러

```python
def render_component(component: dict) -> None:
    """
    JSON 컴포넌트를 Streamlit 위젯으로 재귀적 렌더링.
    
    - section → st.expander + 자식 재귀 렌더링
    - label → st.markdown
    - text_input → st.text_input
    - text_area → st.text_area
    - radio_group → st.radio
    - checkbox_group → st.multiselect
    """
```

### 5.3 JSON 검증

```python
def validate_json(json_str: str) -> tuple[bool, dict | str]:
    """
    JSON 문자열 파싱 및 구조 검증.
    
    Returns:
        (성공 여부, 파싱된 dict 또는 에러 메시지)
    """
```

---

## 6. 에러 처리 전략

| 에러 유형 | 처리 방법 |
|----------|----------|
| API 키 미입력 | 사이드바에 경고 메시지 표시 |
| API 호출 실패 | 에러 상세 메시지와 함께 재시도 안내 |
| 잘못된 JSON 형식 | 미리보기 영역에 파싱 에러 표시 |
| 지원하지 않는 컴포넌트 | 경고와 함께 스킵 처리 |
