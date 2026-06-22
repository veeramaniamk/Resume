import os
import glob
import requests
import fitz  # PyMuPDF
import sys

# Configuration
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://texlive.net/cgi-bin/latexcgi"
COMMAND = "pdflatex"

def compile_latex(target_tex_name):
    print(f"Compiling {target_tex_name} via texlive.net...")
    
    tex_file_path = os.path.join(WORKSPACE_DIR, target_tex_name)
    with open(tex_file_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    files = {
        'filecontents[]': ('document.tex', tex_content),
        'filename[]': (None, 'document.tex'),
        'engine': (None, COMMAND),
        'return': (None, 'pdf')
    }
    
    response = requests.post(API_URL, files=files)
    
    if response.status_code == 200 and response.content.startswith(b'%PDF'):
        pdf_path = os.path.join(WORKSPACE_DIR, target_tex_name.replace('.tex', '.pdf'))
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        print(f"Successfully compiled to {os.path.basename(pdf_path)}")
        return pdf_path
    else:
        print(f"Error compiling {target_tex_name}: HTTP {response.status_code}")
        print(response.text[:500])
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
    
    compiled_results = {}
    
    for tex_file in tex_files:
        tex_name = os.path.basename(tex_file)
        pdf_path = compile_latex(tex_name)
        if pdf_path:
            png_paths = convert_pdf_to_png(pdf_path)
            if png_paths:
                compiled_results[tex_file] = png_paths
            
    if compiled_results:
        generate_readme(compiled_results)
    else:
        print("No previews generated successfully.")
        sys.exit(1)

if __name__ == "__main__":
    main()
