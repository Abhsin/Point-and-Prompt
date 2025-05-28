from PIL import Image
import pytesseract
import os

def extract_text_from_image(image: Image.Image, tesseract_path: str = None, lang: str = 'eng') -> str:
    """
    Extract text from a PIL image using pytesseract.
    Optionally specify the path to the tesseract executable (needed on Windows).
    """
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        # Try to use the environment variable if set
        tesseract_env = os.getenv('TESSERACT_PATH')
        if tesseract_env:
            pytesseract.pytesseract.tesseract_cmd = tesseract_env
    
    try:
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception as e:
        print(f"OCR extraction failed: {e}")
        return ""

if __name__ == '__main__':
    # Test OCR on a sample image
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update if needed
    try:
        test_img = Image.open("captured_region.png")
        print("Loaded 'captured_region.png' for OCR test.")
    except FileNotFoundError:
        try:
            test_img = Image.open("test_image.png")
            print("Loaded 'test_image.png' for OCR test.")
        except FileNotFoundError:
            print("No test image found, creating a dummy one with text.")
            from PIL import ImageDraw, ImageFont
            test_img = Image.new('RGB', (300, 100), color = 'white')
            draw = ImageDraw.Draw(test_img)
            draw.text((10, 40), "Hello OCR!", fill="black")
            test_img.save("test_image.png")
    
    extracted_text = extract_text_from_image(test_img, tesseract_path=tesseract_path)
    print("\n--- OCR Extracted Text ---")
    print(extracted_text)
    print("-------------------------") 