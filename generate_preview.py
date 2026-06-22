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
    print(f"Converting {os.path.basename(pdf_path)} to PNG(s)...")
    base_png_path = pdf_path.replace('.pdf', '')
    
    # Open the PDF document
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        print("Empty PDF.")
        return []
        
    png_paths = []
    zoom = 2.0 
    mat = fitz.Matrix(zoom, zoom)
    
    for i in range(len(doc)):
        # Load each page
        page = doc.load_page(i)
        
        # Render page to an image (zoom for higher resolution)
        pix = page.get_pixmap(matrix=mat)
        
        # Save the image
        if len(doc) == 1:
            png_path = f"{base_png_path}.png"
        else:
            png_path = f"{base_png_path}-page{i+1}.png"
            
        pix.save(png_path)
        png_paths.append(png_path)
        print(f"Successfully created preview image {os.path.basename(png_path)}")
        
    return png_paths

def generate_readme(compiled_results):
    print("Generating README.md...")
    readme_path = os.path.join(WORKSPACE_DIR, 'README.md')
    
    content = "# Resume\n\n"
    content += "This repository contains my LaTeX resume. The preview below is automatically generated and kept up to date!\n\n"
    
    for tex, png_files in compiled_results.items():
        base_name = os.path.basename(tex)
        pdf_name = base_name.replace('.tex', '.pdf')
        
        content += f"## {base_name}\n\n"
        content += f"📄 **[Download PDF]({pdf_name})**\n\n"
        
        for png in png_files:
            png_base = os.path.basename(png)
            content += f"![Resume Preview]({png_base})\n\n"
        
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
    compiled_results = {}
    
    try:
        for tex_file in tex_files:
            tex_name = os.path.basename(tex_file)
            pdf_path = compile_latex(tex_name, tarball_path)
            if pdf_path:
                png_paths = convert_pdf_to_png(pdf_path)
                if png_paths:
                    compiled_results[tex_file] = png_paths
    finally:
        if os.path.exists(tarball_path):
            os.remove(tarball_path)
            
    if compiled_results:
        generate_readme(compiled_results)
    else:
        print("No previews generated successfully.")

if __name__ == "__main__":
    main()
