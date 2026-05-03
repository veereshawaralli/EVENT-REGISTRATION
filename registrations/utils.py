import io
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings

def generate_certificate_pdf(registration):
    """
    Generate a PDF certificate for a confirmed registration.
    Returns the raw PDF bytes if successful, else None.
    """
    import os
    import copy
    from django.conf import settings
    template_path = 'events/certificate_pdf.html'
    
    # Check for custom certificate template
    cert_template = getattr(registration.event, 'certificate_template', None)
    
    if cert_template and cert_template.background_image:
        bg_path = cert_template.background_image.path
    else:
        bg_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'cert_bg.png')
    
    # xhtml2pdf needs raw forward-slash paths (NOT file:/// URLs)
    bg_path = bg_path.replace('\\', '/')
        
    # Process layout text replacements
    # Mirror of the defaults in certificate_builder.html
    default_layout = {
        'title': { 'x': 50, 'y': 15, 'text': "CERTIFICATE", 'font_size': 48, 'color': "#1a2f4c", 'weight': "bold" },
        'subtitle': { 'x': 50, 'y': 28, 'text': "Of Achievement", 'font_size': 20, 'color': "#d4af37", 'weight': "normal" },
        'name': { 'x': 50, 'y': 45, 'text': "[Attendee Name]", 'font_size': 36, 'color': "#1a2f4c", 'weight': "normal" },
        'description': { 'x': 50, 'y': 65, 'text': f"Proudly presented for attending {registration.event.title}", 'font_size': 16, 'color': "#555555", 'weight': "normal" },
        'date': { 'x': 50, 'y': 85, 'text': "Issued: [Date]", 'font_size': 14, 'color': "#1a2f4c", 'weight': "normal" }
    }

    if cert_template and cert_template.layout and len(cert_template.layout) > 0:
        processed_layout = copy.deepcopy(cert_template.layout)
    else:
        processed_layout = default_layout
        
    # Get dynamic values
    attendee_name = registration.user.get_full_name() or registration.user.username
    event_date = registration.event.date.strftime("%B %d, %Y")
    organizer_name = registration.event.organizer.get_full_name() or registration.event.organizer.username
    
    for key, config in processed_layout.items():
        if 'text' in config:
            config['text'] = config['text'].replace('[Attendee Name]', attendee_name)
            config['text'] = config['text'].replace('[Date]', event_date)
            config['text'] = config['text'].replace('[Signature]', organizer_name)
    
    # ----------------------------------------------------------------
    # TABLE-BASED LAYOUT for xhtml2pdf
    # xhtml2pdf does NOT support position: absolute.
    # We must use tables with spacer rows for vertical positioning,
    # and padding/columns for horizontal positioning.
    # A4 Landscape = 297mm wide x 210mm tall.
    # ----------------------------------------------------------------
    PAGE_H = 210.0  # mm
    
    # Build a sorted list of elements by Y coordinate
    elements = []
    for key, config in processed_layout.items():
        y_pct = float(config.get('y', 50))
        x_pct = float(config.get('x', 50))
        font_size = float(config.get('font_size', 20))
        # Row height based on font size (1pt ≈ 0.353mm, with ~2x line height)
        row_height = font_size * 0.353 * 2.0
        # Top edge = center Y - half row height
        center_y = (y_pct / 100.0) * PAGE_H
        top_mm = max(0, center_y - (row_height / 2.0))
        
        elements.append({
            'key': key,
            'text': config.get('text', ''),
            'font_size': font_size,
            'color': config.get('color', '#000000'),
            'weight': config.get('weight', 'normal'),
            'x_pct': x_pct,
            'y_pct': y_pct,
            'top_mm': top_mm,
            'row_height': row_height,
        })
    
    # Sort by Y position
    elements.sort(key=lambda e: e['top_mm'])
    
    # Group elements that share the same Y into rows (tolerance: 5mm)
    rows = []
    for elem in elements:
        if rows and abs(elem['top_mm'] - rows[-1]['top_mm']) < 5.0:
            rows[-1]['items'].append(elem)
        else:
            rows.append({
                'top_mm': elem['top_mm'],
                'row_height': elem['row_height'],
                'items': [elem],
            })
    
    # Calculate spacer gaps and build final row data
    layout_rows = []
    current_y = 0.0
    
    for row in rows:
        gap = max(0, row['top_mm'] - current_y)
        row_height = max(e['row_height'] for e in row['items'])
        
        # Sort items in this row by X coordinate
        items = sorted(row['items'], key=lambda e: e['x_pct'])
        
        # Determine if this is a single centered element or multi-column
        if len(items) == 1:
            item = items[0]
            # Single element: use padding to shift center
            # x_pct=50 means centered, x_pct=20 means shifted left, etc.
            # We use asymmetric padding to move the visual center
            offset_pct = item['x_pct'] - 50.0  # negative=left, positive=right
            pad_left = max(0, offset_pct * 2.0)  # percentage points
            pad_right = max(0, -offset_pct * 2.0)
            
            layout_rows.append({
                'gap_mm': gap,
                'height_mm': row_height,
                'type': 'single',
                'text': item['text'],
                'font_size': item['font_size'],
                'color': item['color'],
                'weight': item['weight'],
                'pad_left_pct': pad_left,
                'pad_right_pct': pad_right,
            })
        else:
            # Multi-column row (e.g., date at x=20 and signature at x=80)
            # Each column gets equal width, with padding to shift text
            num_cols = len(items)
            col_width_pct = 100.0 / num_cols
            
            columns = []
            for i, item in enumerate(items):
                # Where this column's center should be vs where it actually is
                # Column i occupies from (i * col_width_pct) to ((i+1) * col_width_pct)
                col_center = (i + 0.5) * col_width_pct
                # Item wants to be at x_pct
                offset = item['x_pct'] - col_center
                pad_left = max(0, offset * 2.0)
                pad_right = max(0, -offset * 2.0)
                
                columns.append({
                    'text': item['text'],
                    'font_size': item['font_size'],
                    'color': item['color'],
                    'weight': item['weight'],
                    'x_pct': item['x_pct'],
                    'pad_left_pct': pad_left,
                    'pad_right_pct': pad_right,
                })
            
            layout_rows.append({
                'gap_mm': gap,
                'height_mm': row_height,
                'type': 'multi',
                'columns': columns,
            })
        
        current_y = row['top_mm'] + row_height
    
    # Context for the template
    context = {
        'registration': registration, 
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        'BG_PATH': bg_path,
        'cert': cert_template,
        'layout_rows': layout_rows,
    }
    
    template = get_template(template_path)
    html = template.render(context)

    # Create a file-like buffer to receive PDF data.
    result = io.BytesIO()

    # Generate PDF
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    
    return None
