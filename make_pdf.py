
# Constructs the pdf from the html content.  Run it from the textbook root directory:
# python3 htmlbook/make_pdf.py && xpdf {underactuated|manipulation}.pdf
# or, this *should* work (but isn't):
# xpdf -remote foo "openFile(manipulation.pdf)" &  
# python3 htmlbook/make_pdf.py && xpdf -remote foo reload
# 
# Requires PrinceXML: https://www.princexml.com/latest/
# on 18.04 it was: sudo apt install prince

# Also requires puppeteer for offline rendering of mathjax, etc.
# 
# cd ~
# curl -sL https://deb.nodesource.com/setup_10.x -o nodesource_setup.sh
# sudo bash nodesource_setup.sh
# sudo apt install -y nodejs
# npm i puppeteer --save
# 
# Note: I had to manually npm i some of the missing deps on my first try to get # the installer to complete without errors.

# TODO
# - Remove prince watermark from first page?  (How much does it cost?)
# - Bibliography?
# MAYBE
# - prince-books?  https://www.princexml.com/doc/prince-for-books/
# - overflow-x warning is coming from highlight.js
# - font-size-adjust comes in through the rendering process.  but I could
#   investigate more.

import json
import os
import tempfile

def get_file_as_string(filename):
    f = open(filename, "r")
    s = f.read()
    f.close()
    return s

def write_file_as_string(filename, s):
    f = open(filename, "w")
    f.write(s)
    f.close()

def replace_string_before(s, before_str, with_str):
    r = with_str + s[s.find(before_str):]
    return r

def replace_string_after(s, after_str, with_str):
    loc = s.find(after_str) + len(after_str)
    r = s[:loc] + with_str
    return r

def replace_string_between(s, start_str, end_str, with_str):
    index = 0
    while s.find(start_str, index) > 0:
        start = s.find(start_str, index) + len(start_str)
        end = s.find(end_str, start)
        s = s[:start] + with_str + s[end:]
        index = start + len(with_str)
    return s


# root should be textbook repo root
root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
basename = os.path.basename(root) 

dir = tempfile.TemporaryDirectory()
os.symlink(os.path.join(root, 'htmlbook'), os.path.join(dir.name, 'htmlbook'))
os.symlink(os.path.join(root, 'data'), os.path.join(dir.name, 'data'))
os.symlink(os.path.join(root, 'figures'), os.path.join(dir.name, 'figures'))

chapters = json.load(open(os.path.join(root, "chapters.json")))
chapter_ids = ['index'] + chapters['chapter_ids']

prince_input_files = ''
for c in chapter_ids:
  filename = os.path.join(dir.name, c + ".html")
  s = get_file_as_string(os.path.join(root, c + '.html'))

  # Tweak html for rendering

  # Remove hypothesis
  s = s.replace('<script src="https://hypothes.is/embed.js" async></script>','')

  # links to data should point to online version
  s = s.replace('href="data/',f'href="http://{basename}.csail.mit.edu/data/')

  write_file_as_string(filename, s)
#  os.system(f"node {os.path.join(root, 'htmlbook/render_html.js')} http://{basename}.csail.mit.edu/{c}.html {filename}")
  os.system(f"node {os.path.join(root, 'htmlbook/render_html.js')} file://{filename} {filename}")
  prince_input_files += ' ' + filename
  
os.system(f"prince -s {os.path.join(root,'htmlbook/pdf.css')} {prince_input_files} -o {basename}.pdf")

dir.cleanup()
