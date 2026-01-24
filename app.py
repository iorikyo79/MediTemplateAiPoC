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
import requests

# ============================================================================
# Page Configuration
# ============================================================================
"""
MediTemplate AI - PoC Application
손그림 의료 폼 이미지를 구조화된 JSON으로 변환하고 실시간 미리보기 제공
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
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
6. **LAYOUT ANALYSIS**: Use a **24-Column Grid System**. Analyze the relative width and position of each field.
   - Use `layout.col_span` (1 to 24) to specify width. (e.g., 12=50%, 24=100%).
   - Use `row` type to group horizontally adjacent fields.
7. **STYLE ANALYSIS**: Analyze font size, weight, and border styles.
   - Headers usually have larger/bolder fonts.
   - Input fields may be Box style or Underline style.
   - Map these to the `style` object.
8. **MEDICAL COMPONENTS**: Identify any body diagrams or symbols used for marking.
   - Use `image_annotation` type for these.
9. Output JSON ONLY. No markdown block formatting, no explanatory text.

JSON SCHEMA:
{
  "title": "Report Template Name (string)",
  "structure": [
    {
      "id": "unique-uuid-string",
      "type": "section | row | label | text_input | text_area | radio_group | checkbox_group | image_annotation",
      "label": "Display name (string)",
      "layout": {
        "col_span": 24 (number, 1-24, default 24),
        "offset": 0 (number, 0-23, optional)
      },
      "style": {
        "font_size": "header | body | caption" (default body),
        "font_weight": "bold | regular" (default regular),
        "text_align": "left | center | right" (default left),
        "border_style": "box | underline" (default box)
      },
      "options": ["option1", "option2"] (required for radio_group/checkbox_group, null otherwise),
      "placeholder": "Optional placeholder text",
      "image_source": "Optional image path for annotation",
      "children": [recursive Component list]
    }
  ]
}

COMPONENT TYPES:
- section: Container for grouping related fields
- row: Horizontal layout container (children arranged in columns)
- label: Read-only text display
- text_input: Single line text input
- text_area: Multi-line text input  
- radio_group: Single selection from options
- checkbox_group: Multiple selection from options
- image_annotation: Image for marking (e.g., pain location)

OUTPUT ONLY THE JSON. No markdown, no explanation."""

# ============================================================================
# Sample JSON Template
# ============================================================================
SAMPLE_JSON = """{
  "title": "Advanced Medical Report Template",
  "structure": [
    {
      "id": "sec-1",
      "type": "section",
      "label": "Patient Demographics",
      "children": [
        {
          "id": "row-1",
          "type": "row",
          "children": [
            {
              "type": "text_input",
              "label": "Patient Name",
              "layout": { "col_span": 8 },
              "style": { "font_weight": "bold", "border_style": "underline" }
            },
            {
              "type": "text_input",
              "label": "Patient ID",
              "layout": { "col_span": 8 },
              "style": { "border_style": "underline" }
            },
            {
              "type": "text_input",
              "label": "Date of Birth",
              "layout": { "col_span": 8 },
              "style": { "border_style": "underline" }
            }
          ]
        }
      ]
    },
    {
      "id": "sec-2",
      "type": "section",
      "label": "Physical Examination",
      "children": [
        {
          "type": "label",
          "label": "Mark Pain Location",
          "style": { "font_weight": "bold", "font_size": "header" }
        },
        {
          "id": "anno-1",
          "type": "image_annotation",
          "label": "Body Map",
          "layout": { "col_span": 24 },
          "image_source": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Human_body_front_and_side_diagrams.svg/358px-Human_body_front_and_side_diagrams.svg.png"
        },
        {
          "id": "row-2",
          "type": "row",
          "children": [
            {
              "type": "text_area",
              "label": "Observations",
              "layout": { "col_span": 12 }
            },
            {
              "type": "checkbox_group",
              "label": "Symptoms",
              "layout": { "col_span": 12 },
              "options": ["Swelling", "Redness", "Tenderness"]
            }
          ]
        }
      ]
    }
  ]
}"""

# ============================================================================
# Core Functions
# ============================================================================

def analyze_image_with_gemini(image_data: bytes, api_key: str) -> tuple[bool, str]:
    """이미지를 Gemini Vision API로 전송하여 JSON 구조 생성."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        image = Image.open(io.BytesIO(image_data))
        response = model.generate_content([SYSTEM_PROMPT, image])
        
        result = response.text.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])
        
        return True, result
    except Exception as e:
        return False, f"API 오류: {str(e)}"

def validate_json(json_str: str) -> tuple[bool, dict | str]:
    """JSON 문자열 파싱 및 구조 검증."""
    try:
        data = json.loads(json_str)
        if "title" not in data or "structure" not in data:
            return False, "JSON에 'title' 및 'structure' 필드가 필요합니다."
        return True, data
    except json.JSONDecodeError as e:
        return False, f"JSON 파싱 오류: {str(e)}"

def render_styled_label(label: str, style: dict):
    """스타일 메타데이터를 적용하여 라벨 렌더링"""
    font_size = style.get("font_size", "body")
    font_weight = style.get("font_weight", "regular")
    
    css_style = ""
    if font_size == "header": css_style += "font-size: 1.2rem;"
    elif font_size == "caption": css_style += "font-size: 0.8rem; color: #666;"
    
    if font_weight == "bold": css_style += "font_weight: bold;"
    
    st.markdown(f"<p style='{css_style} margin-bottom: 0.2rem;'>{label}</p>", unsafe_allow_html=True)

def render_component(component: dict, depth: int = 0) -> None:
    """JSON 컴포넌트를 Streamlit 위젯으로 재귀적 렌더링 (24-Grid 지원)"""
    comp_type = component.get("type", "")
    label = component.get("label", "Unnamed")
    comp_id = component.get("id", str(uuid.uuid4()))
    options = component.get("options", [])
    placeholder = component.get("placeholder", "")
    children = component.get("children", [])
    
    # Grid Layout & Style Extraction
    layout = component.get("layout", {})
    style = component.get("style", {})
    
    if comp_type == "section":
        with st.expander(f"📁 {label}", expanded=True):
            for child in children:
                render_component(child, depth + 1)

    elif comp_type == "row":
        # 24-Column Grid System Implementation
        # 자식들의 col_span 합이 24가 되도록 비율 계산
        cols_config = []
        valid_children = []
        
        for child in children:
            child_layout = child.get("layout", {})
            span = child_layout.get("col_span", 24)
            cols_config.append(span)
            valid_children.append(child)
            
        if cols_config:
            cols = st.columns(cols_config)
            for idx, child in enumerate(valid_children):
                with cols[idx]:
                    render_component(child, depth + 1)
        
    elif comp_type == "label":
        render_styled_label(label, style)
        
    elif comp_type == "text_input":
        render_styled_label(label, style)
        st.text_input(
            label, 
            placeholder=placeholder,
            key=f"input_{comp_id}",
            label_visibility="collapsed"
        )
        
    elif comp_type == "text_area":
        render_styled_label(label, style)
        st.text_area(
            label, 
            placeholder=placeholder,
            key=f"textarea_{comp_id}",
            label_visibility="collapsed"
        )
        
    elif comp_type == "image_annotation":
        render_styled_label(label, style)
        img_source = component.get("image_source")
        
        bg_image = None
        if img_source and img_source.startswith("http"):
            try:
                response = requests.get(img_source, timeout=5)
                if response.status_code == 200:
                    bg_image = Image.open(io.BytesIO(response.content))
            except Exception:
                pass
        
        if bg_image:
            # Canvas Component
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",  # 마킹 색상
                stroke_width=3,
                stroke_color="#FF0000",
                background_image=bg_image,
                background_color="#eee",
                height=400,
                drawing_mode="freedraw",
                key=f"canvas_{comp_id}",
            )
        else:
            st.warning(f"⚠️ 이미지를 로드할 수 없습니다: {img_source}")

    elif comp_type in ["radio_group", "checkbox_group"]:
        render_styled_label(label, style)
        if options:
            if comp_type == "radio_group":
                st.radio(label, options, key=f"radio_{comp_id}", label_visibility="collapsed")
            else:
                st.multiselect(label, options, key=f"check_{comp_id}", label_visibility="collapsed")
    
    else:
        st.info(f"ℹ️ Unknown type: {comp_type}")


def render_preview(data: dict) -> None:
    st.markdown(f"### 📋 {data.get('title', 'Untitled Template')}")
    st.divider()
    for component in data.get("structure", []):
        render_component(component)

# ============================================================================
# Sidebar & Main UI (Same as before, simplified for brevity)
# ============================================================================
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    api_key = st.text_input("Google AI API Key", type="password")
    st.markdown("---")
    st.markdown("### 📦 고급 컴포넌트\n- `Row (Grid)`\n- `Style Options`\n- `Image Annotation`")

st.markdown('<p class="main-header">🏥 MediTemplate AI (Advanced)</p>', unsafe_allow_html=True)

if "json_content" not in st.session_state:
    st.session_state.json_content = SAMPLE_JSON

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📤 이미지 업로드")
    uploaded_file = st.file_uploader("Upload Medical Form", type=["jpg", "png"])
    
    if uploaded_file and st.button("🚀 JSON 생성", type="primary"):
        if api_key:
            with st.spinner("Analyzing..."):
                success, result = analyze_image_with_gemini(uploaded_file.getvalue(), api_key)
                if success:
                    st.session_state.json_content = result
                    st.rerun()
        else:
            st.error("API Key Required")
            
    st.markdown("### ✏️ JSON 에디터")
    json_input = st.text_area("JSON", value=st.session_state.json_content, height=600, key="json_editor")
    if json_input != st.session_state.json_content:
        st.session_state.json_content = json_input

with col2:
    st.markdown("### 👁️ 실시간 미리보기")
    is_valid, result = validate_json(st.session_state.json_content)
    if is_valid:
        render_preview(result)
    else:
        st.error(f"JSON Error: {result}")

