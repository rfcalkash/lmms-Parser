from bs4 import BeautifulSoup
import urllib.request
from os import path, remove
import re
import csv
import sys
import subprocess
from pathlib import Path
from shutil import copyfile
import glob


class MMPFile:    
    def __init__(self):
        self.link = ''
        self.name = ''
        self.extension = ''
        self.genre = ''
        self.popularity=0
        self.rating=0
        self.srcFilename = ''
        self.renderedFilename = ''
  
def link_has_title(tag):
    return tag.name=="a" and tag.has_attr('title')

def link_has_subcategory(tag):
    subcategoryPattern = re.compile(".*\&subcategory\=.*", re.IGNORECASE)
    return tag.name=="a" and subcategoryPattern.match(tag['href'])

def downloadData(url):
    return urllib.request.urlopen(url).read().decode()

def downloadFile(url, filename):
    file = open(filename, "x+b")
    file.write(urllib.request.urlopen(url).read())
    file.close()

def runProcess(process, arguments, output = ''):
    res = subprocess.run([process, arguments], capture_output=True)
    if(res.returncode!=0):
        print("ERROR", res.stderr)
    elif(len(output)>0):
        file = open(output, "x+b")
        file.write(res.stdout)
        file.close()
    return res==0

if(len(sys.argv)<3):
    print("Pass target folder and path to lmms.exe as argument")
    exit
folder = sys.argv[1]
Path(folder+'\data').mkdir(parents=True, exist_ok=True)
Path(folder+'\\tmp').mkdir(parents=True, exist_ok=True)
tmpFolder = folder+'\\tmp'
lmms = sys.argv[2]
counter = 1
with open(folder+'\metadata.csv', mode='w', newline='') as meta_file:
    meta_writer = csv.writer(meta_file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    meta_writer.writerow(["link","name","extension","genre","popularity","rating","src","render"])
    soup = BeautifulSoup(downloadData('https://lmms.io/lsp/?action=browse&category=Projects&sort=rating'), 'html5lib')
    for f in soup.find_all("tr", class_="file"):
        try:
            file_=MMPFile()
            for link in f.find_all(link_has_title):
                file_.link=link.get("href")
                fullname=path.splitext(link['title'])
                file_.name=fullname[0]
                file_.extension=fullname[1]
            for link in f.find_all(link_has_subcategory):
                file_.genre=link.string.strip()
            popularityTags=f.find_all("span", class_="fas fa-download")
            if(len(popularityTags)>0):
                file_.popularity = int(popularityTags[0].next.string.strip())
            file_.rating = len(f.find_all("span", class_="fas fa-star"))
            link = 'https://lmms.io/lsp/download_file.php?'+file_.link[17:]+'&name=temp'+file_.extension
            downloadFile(link, tmpFolder +'\\temp'+file_.extension)
            if(file_.extension[-1]!="z" or runProcess(lmms,'dump '+tmpFolder+'\\temp'+file_.extension, tmpFolder+"\\temp.mmp")):
                copyfile(tmpFolder+"\\temp.mmp", folder+'\data\\'+str(counter)+'.mmp')
                if(runProcess(lmms,'render '+tmpFolder+'\\temp.mmp --format wav --output '+ folder+'\data\\'+str(counter)+'.wav')):
                    file_.srcFilename=folder+'\data\\'+str(counter)+'.mmp'
                    file_.renderedFilename =folder+'\data\\'+str(counter)+'.wav'
                    meta_writer.writerow([file_.link,file_.name,file_.extension,file_.genre,file_.popularity,file_.rating, file_.srcFilename, file_.renderedFilename])
        except Exception:
            print("ERROR on processing", f)
        finally:
            files = glob.glob('tmpFolder\*')
            for f in files:
                remove(f)
    #for fileData in parser.files:
    #    meta_writer.writerow([fileData.link,fileData.name,fileData.extension,fileData.genre,fileData.popularity,fileData.rating])
    #currentPage = 0
