# preprocess_digits_no_rotate_no_crop.py
try:
    import cv2  # type: ignore
    HAS_CV2 = True
except Exception:
    cv2 = None  # type: ignore
    HAS_CV2 = False

import numpy as np
from pathlib import Path


def _ensure_dir_for(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def preprocess(in_path: str, out_path: str):
    """
    Preprocess scorecard images for OCR.
    On platforms without OpenCV (e.g., Streamlit Cloud), falls back to PIL-based processing.
    """
    if HAS_CV2:
        img = cv2.imread(in_path)
        assert img is not None, f"Bild nicht gefunden: {in_path}"

        # Signifikant verkleinern: längste Seite auf max. 1024 Pixel begrenzen
        MAX_LONG_SIDE = 2048
        h, w = img.shape[:2]
        long_side = max(h, w)
        if long_side > MAX_LONG_SIDE:
            scale = MAX_LONG_SIDE / long_side
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Graustufen
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Leicht entrauschen (erhält Kanten)
        gray = cv2.bilateralFilter(gray, d=5, sigmaColor=75, sigmaSpace=75)

        # Adaptives Thresholding (robust bei ungleichmäßiger Beleuchtung)
        bw = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
            blockSize=31, C=8
        )

        # Kleine Artefakte entfernen
        kernel = np.ones((2, 2), np.uint8)
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)

        # Leicht Kontrast anheben
        bw = cv2.convertScaleAbs(bw, alpha=1.15, beta=0)

        # Verlustfrei speichern (stark komprimiertes PNG)
        _ensure_dir_for(out_path)
        cv2.imwrite(out_path, bw, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    else:
        # Fallback ohne OpenCV: PIL verwenden
        from PIL import Image, ImageOps, ImageFilter

        img = Image.open(in_path)
        # Signifikant verkleinern: längste Seite auf max. 1024 Pixel
        MAX_LONG_SIDE = 1024
        w, h = img.size
        long_side = max(w, h)
        if long_side > MAX_LONG_SIDE:
            scale = MAX_LONG_SIDE / long_side
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)

        # In Graustufen konvertieren und leicht entrauschen
        gray = img.convert("L").filter(ImageFilter.MedianFilter(size=3))
        # Kontrast automatisch anpassen
        gray = ImageOps.autocontrast(gray, cutoff=2)
        # Einfaches Thresholding
        bw = gray.point(lambda p: 255 if p > 180 else 0)

        _ensure_dir_for(out_path)
        # PNG speichern mit Optimierung
        bw.save(out_path, format="PNG", optimize=True)

    print(["Pic preprocess done:", out_path])


if __name__ == "__main__":

    im1 = "WhatsApp Image 2025-10-02 at 20.35.25.jpeg"
    im2 = "WhatsApp Image 2025-10-02 at 20.35.42.jpeg"
    preprocess(im1, "IM1_prepr.png")
    preprocess(im2, "IM2_prepr.png")

