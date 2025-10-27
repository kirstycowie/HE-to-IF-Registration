# --- Run this with ---
# python -m streamlit run "C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\HE_to_IF_app.py"

import os
import numpy as np
from PIL import Image
import streamlit as st
import SimpleITK as sitk
from streamlit_drawable_canvas import st_canvas

def rescale_affine_transform(transform, scale_factor):
    """
    Rescale a 2D SimpleITK AffineTransform by a uniform scale factor.
    This assumes the transform was estimated on a downsampled image
    and needs to be applied on a full-resolution one.
    """
    if not isinstance(transform, sitk.AffineTransform):
        raise ValueError("Transform must be a SimpleITK AffineTransform.")

    A = np.array(transform.GetMatrix()).reshape(2, 2)
    t = np.array(transform.GetTranslation())
    center = np.array(transform.GetCenter())

    # Rescale translation and center
    t_rescaled = t * scale_factor
    center_rescaled = center * scale_factor

    # Build new transform
    scaled_transform = sitk.AffineTransform(2)
    scaled_transform.SetMatrix(A.flatten())
    scaled_transform.SetTranslation(t_rescaled.tolist())
    scaled_transform.SetCenter(center_rescaled.tolist())

    return scaled_transform

# --- Helper functions ---
def compute_display_size(w, h, max_display=1000):
    """Scale image to fit browser while preserving aspect ratio."""
    if max(w, h) <= max_display:
        return w, h
    scale = max_display / max(w, h)
    return int(round(w * scale)), int(round(h * scale))

def select_points(image, key, display_width=None):
    """Interactive point selection for Streamlit canvas."""
    iw, ih = image.size
    if display_width:
        dw = display_width
        dh = int(dw * ih / iw)
    else:
        dw, dh = iw, ih
    img_resized = image.resize((dw, dh), Image.LANCZOS)

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="red",
        background_image=img_resized,
        height=dh,
        width=dw,
        drawing_mode="point",
        key=f"canvas_{key}"
    )

    points = []
    if canvas_result.json_data and "objects" in canvas_result.json_data:
        for obj in canvas_result.json_data["objects"]:
            if "left" in obj and "top" in obj:
                orig_x = obj["left"] * (iw / dw)
                orig_y = obj["top"] * (ih / dh)
                points.append((float(orig_x), float(orig_y)))

    if 3 <= len(points) <= 10:
        st.success(f"{len(points)} points selected.")
    elif len(points) < 3:
        st.warning("Select at least 3 points.")
    else:
        st.warning("Too many points — only first 10 used.")
        points = points[:10]

    return points

# --- Paths ---
he_folder = r'C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\HEWSIthumbnails2'
if_folder = r'C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\IFs'
transform_folder = r"C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\IFtransforms"

# --- Collect available animal numbers ---
he_files = [f for f in os.listdir(he_folder) if f.lower().endswith(".png")]
if_files = [f for f in os.listdir(if_folder) if f.lower().endswith(".tif")]
extract_number = lambda f: ''.join([c for c in f if c.isdigit()])

he_numbers = {extract_number(f) for f in he_files}
if_numbers = {extract_number(f) for f in if_files}
common_numbers = sorted(he_numbers & if_numbers)

# --- Streamlit UI ---
st.title("Manual Landmark-Based IF → H&E Registration")
if not common_numbers:
    st.error("No matching H&E and IF images found.")
    st.stop()

animal_number = st.selectbox("Select Animal Number", common_numbers)
he_path = os.path.join(he_folder, f"animal{animal_number}.png")
if_path = os.path.join(if_folder, f"animal{animal_number}.tif")
#svg_path = os.path.join(if_folder, f"animal{animal_number}.svg")

# --- Load images ---
he_img = Image.open(he_path).convert("RGB")
if_img = Image.open(if_path).convert("RGB")
#if_img = load_svg_as_image(svg_path)

# --- Display images for point selection ---
disp_w = 800
st.markdown("### Select landmarks on the H&E (Fixed) image")
fixed_points = select_points(he_img, "fixed", display_width=disp_w)

st.markdown("---")
st.markdown("### Select corresponding landmarks on the IF (Moving) image")
moving_points = select_points(if_img, "moving", display_width=disp_w)

# --- Perform registration ---
if not (3 <= len(fixed_points) <= 10 and 3 <= len(moving_points) <= 10):
    st.info("Select 3–10 landmarks on both images.")
elif len(fixed_points) != len(moving_points):
    st.error("Number of landmarks must match.")
else:
    fixed_flat = [float(c) for p in fixed_points for c in p]
    moving_flat = [float(c) for p in moving_points for c in p]

    transform = sitk.AffineTransform(2)
    initializer = sitk.LandmarkBasedTransformInitializerFilter()
    initializer.SetFixedLandmarks(fixed_flat)
    initializer.SetMovingLandmarks(moving_flat)

    try:
        output_transform = initializer.Execute(transform)
        scale_factor = 16
        output_transform_scaled = rescale_affine_transform(output_transform, scale_factor)
        inv_transform = output_transform_scaled.GetInverse()
        st.success("Registration successful!")
    except Exception as e:
        st.error(f"Could not compute transform: {e}")
        output_transform = None
        inv_transform = None

    # --- Save inverse transform (H&E → IF) ---
    if inv_transform and st.button("Save Inverse Transform (H&E → IF)"):
        os.makedirs(transform_folder, exist_ok=True)
        inv_path = os.path.join(transform_folder, f"animal{animal_number}_inverse_HtoIF.tfm")
        sitk.WriteTransform(inv_transform, inv_path)
        st.success(f"Saved inverse transform:\n{inv_path}")
