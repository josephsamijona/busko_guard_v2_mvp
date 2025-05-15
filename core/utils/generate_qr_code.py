# utils.py
import qrcode
from io import BytesIO
import base64
from django.utils.html import format_html

def generate_qr_code(data, as_html=False, width=150, height=150):
    """
    Génère une image QR code à partir d'une chaîne de caractères.
    
    Args:
        data: La chaîne à encoder dans le QR code
        as_html: Si True, retourne une balise HTML img, sinon retourne l'URL data en base64
        width/height: Dimensions de l'image si as_html=True
    
    Returns:
        Une chaîne contenant soit une URL data en base64, soit une balise img HTML
    """
    if not data:
        return None
        
    # Création d'un QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Création d'une image
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # URL de l'image en base64
    img_url = f"data:image/png;base64,{img_str}"
    
    # Retourne soit l'URL, soit une balise HTML img
    if as_html:
        return format_html('<img src="{}" width="{}" height="{}"/>', 
                          img_url, width, height)
    return img_url