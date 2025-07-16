from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_birth_certificate(filename="sample_birth_certificate.png"):
    """
    Create a sample birth certificate image for testing.
    """
    # Create a new image with white background
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        header_font = ImageFont.truetype("arial.ttf", 18)
        text_font = ImageFont.truetype("arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Colors
    black = (0, 0, 0)
    blue = (0, 0, 139)
    
    # Title
    title = "CERTIFICATE OF BIRTH"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, 50), title, fill=blue, font=title_font)
    
    # Header
    header = "STATE OF CALIFORNIA"
    header_bbox = draw.textbbox((0, 0), header, font=header_font)
    header_width = header_bbox[2] - header_bbox[0]
    draw.text(((width - header_width) // 2, 80), header, fill=black, font=header_font)
    
    # Certificate details
    y_pos = 150
    line_height = 30
    
    details = [
        ("Full Name:", "Alice Johnson"),
        ("Date of Birth:", "March 15, 1998"),
        ("Place of Birth:", "Los Angeles, California"),
        ("Father's Name:", "Robert Johnson"),
        ("Mother's Name:", "Maria Johnson"),
        ("Certificate Number:", "BC-2023-001234"),
        ("Date of Registration:", "March 20, 1998")
    ]
    
    for label, value in details:
        draw.text((100, y_pos), label, fill=black, font=text_font)
        draw.text((300, y_pos), value, fill=black, font=text_font)
        y_pos += line_height
    
    # Add some official-looking elements
    draw.rectangle((50, 40, width-50, height-50), outline=black, width=2)
    draw.rectangle((60, 120, width-60, height-60), outline=black, width=1)
    
    # Footer
    footer = "OFFICIAL DOCUMENT - NOT VALID FOR LEGAL PURPOSES (SAMPLE ONLY)"
    footer_bbox = draw.textbbox((0, 0), footer, font=text_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(((width - footer_width) // 2, height - 80), footer, fill=blue, font=text_font)
    
    # Save the image
    img.save(filename)
    print(f"Sample birth certificate created: {filename}")
    return filename

if __name__ == "__main__":
    create_sample_birth_certificate() 