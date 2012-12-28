#!/usr/bin/python
# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser # Parser HTML
import urllib  # HTTP Request and Download HTML pages
import pprint  # printer custom object
import os      # used to create directory in filesystem
import re      # regular expression
import sys
import urllib2
from os.path import basename
from urlparse import urlsplit
from subprocess import call

list_chapter = []
guide_title = []
path_pdf =  os.path.expanduser('~') + "/Documents/Guide_HTML"

class ParseIndex(HTMLParser):
    def __init__(self):

        HTMLParser.__init__(self)
        self.title = False
        self.header = False
        self.prendi_titolo = False

    def handle_starttag(self, tag, attrs):
        self.title = False

        if tag == "a":
            if attrs[0][0] == 'id' and "lesson" in attrs[0][1]:
               self.title = True
               #tmp = attrs[0][1].replace("lesson", "")
               list_chapter.append({'lezione': '', 'link':attrs[1][1]})
        
        if tag == "div" and attrs[0] == ('class','guide-title'):
                self.header = True

        if tag == "h1" and self.header == True:
                self.prendi_titolo = True
                self.header = False

    def handle_data(self, data):
        if self.title == True:
            chars = ['\n','\t','\r',' ']
            data = re.sub("[%s]" % "". join(chars), ' ' ,data)
            list_chapter[-1]['lezione'] = "%s" % data.decode('utf-8')
            self.title = False
        if self.prendi_titolo == True:
            guide_title.append(data)
            print data
            self.prendi_titolo = False

# -------------------------------------------------------------- #

inner_tex = []

class ParseSigleLesson(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.code = False
    #def handle_starttag(self, tag, attrs):
        
    def handle_starttag(self, tag, attrs):
        if tag == "p":
            inner_tex.append("\paragraph{} ")
        if tag == "ul" or tag == "ol":
            inner_tex.append("\\begin{itemize} ")
        if tag == "li":
            inner_tex.append("\item ")
        if tag == "strong":
            inner_tex.append("\\textbf{")
        if tag == "div" and (attrs[0] == ('class','boxcode') or attrs[0]== ('class','console')):
            inner_tex.append("\lstset{language=C} \n \\begin{lstlisting}")
            self.code = True
        if tag == "img":
            d = dict(attrs)
            filename = download_img(d["src"])
            inner_tex.append("\\begin{wrapfigure} \n \\begin{center} \n \includegraphics[scale=0.5]{img/%s} \n \end{center} \n \end{wrapfigure}" % filename)
    def handle_data(self, data):
        inner_tex.append(data)

    def handle_endtag(self, tag):
        if tag == "ul" or tag== "ol":
            inner_tex.append("\\end{itemize}")
        if tag == "strong":
            inner_tex.append("}")
        if tag == "div" and self.code == True:
            self.code = False
            inner_tex.append("\end{lstlisting}")

def download_img(imgUrl):
    imgData = urllib2.urlopen(imgUrl).read()
    fileName = "img/%s" % basename(urlsplit(imgUrl)[2])
    if not os.path.exists("img"):
            os.makedirs("img")

    output = open(fileName,'wb')
    output.write(imgData)
    output.close()
    return basename(urlsplit(imgUrl)[2])

############### MAIN PROGRAM #####################

guide_URI = ""#"http://www.html.it/guide/guida-ruby-on-rails-2/"

if len(sys.argv) != 3:
    sys.exit("Error args. Use --help")
    
if sys.argv[1] == '--guide':   
    guide_URI = sys.argv[2]
elif sys.argv[1] == '--help':    
    print "\n******************** HELP ********************"
    print "--help            This Help"
    print "--guide           insert link of guide"
    print "\nThanks, Gianluca Tursi ;)"
    sys.exit(0)
else:
    sys.exit("Error args. Use --help")    
    
#if len(sys.argv) > 3:
#   sys.exit("USAGE: ./run -h")
# Dowload della prima pagina [link differente agli altri]
print "*********   The program take a while **********"

f = urllib.urlopen(guide_URI)
s = f.read()
f.close()

titolo = s[s.find("<div class=\"article-header-item\">"):s.find("<div class=\"meta-test\">")]
titolo = titolo[titolo.find("<h1>")+4:titolo.find("</h1>")]

end = s.find("<div id=\"sidebar\">")
start = s.find("<div class=\"entry guide-item\">")
s = s[start:end]

parser = ParseIndex()   
parser.feed(s)
parser.close()

#print list_chapter

latex = "\documentclass{report} \n \usepackage[utf8]{inputenc} \n \usepackage{listings} \usepackage{graphicx} \\title{" + titolo +"} \\author{Gianluca Tursi} \date{} \maketitle \\tableofcontents \\begin{document}"
parser = ParseSigleLesson()

for lesson in list_chapter:

    inner_tex = []
    chapter_title = lesson['lezione']#re.sub('[\']',"\\' ", lesson['lezione'])
    latex = latex + "\chapter{%s}" % chapter_title
    f = urllib.urlopen(lesson['link'])
    s = f.read()
    f.close()

    start = s.find("<div class=\"entry guide-item content-text\">")
    end = s.find("<div class=\"page-slider\">")
    s = s[start:end]

    parser.feed(s)
    parser.close()

    for elem in inner_tex:
        latex = latex + elem.decode("utf-8")

latex = re.sub('[_]','\_',latex)
latex = re.sub('[$]','\$',latex)
latex = re.sub('[«]','<<', latex)
latex = re.sub('[»]','>>', latex)
latex = re.sub('[#]','\#', latex)
latex = re.sub('[&]','\&', latex)

latex = latex + "\end{document}"

file_tex = open('guida.tex', 'w')
file_tex.write(latex.encode("utf-8"))
file_tex.close()

call(["/usr/texbin/pdflatex", "-interaction=nonstopmode","guida.tex"])

#call(["open", "guida.pdf"])

if not os.path.exists(path_pdf):
    os.makedirs(path_pdf)

titolo = re.sub("[\t]", "", titolo)
titolo = re.sub("[\n]", "", titolo)
titolo = re.sub("[\r]", "", titolo)

call(["cp", "guida.pdf", path_pdf + "//" + titolo + ".pdf"])
call(["open", path_pdf + "//" + titolo + ".pdf"])
#print latex.encode("utf-8")
print "The guide is saved in " + path_pdf + "//" + titolo + ".pdf"
