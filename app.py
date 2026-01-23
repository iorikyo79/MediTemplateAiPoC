"""
MediTemplate AI - PoC Application
손그림 의료 폼 이미지를 구조화된 JSON으로 변환하고 실시간 미리보기 제공
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import io
import uuid

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="MediTemplate AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom Styles
# ============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .section-box {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #3B82F6;
    }
    .error-box {
        background: #FEF2F2;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #EF4444;
        color: #991B1B;
    }
    .success-box {
        background: #F0FDF4;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #22C55E;
        color: #166534;
    }
    .stExpander {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# System Prompt for Gemini
# ============================================================================
SYSTEM_PROMPT = """You are an Expert Medical UI/UX Designer & Data Structurer.

Your task is to analyze the provided image of a medical report form and extract its structure.

INSTRUCTIONS:
1. Analyze the provided image of a medical report form carefully.
2. Extract the logical structure and components.
3. Map them strictly to the provided JSON Schema.
4. Ignore strictly decorative elements, focus on data entry fields and sections.
5. For handwritten text that is unclear, use a placeholder like "[Unclear Text]".
6. **LAYOUT ANALYSIS**: Analyze the layout carefully. If multiple fields are placed horizontally on the same line, wrap them in a 'row' type object. Estimate their relative width ratio (e.g., 1:1, 1:2, 2:1:1).
7. Output JSON ONLY. No markdown block formatting, no explanatory text.

JSON SCHEMA:
{
  "title": "Report Template Name (string)",
  "structure": [
    {
      "id": "unique-uuid-string",
      "type": "section | row | label | text_input | text_area | radio_group | checkbox_group",
      "label": "Display name (string)",
      "options": ["option1", "option2"] (required for radio_group/checkbox_group, null otherwise),
      "placeholder": "Optional placeholder text",
      "width_ratio": 1 (number, optional, used inside 'row' to specify relative width, default is 1),
      "children": [recursive Component list, for 'section' and 'row' types]
    }
  ]
}

COMPONENT TYPES:
- section: Container for grouping related fields (can have children)
- row: Horizontal layout container for placing multiple fields side-by-side (children are arranged in columns)
- label: Read-only text display
- text_input: Single line text input
- text_area: Multi-line text input  
- radio_group: Single selection from options
- checkbox_group: Multiple selection from options

ROW LAYOUT EXAMPLE:
If "Patient ID" and "Patient Name" are on the same line with equal width:
{
  "type": "row",
  "children": [
    {"type": "text_input", "label": "Patient ID", "width_ratio": 1},
    {"type": "text_input", "label": "Patient Name", "width_ratio": 1}
  ]
}

OUTPUT ONLY THE JSON. No markdown, no explanation."""

# ============================================================================
# Sample JSON Template
# ============================================================================
SAMPLE_JSON = """{
  "title": "Sample Medical Report Template",
  "structure": [
    {
      "id": "section-1",
      "type": "section",
      "label": "Patient Information",
      "children": [
        {
          "id": "row-1",
          "type": "row",
          "children": [
            {
              "id": "field-1",
              "type": "text_input",
              "label": "Patient ID",
              "placeholder": "Enter patient ID",
              "width_ratio": 1
            },
            {
              "id": "field-2",
              "type": "text_input",
              "label": "Patient Name",
              "placeholder": "Enter patient name",
              "width_ratio": 2
            }
          ]
        },
        {
          "id": "row-2",
          "type": "row",
          "children": [
            {
              "id": "field-3",
              "type": "radio_group",
              "label": "Gender",
              "options": ["Male", "Female", "Other"],
              "width_ratio": 1
            },
            {
              "id": "field-4",
              "type": "text_input",
              "label": "Age",
              "placeholder": "Enter age",
              "width_ratio": 1
            }
          ]
        }
      ]
    },
    {
      "id": "section-2",
      "type": "section",
      "label": "Clinical Findings",
      "children": [
        {
          "id": "field-5",
          "type": "text_area",
          "label": "Findings",
          "placeholder": "Enter clinical findings..."
        },
        {
          "id": "field-6",
          "type": "checkbox_group",
          "label": "Symptoms",
          "options": ["Fever", "Cough", "Fatigue", "Headache"]
        }
      ]
    }
  ]
}"""

# ============================================================================
# Core Functions
# ============================================================================

def analyze_image_with_gemini(image_data: bytes, api_key: str) -> tuple[bool, str]:
    """
    이미지를 Gemini Vision API로 전송하여 JSON 구조 생성.
    
    Returns:
        (성공 여부, JSON 문자열 또는 에러 메시지)
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        # PIL Image로 변환
        image = Image.open(io.BytesIO(image_data))
        
        # Gemini API 호출
        response = model.generate_content([SYSTEM_PROMPT, image])
        
        # 응답에서 JSON 추출 (마크다운 블록 제거)
        result = response.text.strip()
        if result.startswith("```"):
            # ```json 또는 ``` 제거
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])
        
        return True, result
        
    except Exception as e:
        return False, f"API 오류: {str(e)}"


def validate_json(json_str: str) -> tuple[bool, dict | str]:
    """
    JSON 문자열 파싱 및 구조 검증.
    
    Returns:
        (성공 여부, 파싱된 dict 또는 에러 메시지)
    """
    try:
        data = json.loads(json_str)
        
        # 기본 구조 검증
        if "title" not in data:
            return False, "JSON에 'title' 필드가 필요합니다."
        if "structure" not in data:
            return False, "JSON에 'structure' 필드가 필요합니다."
        if not isinstance(data["structure"], list):
            return False, "'structure'는 배열이어야 합니다."
            
        return True, data
        
    except json.JSONDecodeError as e:
        return False, f"JSON 파싱 오류: {str(e)}"


def render_component(component: dict, depth: int = 0) -> None:
    """
    JSON 컴포넌트를 Streamlit 위젯으로 재귀적 렌더링.
    """
    comp_type = component.get("type", "")
    label = component.get("label", "Unnamed")
    comp_id = component.get("id", str(uuid.uuid4()))
    options = component.get("options", [])
    placeholder = component.get("placeholder", "")
    children = component.get("children", [])
    
    if comp_type == "section":
        with st.expander(f"📁 {label}", expanded=True):
            for child in children:
                render_component(child, depth + 1)
                
    elif comp_type == "row":
        # Row 컨테이너: 자식 요소들을 가로로 배치
        if children:
            # width_ratio 추출 (없으면 1로 기본값)
            ratios = [child.get("width_ratio", 1) for child in children]
            cols = st.columns(ratios)
            for idx, child in enumerate(children):
                with cols[idx]:
                    render_component(child, depth + 1)
                
    elif comp_type == "label":
        st.markdown(f"**{label}**")
        
    elif comp_type == "text_input":
        st.text_input(
            label, 
            placeholder=placeholder or f"Enter {label}...",
            key=f"input_{comp_id}"
        )
        
    elif comp_type == "text_area":
        st.text_area(
            label, 
            placeholder=placeholder or f"Enter {label}...",
            key=f"textarea_{comp_id}",
            height=100
        )
        
    elif comp_type == "radio_group":
        if options:
            st.radio(label, options=options, key=f"radio_{comp_id}")
        else:
            st.warning(f"⚠️ '{label}': options가 필요합니다.")
            
    elif comp_type == "checkbox_group":
        if options:
            st.multiselect(label, options=options, key=f"checkbox_{comp_id}")
        else:
            st.warning(f"⚠️ '{label}': options가 필요합니다.")
            
    else:
        st.info(f"ℹ️ 지원하지 않는 타입: {comp_type}")


def render_preview(data: dict) -> None:
    """
    전체 JSON 구조를 미리보기로 렌더링.
    """
    st.markdown(f"### 📋 {data.get('title', 'Untitled Template')}")
    st.divider()
    
    structure = data.get("structure", [])
    for component in structure:
        render_component(component)


# ============================================================================
# Sidebar - API Configuration
# ============================================================================
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    st.divider()
    
    api_key = st.text_input(
        "Google AI API Key",
        type="password",
        placeholder="AIza...",
        help="Google AI Studio에서 API 키를 발급받으세요."
    )
    
    if api_key:
        st.success("✅ API 키 입력됨")
    else:
        st.warning("⚠️ API 키를 입력해주세요")
    
    st.divider()
    st.markdown("""
    ### 📖 사용 방법
    1. API 키 입력
    2. 이미지 업로드
    3. JSON 생성 클릭
    4. 결과 편집 및 확인
    """)
    
    st.divider()
    st.markdown("""
    ### 📦 지원 컴포넌트
    - `section` - 그룹 컨테이너
    - `row` - 가로 배치 컨테이너
    - `label` - 텍스트 라벨
    - `text_input` - 한 줄 입력
    - `text_area` - 여러 줄 입력
    - `radio_group` - 단일 선택
    - `checkbox_group` - 다중 선택
    """)

# ============================================================================
# Main Content
# ============================================================================
st.markdown('<p class="main-header">🏥 MediTemplate AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">손그림 의료 폼을 구조화된 JSON으로 변환합니다</p>', unsafe_allow_html=True)

# 세션 상태 초기화
if "json_content" not in st.session_state:
    st.session_state.json_content = SAMPLE_JSON

if "generation_triggered" not in st.session_state:
    st.session_state.generation_triggered = False

# 2-Column Layout
col1, col2 = st.columns([1, 1], gap="large")

# ============================================================================
# Left Column - Image Upload & JSON Editor
# ============================================================================
with col1:
    st.markdown("### 📤 이미지 업로드")
    
    uploaded_file = st.file_uploader(
        "손그림 또는 스캔된 폼 이미지를 업로드하세요",
        type=["jpg", "jpeg", "png"],
        help="JPG 또는 PNG 형식의 이미지를 지원합니다."
    )
    
    if uploaded_file:
        st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
        
        # JSON 생성 버튼
        if st.button("🚀 JSON 생성", type="primary", use_container_width=True):
            if not api_key:
                st.error("❌ 사이드바에서 API 키를 먼저 입력해주세요.")
            else:
                with st.spinner("🔄 AI가 이미지를 분석하고 있습니다..."):
                    image_bytes = uploaded_file.getvalue()
                    success, result = analyze_image_with_gemini(image_bytes, api_key)
                    
                    if success:
                        st.session_state.json_content = result
                        st.session_state.generation_triggered = True
                        st.success("✅ JSON 생성 완료!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
    
    st.divider()
    st.markdown("### ✏️ JSON 에디터")
    
    # JSON 에디터
    json_input = st.text_area(
        "JSON 구조 (직접 수정 가능)",
        value=st.session_state.json_content,
        height=400,
        key="json_editor",
        label_visibility="collapsed"
    )
    
    # 에디터 변경 시 세션 상태 업데이트
    if json_input != st.session_state.json_content:
        st.session_state.json_content = json_input

# ============================================================================
# Right Column - Live Preview
# ============================================================================
with col2:
    st.markdown("### 👁️ 실시간 미리보기")
    
    # JSON 검증 및 렌더링
    is_valid, result = validate_json(st.session_state.json_content)
    
    if is_valid:
        render_preview(result)
    else:
        st.markdown(f"""
        <div class="error-box">
            <strong>❌ JSON 오류</strong><br>
            {result}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**💡 Tip:** JSON 형식을 확인하고 수정해주세요.")

# ============================================================================
# Footer
# ============================================================================
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #9CA3AF; font-size: 0.875rem;">
        MediTemplate AI PoC | Built with Streamlit & Gemini Vision
    </div>
    """,
    unsafe_allow_html=True
)
