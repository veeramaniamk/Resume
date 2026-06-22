import requests
import sys

with open('Spring-boot.tex', 'r', encoding='utf-8') as f:
    tex_content = f.read()

print("Testing compilation with texlive.net...")
files = {
    'filecontents[]': ('document.tex', tex_content),
    'filename[]': (None, 'document.tex'),
    'engine': (None, 'pdflatex'),
    'return': (None, 'pdf')
}

response = requests.post('https://texlive.net/cgi-bin/latexcgi', files=files)

if response.status_code == 200 and response.content.startswith(b'%PDF'):
    with open('Spring-boot-test.pdf', 'wb') as f:
        f.write(response.content)
    print("Success! texlive.net successfully compiled it.")
else:
    print(f"Failed. HTTP {response.status_code}")
    print(response.text[:500])
