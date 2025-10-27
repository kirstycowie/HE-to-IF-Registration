import openslide
import SimpleITK as sitk
import numpy as np
from PIL import Image
import os

# --- Paths ---
wsi_path = r"C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\OneDrive_2_22-07-2025\2025-05-20 09.39.25_animal4.ndpi"
transform_path = r"C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\IFtransforms\animal4_inverse_HtoIF.tfm"
if_path = r"C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\IFs\animal4.png"
output_folder = r"C:\Users\gvb24177\OneDrive - University of Strathclyde\Kirsty PHD\registrationPractice_July2025\RegisteredPatches_IFaligned"

os.makedirs(output_folder, exist_ok=True)

# --- Load WSI and IF images ---
slide = openslide.OpenSlide(wsi_path)
if_img = sitk.ReadImage(if_path)
transform = sitk.ReadTransform(transform_path)

# --- Patch parameters ---
patch_size = 4096
overlap = 128
level = 0
wsi_w, wsi_h = slide.level_dimensions[level]
print(f"WSI size: {wsi_w} x {wsi_h}")

xs = list(range(0, wsi_w, patch_size - overlap))
ys = list(range(0, wsi_h, patch_size - overlap))

print("Transform matrix:", transform.GetMatrix())
print("Transform translation:", transform.GetTranslation())


# --- Loop through patches ---
for i, y in enumerate(ys):
    for j, x in enumerate(xs):
        print(f"Processing patch at ({x}, {y})")

        # --- 1️⃣ Extract patch ---
        w = min(patch_size, wsi_w - x)
        h = min(patch_size, wsi_h - y)
        patch = slide.read_region((x, y), level, (w, h)).convert("RGB")
        patch_np = np.array(patch)

        # --- 2️⃣ Convert patch to SimpleITK RGB image ---
        patch_rgb = sitk.GetImageFromArray(patch_np, isVector=True)
        patch_rgb.SetOrigin((x, y))
        patch_rgb.SetSpacing(if_img.GetSpacing())

        # --- 3️⃣ Resample the RGB image using the transform ---
        resampler = sitk.ResampleImageFilter()
        resampler.SetTransform(transform)
        resampler.SetInterpolator(sitk.sitkLinear)
        resampler.SetDefaultPixelValue(0)
        resampler.SetReferenceImage(if_img)

        transformed_rgb = resampler.Execute(patch_rgb)

        # --- 4️⃣ Convert back to NumPy and save ---
        transformed_np = sitk.GetArrayFromImage(transformed_rgb)
        transformed_np = np.clip(transformed_np, 0, 255).astype(np.uint8)

        # --- 5️⃣ Save patch ---
        out_path = os.path.join(output_folder, f"patch_y{y}_x{x}.tif")
        Image.fromarray(transformed_np).save(out_path)
        print(f"Saved: {out_path}")

slide.close()
print("✅ All patches transformed into IF space!")

print("Transform matrix:", transform.GetMatrix())
print("Transform translation:", transform.GetTranslation())

print("IF origin:", if_img.GetOrigin())
print("IF spacing:", if_img.GetSpacing())
print("IF size:", if_img.GetSize())

print("Patch origin:", patch_rgb.GetOrigin())
print("IF size:", if_img.GetSize())
print("IF spacing:", if_img.GetSpacing())
