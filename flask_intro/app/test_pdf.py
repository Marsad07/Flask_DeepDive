from xhtml2pdf import pisa
from io import BytesIO

html_content = """
<html>
<head>
    <style>
        body { background-color: #FFFDD0; font-family: Arial; }
        h1 { color: #008080; }
    </style>
</head>
<body>
    <h1>Test PDF - Atlas Desk</h1>
    <p>If you can see this, xhtml2pdf is working!</p>
</body>
</html>
"""

with open('test_output.pdf', 'wb') as pdf_file:
    pisa.CreatePDF(html_content, dest=pdf_file)

print("PDF created successfully! Check for test_output.pdf")