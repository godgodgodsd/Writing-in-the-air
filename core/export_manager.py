"""
Export Manager
Handles canvas export to multiple formats:
- JPEG
- PNG
- PDF
"""

import os
import cv2
from datetime import datetime


class ExportManager:

    def __init__(self, export_dir="exports"):
        self.export_dir = export_dir
        # Create exports directory if it doesn't exist
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

    def export_jpeg(self, canvas):
        """Export canvas as JPEG"""
        filename = self._generate_filename("jpg")
        filepath = os.path.join(self.export_dir, filename)
        
        # Convert BGRA to BGR for JPEG
        bgr_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGRA2BGR)
        cv2.imwrite(filepath, bgr_canvas)
        return filepath

    def export_png(self, canvas):
        """Export canvas as PNG"""
        filename = self._generate_filename("png")
        filepath = os.path.join(self.export_dir, filename)
        
        cv2.imwrite(filepath, canvas)
        return filepath

    def export_pdf(self, canvas):
        """Export canvas as PDF using PIL"""
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("PIL/Pillow is required for PDF export. Install it with: pip install pillow")
        
        filename = self._generate_filename("pdf")
        filepath = os.path.join(self.export_dir, filename)
        
        # Convert BGRA to RGB for PIL
        bgr_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGRA2BGR)
        rgb_canvas = cv2.cvtColor(bgr_canvas, cv2.COLOR_BGR2RGB)
        
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(rgb_canvas)
        pil_image.save(filepath, "PDF")
        return filepath

    def _generate_filename(self, format_ext):
        """Generate a unique filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"paint_export_{timestamp}.{format_ext}"

    def export(self, canvas, export_format):
        """Export canvas in specified format"""
        format_lower = export_format.lower()
        
        if format_lower == "jpeg" or format_lower == "jpg":
            return self.export_jpeg(canvas)
        elif format_lower == "png":
            return self.export_png(canvas)
        elif format_lower == "pdf":
            return self.export_pdf(canvas)
        else:
            raise ValueError(f"Unsupported format: {export_format}")
