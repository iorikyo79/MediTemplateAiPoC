"""
MediTemplate AI - PoC Application
손그림 의료 폼 이미지를 구조화된 JSON으로 변환하고, 절대 좌표 기반 그리드로 정밀 렌더링하며,
AI 기반 레이아웃 검증 기능을 제공합니다.
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import json
import io
import uuid
import requests
import time

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
    .verify-box-good {
        background: #F0FDF4;
        border: 1px solid #22C55E;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }
    .verify-box-bad {
        background: #FEF2F2;
        border: 1px solid #EF4444;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }
    .stExpander {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
    }
    div[data-testid="column"] {
        border: 1px dashed rgba(0,0,0,0.05); /* 그리드 디버깅용 (선택사항) */
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# System Prompts (2-Stage Pipeline)
# ============================================================================

# Stage 1: Structure Extraction
PROMPT_STAGE_1 = """You are an Expert Medical Data Analyst.

Task: Extract the LOGICAL STRUCTURE and CONTENT from the medical form image.
IGNORE layout, positions, styles, and grid for now. Focus ONLY on content completeness.

INSTRUCTIONS:
1. Identify all Sections, Labels, Inputs, Options, and Annotations.
2. Group them strictly by logical hierarchy (Section > Label/Input).
3. Do NOT omit any text or field.
4. Extract Checkboxes and Radio buttons as individual items with `group_id`.
5. For `layout` and `style`, leave them empty or default.

JSON SCHEMA (Skeleton):
{
  "title": "Form Title",
  "structure": [
    {
      "type": "section | row | label | text_input | radio | checkbox | image_annotation",
      "label": "Text Content",
      "options": ["Val"],
      "group_id": "group",
      "children": []
    }
  ]
}
OUTPUT JSON ONLY."""

# Stage 2: Layout & Style Refinement
PROMPT_STAGE_2 = """You are an Expert UI/UX Designer specialized in Grid Layouts.

Task: Take the provided JSON SKELETON and the ORIGINAL IMAGE.
Map each component to its PRECISE LOCATION using a 24-Column Absolute Grid.

INSTRUCTIONS:
1. **ABSOLUTE GRID**: Fill in `layout: { "col_start": X, "col_width": Y }` for EVERY component.
   - `col_start`: 1-24. `col_width`: 1-24.
   - Ensure components on the same line have non-overlapping coordinates.
   - Insert `row` containers where horizontally adjacent items exist.

2. **STYLE**: Fill in `style: { "font_weight": "...", "border_style": "..." }`.
   - Headlines -> font_size: "header", font_weight: "bold".
   - Inputs -> border_style: "underline" or "box".

3. **VERIFY**: Ensure the JSON structure exactly matches the provided skeleton, only adding layout/style metadata.

OUTPUT FULL JSON ONLY."""

# Verification Prompt (Unchanged)
VERIFY_PROMPT = """You are an Expert UI/UX QA Engineer.

Task: Compare the ORIGINAL IMAGE of a medical form with the GENERATED JSON structure.

Evaluate:
1. **Layout Accuracy**: Do the `col_start` and `col_width` values in JSON accurately reflect the visual position in the image?
2. **Completeness**: Are any fields missing?
3. **Control Type**: Are checkboxes/radios correctly identified?

Output JSON:
{
  "similarity_score": 85 (0-100),
  "evaluation_summary": "One sentence summary.",
  "layout_issues": ["List of specific layout mismatches"],
  "missing_elements": ["List of missing fields"],
  "improvement_suggestions": ["Actionable JSON fix suggestions"]
}
OUTPUT JSON ONLY."""

# ============================================================================
# Sample JSON Template
# ============================================================================
SAMPLE_JSON = """{
  "title": "High Fidelity Medical Form",
  "structure": [
    {
      "type": "section",
      "label": "Patient Info",
      "layout": { "col_start": 1, "col_width": 24 },
      "children": [
        {
          "type": "row",
          "children": [
            {
              "type": "label",
              "label": "Patient Name :",
              "layout": { "col_start": 1, "col_width": 4 },
              "style": { "font_weight": "bold", "text_align": "right" }
            },
            {
              "type": "text_input",
              "layout": { "col_start": 5, "col_width": 8 },
              "style": { "border_style": "underline" }
            },
             {
              "type": "label",
              "label": "ID :",
              "layout": { "col_start": 14, "col_width": 2 },
              "style": { "text_align": "right" }
            },
            {
              "type": "text_input",
              "layout": { "col_start": 16, "col_width": 8 },
              "style": { "border_style": "underline" }
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

def call_gemini(system_prompt, image_bytes=None, text_content=None, api_key=None):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        content = [system_prompt]
        if image_bytes:
            content.append(Image.open(io.BytesIO(image_bytes)))
        if text_content:
            content.append(text_content)
            
        response = model.generate_content(content)
        result = response.text.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])
        return True, result
    except Exception as e:
        return False, str(e)

def analyze_image_pipeline(image_bytes, api_key, progress_bar=None):
    """2-Stage Generation Pipeline"""
    
    # Stage 1: Structure Extraction
    if progress_bar: progress_bar.progress(10, text="Stage 1: Extracting Structure & Content...")
    success, json_skeleton = call_gemini(PROMPT_STAGE_1, image_bytes=image_bytes, api_key=api_key)
    
    if not success: return False, json_skeleton
    
    # Stage 2: Layout Refinement
    if progress_bar: progress_bar.progress(50, text="Stage 2: Calculating Absolute Grid & Styles...")
    success, final_json = call_gemini(PROMPT_STAGE_2, image_bytes=image_bytes, text_content=f"SKELETON JSON:\n{json_skeleton}", api_key=api_key)
    
    if progress_bar: progress_bar.progress(100, text="Done!")
    return success, final_json

def verify_layout(image_bytes, json_str, api_key):
    return call_gemini(VERIFY_PROMPT, image_bytes=image_bytes, text_content=f"Generated JSON:\n{json_str}", api_key=api_key)

def validate_json(json_str):
    try:
        data = json.loads(json_str)
        return True, data
    except Exception as e:
        return False, str(e)

def render_styled_label(label: str, style: dict):
    font_size = style.get("font_size", "body")
    font_weight = style.get("font_weight", "regular")
    align = style.get("text_align", "left")
    
    css = f"text-align: {align}; margin-bottom: 0.2rem;"
    if font_size == "header": css += "font-size: 1.2rem;"
    elif font_size == "caption": css += "font-size: 0.8rem; color: #666;"
    if font_weight == "bold": css += "font_weight: bold;"
    
    st.markdown(f"<div style='{css}'>{label}</div>", unsafe_allow_html=True)

def render_component(component: dict, depth: int = 0):
    comp_type = component.get("type", "")
    comp_id = component.get("id", str(uuid.uuid4()))
    label = component.get("label", "")
    style = component.get("style", {})
    options = component.get("options", [])
    group_id = component.get("group_id", "")
    
    if comp_type == "section":
        with st.expander(f"📁 {label}", expanded=True):
            for child in component.get("children", []):
                render_component(child, depth + 1)
                
    elif comp_type == "row":
        children = sorted(component.get("children", []), key=lambda x: x.get("layout", {}).get("col_start", 1))
        current_cursor = 1
        layout_plan = []
        
        for child in children:
            layout = child.get("layout", {})
            start = layout.get("col_start", current_cursor)
            width = layout.get("col_width", 4)
            if start > current_cursor:
                layout_plan.append((start - current_cursor, None))
            layout_plan.append((width, child))
            current_cursor = start + width
            
        if layout_plan:
            widths = [item[0] for item in layout_plan]
            try:
                cols = st.columns(widths)
                for idx, (width, child_comp) in enumerate(layout_plan):
                    with cols[idx]:
                        if child_comp: render_component(child_comp, depth + 1)
            except Exception as e:
                st.error(f"Layout Error: {str(e)}")
                        
    elif comp_type == "label":
        render_styled_label(label, style)
    elif comp_type == "text_input":
        render_styled_label(label, style)
        st.text_input(" ", key=f"in_{comp_id}", label_visibility="collapsed")
    elif comp_type == "text_area":
        render_styled_label(label, style)
        st.text_area(" ", key=f"txt_{comp_id}", label_visibility="collapsed", height=80)
    elif comp_type == "radio":
        st.radio(label, options=options, key=f"rad_{comp_id}_{group_id}")
    elif comp_type == "checkbox":
        st.checkbox(label, key=f"chk_{comp_id}_{group_id}")
    elif comp_type == "image_annotation":
        render_styled_label(label, style)
        img_source = component.get("image_source")
        bg_image = None
        if img_source and img_source.startswith("http"):
            try:
                response = requests.get(img_source, timeout=3)
                if response.status_code == 200:
                    bg_image = Image.open(io.BytesIO(response.content))
            except: pass
        if bg_image:
             st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=3, stroke_color="red", background_image=bg_image, height=300, key=f"canvas_{comp_id}")
        else:
            st.warning(f"Image failed: {img_source}")

def render_preview(data):
    st.markdown(f"### 📋 {data.get('title', 'Template')}")
    st.divider()
    for comp in data.get("structure", []):
        render_component(comp)

# ============================================================================
# MAIN APP UI
# ============================================================================
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Google AI API Key", type="password")
    
st.title("🏥 MediTemplate AI (Ver.3)")
st.markdown("Precision Layout & AI Verification System")

if "json_content" not in st.session_state:
    st.session_state.json_content = SAMPLE_JSON
    
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Source & Editor")
    uploaded_file = st.file_uploader("Upload Form Image", type=["jpg", "png"])
    
    # 1. Generate (2-Stage Pipeline)
    if uploaded_file and st.button("🚀 Generate JSON (2-Stage Pipeline)", type="primary", use_container_width=True):
        if not api_key:
            st.error("API Key required")
        else:
            progress_bar = st.progress(0, text="Starting analysis...")
            success, res = analyze_image_pipeline(uploaded_file.getvalue(), api_key, progress_bar)
            if success:
                st.session_state.json_content = res
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(res)
                    
    # 2. Verify
    if uploaded_file and st.button("🔍 Verify Layout (AI Agent)", use_container_width=True):
        if not api_key:
            st.error("API Key required")
        else:
            with st.spinner("Compare Image vs JSON..."):
                success, res = verify_layout(uploaded_file.getvalue(), st.session_state.json_content, api_key)
                if success:
                    st.session_state.verify_result = res
                else:
                    st.error(res)

    if "verify_result" in st.session_state:
        try:
            v_res = json.loads(st.session_state.verify_result)
            score = v_res.get("similarity_score", 0)
            color_cls = "verify-box-good" if score >= 80 else "verify-box-bad"
            
            st.markdown(f"""
            <div class="{color_cls}">
                <h3>Score: {score}/100</h3>
                <p><strong>📝 Evaluation:</strong> {v_res.get('evaluation_summary')}</p>
                <p><strong>⚠️ Missing:</strong> {', '.join(v_res.get('missing_elements', []))}</p>
                <p><strong>💡 Suggestions:</strong> {str(v_res.get('improvement_suggestions'))}</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.warning("Raw Verify Output: " + st.session_state.verify_result)

    st.markdown("### JSON Structure")
    json_val = st.text_area("JSON", st.session_state.json_content, height=600)
    if json_val != st.session_state.json_content:
        st.session_state.json_content = json_val
        
with col2:
    st.subheader("2. Live Preview (Absolute Grid)")
    valid, res = validate_json(st.session_state.json_content)
    if valid:
        render_preview(res)
    else:
        st.error(f"JSON Error: {res}")
