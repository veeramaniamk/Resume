import os
import glob
import tarfile
import tempfile
import requests
import fitz  # PyMuPDF
import sys

# Configuration
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://latexonline.cc/data"
COMMAND = "pdflatex"

def create_tarball():
    fd, temp_path = tempfile.mkstemp(suffix=".tar.bz2")
    os.close(fd)
    
    with tarfile.open(temp_path, "w:bz2") as tar:
        for item in os.listdir(WORKSPACE_DIR):
            item_path = os.path.join(WORKSPACE_DIR, item)
            # Avoid adding git history or cache folders to save bandwidth
            if item in ['.git', '__pycache__'] or item.endswith('.pdf') or item.endswith('.png') or item.endswith('.tar.bz2'):
                continue
            tar.add(item_path, arcname=item)
            
    return temp_path

def compile_latex(target_tex_name, tarball_path):
    print(f"Compiling {target_tex_name} via latexonline.cc...")
    params = {
        'target': target_tex_name,
        'command': COMMAND,
        'force': 'true'
    }
    with open(tarball_path, 'rb') as f:
        files = {'file': f}
        # Allow redirects as latexonline uses 301/302 redirects
        response = requests.post(API_URL, params=params, files=files, allow_redirects=True)
    
    if response.status_code == 200:
        pdf_path = os.path.join(WORKSPACE_DIR, target_tex_name.replace('.tex', '.pdf'))
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        print(f"Successfully compiled to {os.path.basename(pdf_path)}")
        return pdf_path
    else:
        print(f"Error compiling {target_tex_name}: HTTP {response.status_code}")
        print(response.text)
        return None

def convert_pdf_to_png(pdf_path):
    print(f"Converting {os.path.basename(pdf_path)} to PNG...")
    png_path = pdf_path.replace('.pdf', '.png')
    
    # Open the PDF document
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        print("Empty PDF.")
        return None
        
    # Load first page
    page = doc.load_page(0)
    
    # Render page to an image (zoom for higher resolution)
    zoom = 2.0 
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Save the image
    pix.save(png_path)
    print(f"Successfully created preview image {os.path.basename(png_path)}")
    return png_path

def generate_readme(tex_files):
    print("Generating README.md...")
    readme_path = os.path.join(WORKSPACE_DIR, 'README.md')
    
    content = "# Resume\n\n"
    content += "This repository contains my LaTeX resume. The preview below is automatically generated and kept up to date!\n\n"
    
    for tex in tex_files:
        base_name = os.path.basename(tex)
        png_name = base_name.replace('.tex', '.png')
        pdf_name = base_name.replace('.tex', '.pdf')
        
        content += f"## {base_name}\n\n"
        content += f"📄 **[Download PDF]({pdf_name})**\n\n"
        content += f"![Resume Preview]({png_name})\n\n"
        
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("README.md updated successfully!")

def main():
    tex_files = glob.glob(os.path.join(WORKSPACE_DIR, "*.tex"))
    if not tex_files:
        print("No .tex files found in the directory.")
        return

    print(f"Found {len(tex_files)} LaTeX files to compile.")
    
    tarball_path = create_tarball()
    successful_compiles = []
    
    try:
        for tex_file in tex_files:
            tex_name = os.path.basename(tex_file)
            pdf_path = compile_latex(tex_name, tarball_path)
            if pdf_path:
                png_path = convert_pdf_to_png(pdf_path)
                if png_path:
                    successful_compiles.append(tex_file)
    finally:
        if os.path.exists(tarball_path):
            os.remove(tarball_path)
            
    if successful_compiles:
        generate_readme(successful_compiles)
    else:
        print("No previews generated successfully.")

if __name__ == "__main__":
    main()
