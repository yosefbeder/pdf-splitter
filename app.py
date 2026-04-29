import io
import zipfile
from flask import Flask, request, send_file, flash, render_template_string, make_response

import fitz  # PyMuPDF

app = Flask(__name__)
app.secret_key = "super_secret_pdf_splitter_key"  # Needed for flash messages

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Splitter</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --primary-color: #3b82f6;
            --primary-hover: #2563eb;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --error-bg: #7f1d1d;
            --error-text: #fca5a5;
            --success-bg: #064e3b;
            --success-text: #6ee7b7;
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-image: radial-gradient(circle at top right, #1e1b4b, #0f172a);
        }

        .container {
            width: 100%;
            max-width: 600px;
            background: var(--surface-color);
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.05);
            animation: fadeIn 0.6s ease-out;
            margin: 20px;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            margin-top: 0;
            font-size: 2rem;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
            text-align: center;
        }

        .form-group {
            margin-bottom: 1.5rem;
            position: relative;
        }

        .label-wrapper {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            gap: 0.5rem;
        }

        label {
            font-weight: 500;
            color: #e2e8f0;
        }

        .tooltip-icon {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--border-color);
            color: var(--text-muted);
            font-size: 11px;
            font-weight: bold;
            cursor: pointer;
            position: relative;
            transition: all 0.2s;
        }

        .tooltip-icon:hover {
            background: var(--primary-color);
            color: white;
        }

        .tooltip-text {
            visibility: hidden;
            opacity: 0;
            width: max-content;
            max-width: 280px;
            background-color: #334155;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 10px 14px;
            position: absolute;
            z-index: 10;
            bottom: 135%;
            left: 50%;
            transform: translateX(-50%) translateY(10px);
            transition: opacity 0.3s, transform 0.3s;
            font-size: 0.85rem;
            font-weight: normal;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
            line-height: 1.5;
        }

        .tooltip-text::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -6px;
            border-width: 6px;
            border-style: solid;
            border-color: #334155 transparent transparent transparent;
        }

        .tooltip-icon:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        input[type="number"],
        input[type="file"],
        textarea {
            width: 100%;
            padding: 0.75rem;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-main);
            font-family: inherit;
            box-sizing: border-box;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        input[type="number"]:focus,
        textarea:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }

        textarea {
            resize: vertical;
            min-height: 180px;
            font-family: monospace;
            font-size: 0.9rem;
            line-height: 1.4;
        }

        /* Checkbox styling */
        .checkbox-wrapper {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .checkbox-wrapper input[type="checkbox"] {
            width: 1.2rem;
            height: 1.2rem;
            accent-color: var(--primary-color);
            cursor: pointer;
        }

        button {
            width: 100%;
            padding: 1rem;
            margin-top: 1.5rem;
            background: linear-gradient(135deg, var(--primary-color), #8b5cf6);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
        }

        button:active {
            transform: translateY(0);
        }

        .flash-messages {
            margin-bottom: 1.5rem;
        }

        .flash {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }

        .flash.error {
            background: var(--error-bg);
            color: var(--error-text);
            border: 1px solid #991b1b;
        }

        .flash.success {
            background: var(--success-bg);
            color: var(--success-text);
            border: 1px solid #047857;
        }

        /* Loading Overlay */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 0;
            visibility: hidden;
            transition: all 0.4s ease;
        }

        .loading-overlay.active {
            opacity: 1;
            visibility: visible;
        }

        .loading-content {
            text-align: center;
            max-width: 400px;
            padding: 2rem;
        }

        .loading-video-container {
            position: relative;
            width: 100%;
            max-width: 320px;
            margin: 0 auto 2rem;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .loading-content video {
            width: 100%;
            display: block;
        }

        .loading-text {
            font-size: 1.25rem;
            font-weight: 500;
            color: var(--text-main);
            margin-bottom: 0.5rem;
        }

        .loading-subtext {
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        .close-loading {
            margin-top: 2rem;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            display: none;
        }

        .close-loading:hover {
            background: rgba(255,255,255,0.2);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .animate-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
    </style>
</head>
<body>
    <div id="loading-overlay" class="loading-overlay">
        <div class="loading-content">
            <div class="loading-video-container">
                <video id="loading-video" loop muted playsinline>
                    <source src="/static/cutting-paper-machine.mp4" type="video/mp4">
                </video>
            </div>
            <div class="loading-text animate-pulse">Processing your PDF...</div>
            <div class="loading-subtext">This might take a few seconds depending on the file size.</div>
            <button id="close-loading" class="close-loading">Close Overlay</button>
        </div>
    </div>

    <div class="container">
        <h1>PDF Splitter</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <form id="split-form" method="POST" enctype="multipart/form-data">
            
            <div class="form-group">
                <div class="label-wrapper">
                    <label for="pdf_file">Upload Source PDF</label>
                    <div class="tooltip-icon">i
                        <span class="tooltip-text">Select the master PDF document that you want to split into smaller sections.</span>
                    </div>
                </div>
                <input type="file" id="pdf_file" name="pdf_file" accept=".pdf" required>
            </div>

            <div class="form-group">
                <div class="label-wrapper">
                    <label for="page_offset">Page Offset</label>
                    <div class="tooltip-icon">i
                        <span class="tooltip-text">Added to input pages. Adjust this if the printed page numbers differ from the PDF's absolute page. E.g. if logical page 1 is physical page 15, set to 14.</span>
                    </div>
                </div>
                <input type="number" id="page_offset" name="page_offset" value="0" required>
            </div>

            <div class="form-group">
                <div class="label-wrapper">
                    <label for="sections">Sections (CSV)</label>
                    <div class="tooltip-icon">i
                        <span class="tooltip-text">
                            Paste a list or CSV with two columns: <b>Page Number</b> and <b>File Name</b>.<br><br>
                            Example format:<br>
                            5, "TantaUnive_GIT"<br>
                            8, "TantaUnive_GIT_2"<br>
                            Sections mapped to 'None' will be skipped.
                        </span>
                    </div>
                </div>
                <!-- Default value prepopulated for convenience just like the script --><textarea id="sections" name="sections" required>
2,TantaUnive_ENDOCRINE_REPRODUCTIVE_ANATOMY_OF_PITUITARY_GLAND
4,TantaUnive_ENDOCRINE_REPRODUCTIVE_DEVELOPMENT_OF_PITUITARY_GLAND
5,TantaUnive_ENDOCRINE_REPRODUCTIVE_HISTOLOGY_OF_PITUITARY_GLAND
10,TantaUnive_ENDOCRINE_REPRODUCTIVE_BIOCHEMISTRY_OF_HORMONES
16,TantaUnive_ENDOCRINE_REPRODUCTIVE_HORMONES_OF_PITUITARY_GLAND_THE_HYPOPHYSIS
16,TantaUnive_ENDOCRINE_REPRODUCTIVE_ANTERIOR_PITUITARY_HORMONES
22,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHYSIOLOGY_OF_GROWTH
25,TantaUnive_ENDOCRINE_REPRODUCTIVE_POSTERIOR_PITUITARY_HORMONES
28,TantaUnive_ENDOCRINE_REPRODUCTIVE_PITUITARY_HORMONES_PREPARATIONS
34,TantaUnive_ENDOCRINE_REPRODUCTIVE_ANATOMY_OF_PINEAL_GLAND
35,TantaUnive_ENDOCRINE_REPRODUCTIVE_MELATONIN_HORMONE
38,TantaUnive_ENDOCRINE_REPRODUCTIVE_ANATOMY_OF_THYROID_GLAND
39,TantaUnive_ENDOCRINE_REPRODUCTIVE_DEVELOPMENT_OF_THYROID_GLAND
43,TantaUnive_ENDOCRINE_REPRODUCTIVE_HISTOLOGY_OF_THYROID_GLAND
46,TantaUnive_ENDOCRINE_REPRODUCTIVE_BIOCHEMISTRY_OF_THYROID_HORMONE
49,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHYSIOLOGY_OF_THYROID_GLAND
54,TantaUnive_ENDOCRINE_REPRODUCTIVE_PATHOLOGICAL_FEATURES_OF_THYROID_GLAND_DISORDERS
71,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHARMACOLOGY_OF_THYROID_DISORDERS
78,TantaUnive_ENDOCRINE_REPRODUCTIVE_ANATOMY_OF_PARATHYROID_GLAND
79,TantaUnive_ENDOCRINE_REPRODUCTIVE_DEVELOPMENT_OF_PARATHYROID_GLAND
80,TantaUnive_ENDOCRINE_REPRODUCTIVE_HISTOLOGY_OF_PARATHYROID_GLAND
83,TantaUnive_ENDOCRINE_REPRODUCTIVE_BIOCHEMISTRY_OF_HORMONES_REGULATING_CA_HOMEOSTASIS
86,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHYSIOLOGY_OF_HORMONES_REGULATING_CA_HOMEOSTASIS
93,TantaUnive_ENDOCRINE_REPRODUCTIVE_HISTOLOGY_OF_ENDOCRINE_PART_OF_PANCREAS
96,TantaUnive_ENDOCRINE_REPRODUCTIVE_BIOCHEMISTRY_OF_HORMONES_OF_ENDOCRINE_PANCREAS_INSULIN_RESISTANCE
109,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHYSIOLOGY_OF_ENDOCRINE_PART_OF_PANCREAS
115,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHARMACOLOGY_OF_DIABETES_MELLITUS
124,TantaUnive_ENDOCRINE_REPRODUCTIVE_ANATOMY_OF_SUPRARENAL_ADRENAL_GLANDS
126,TantaUnive_ENDOCRINE_REPRODUCTIVE_DEVELOPMENT_AND_OF_SUPRA_RENAL_GLAND
127,TantaUnive_ENDOCRINE_REPRODUCTIVE_HISTOLOGY_OF_SUPRARENAL_GLAND
133,TantaUnive_ENDOCRINE_REPRODUCTIVE_BIOCHEMISTRY_OF_HORMONES_OF_ADRENAL_GLAND
138,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHYSIOLOGY_OF_ADRENAL_GLAND_HORMONES
146,TantaUnive_ENDOCRINE_REPRODUCTIVE_TUMORS_OF_ADRENAL_GLANS
149,TantaUnive_ENDOCRINE_REPRODUCTIVE_PHARMACOLOGY_OF_ADRENAL_DISORDERS

                </textarea>
            </div>

            <div class="checkbox-wrapper">
                <input type="checkbox" id="include_last_page" name="include_last_page" checked>
                <div class="label-wrapper" style="margin: 0;">
                    <label for="include_last_page" style="cursor:pointer;">Include Last Page</label>
                    <div class="tooltip-icon">i
                        <span class="tooltip-text">
                            <b>Active:</b> Output includes the ending page.<br>
                            (e.g., 5 to 8 -> pages 5, 6, 7, 8)<br><br>
                            <b>Inactive:</b> Output stops before the ending page.<br>
                            (e.g., 5 to 7 -> pages 5, 6, 7)
                        </span>
                    </div>
                </div>
            </div>

            <button type="submit" id="submit-btn">Process & Download ZIP</button>
        </form>
    </div>

    <script>
        const form = document.getElementById('split-form');
        const overlay = document.getElementById('loading-overlay');
        const video = document.getElementById('loading-video');
        const closeBtn = document.getElementById('close-loading');

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
        }

        form.onsubmit = function() {
            // Check if form is valid before showing overlay
            if (form.checkValidity()) {
                overlay.classList.add('active');
                video.play();
                
                // Clear any existing cookie
                document.cookie = "fileDownload=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

                // Poll for the download cookie
                const checkDownload = setInterval(() => {
                    if (getCookie('fileDownload')) {
                        // Clear the cookie
                        document.cookie = "fileDownload=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                        // Hide loading
                        overlay.classList.remove('active');
                        video.pause();
                        clearInterval(checkDownload);
                    }
                }, 500);

                // Fallback close button after 10 seconds
                setTimeout(() => {
                    closeBtn.style.display = 'inline-block';
                }, 10000);
            }
        };

        closeBtn.onclick = function() {
            overlay.classList.remove('active');
            video.pause();
        };

        // If page is shown from cache (back button), hide overlay
        window.onpageshow = function(event) {
            if (event.persisted) {
                overlay.classList.remove('active');
                video.pause();
            }
        };
    </script>
</body>
</html>
"""

def parse_sections(sections_text):
    """
    Robustly parses section lines pasted from Python, CSV, or Tab-Separated.
    """
    sections = []
    for line in sections_text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        # Clean up commas, parens, and spaces
        # Turn '(5, "File"),' -> '5, "File"'
        line = line.strip("(), ")
        
        # Split by comma or whitespace depending on structure
        if ',' in line:
            parts = line.split(',', 1)
        else:
            parts = line.split(None, 1)
            
        if len(parts) >= 2:
            try:
                page = int(parts[0].strip())
                # Handle quoted strings
                name = parts[1].strip(' \t"\'')
                if name.lower() == 'none' or not name:
                    name = None
                sections.append((page, name))
            except ValueError:
                pass # skip invalid formats silently like a good web app
    return sections

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash("No file was uploaded.", "error")
            return render_template_string(HTML_TEMPLATE)
        
        file = request.files['pdf_file']
        if file.filename == '':
            flash("No selected file.", "error")
            return render_template_string(HTML_TEMPLATE)
            
        try:
            page_offset = int(request.form.get('page_offset', 0))
        except ValueError:
            page_offset = 0
            
        include_last_page = request.form.get('include_last_page') == 'on'
        
        sections_text = request.form.get('sections', '')
        sections = parse_sections(sections_text)
        
        if not sections:
            flash("No valid sections were parsed. Please check the CSV format.", "error")
            return render_template_string(HTML_TEMPLATE)
            
        # Sort sections by page number to guarantee ascending order
        sections = sorted(sections, key=lambda x: x[0])
        
        try:
            # Read source PDF entirely into memory
            pdf_bytes = file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)
            
            # Use an in-memory BytesIO object to create the ZIP file
            memory_zip_file = io.BytesIO()
            with zipfile.ZipFile(memory_zip_file, 'w') as zf:
                
                for i, (printed_page, file_id) in enumerate(sections):
                    # Calculate 0-indexed start page
                    start_idx = printed_page + page_offset - 1
                    
                    if i + 1 < len(sections):
                        next_printed_page = sections[i + 1][0]
                        end_idx = next_printed_page + page_offset - 1
                        
                        # If include_last_page is disabled, do not include the page marking the start of the next section
                        if not include_last_page:
                            end_idx -= 1
                    else:
                        # The last section goes to the very end of the document
                        end_idx = total_pages - 1
                        
                    # Bounds checking safety
                    start_idx = max(0, start_idx)
                    end_idx = min(total_pages - 1, end_idx)
                    
                    # If this block is marked None, skip processing
                    if file_id is None:
                        continue
                        
                    if start_idx > end_idx:
                        continue
                        
                    # Extract the page slice and save
                    new_doc = fitz.open()
                    new_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx)
                    
                    pdf_out = io.BytesIO()
                    new_doc.save(pdf_out)
                    new_doc.close()
                    
                    # Add to the ZIP archive
                    filename = f"{file_id}.pdf"
                    zf.writestr(filename, pdf_out.getvalue())
            
            doc.close()
            
            # Point to start of ZIP in memory
            memory_zip_file.seek(0)
            
            response = make_response(send_file(
                memory_zip_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name='split_pdfs.zip'
            ))
            response.set_cookie('fileDownload', 'true', path='/')
            return response
            
        except Exception as e:
            flash(f"An error occurred while processing the PDF: {str(e)}", "error")
            
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, port=5001)