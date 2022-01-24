from html.parser import HTMLParser
from os import link, popen
from typing import List
from enum import Enum
import urllib.request
import os.path
import re
import csv
import sys

class MMPFile:    
    def __init__(self):
        self.link = ''
        self.name = ''
        self.extension = ''
        self.genre = ''
        self.popularity=0
        self.rating=0
  

class LMMSParser(HTMLParser):    

    class CurrentParsingData(Enum):
        NONE = 0
        GENRE = 1
        POPULARITY = 2
        PAGES = 3

    def __init__(self, *, convert_charrefs: bool = ...):
        super().__init__(convert_charrefs=convert_charrefs)
        self.currentFile = MMPFile()
        self.collectingFile = False
        self.files = list()
        self.parsingData = self.CurrentParsingData.NONE
        self.totalPages=0

    def handle_starttag(self, tag, attrs):
        if(tag=='tr'):
            for attr in attrs:
                if(attr[0]=="class" and attr[1]=="file"):
                    self.collectingFile = True
        elif(self.collectingFile):            
            extensionPattern = re.compile(".*\.mmpz?", re.IGNORECASE)
            subcategoryPattern = re.compile(".*\&subcategory\=.*", re.IGNORECASE)
            if(tag=='a'):
                href = ''
                title = ''
                for attr in attrs:
                    if(attr[0]=="href"):
                        href = attr[1]
                    if(attr[0]=="title"):
                        title = attr[1]
                if(len(href)>0 and extensionPattern.match(title)):
                    self.currentFile.link=href
                    self.currentFile.name=title
                    self.currentFile.extension=os.path.splitext(title)[1]
                elif(subcategoryPattern.match(href)):
                    self.parsingData=self.CurrentParsingData.GENRE
            elif(tag=='svg'):
                for attr in attrs:
                    if(attr[0]=="data-icon" and attr[1]=="star"):
                        for attr2 in attrs:
                            if(attr2[0]=="data-prefix" and attr2[1]=="fas"):
                                self.currentFile.rating=self.currentFile.rating+1
                    elif(attr[0]=="data-icon" and attr[1]=="download"):
                        self.parsingData=self.CurrentParsingData.POPULARITY

    def handle_endtag(self, tag):
        if(tag=='tr'):
            self.files.append(self.currentFile)
            self.collectingFile = False
            print("file added:", self.currentFile.name)
            self.currentFile = MMPFile()


    def handle_data(self, data: str):
        if(self.collectingFile):
            if(self.parsingData==self.CurrentParsingData.GENRE):
                self.currentFile.genre=data.strip()
                self.parsingData=self.CurrentParsingData.NONE
            elif(self.parsingData==self.CurrentParsingData.POPULARITY):
                self.currentFile.popularity=int(data.strip())
                self.parsingData=self.CurrentParsingData.NONE
        elif(self.parsingData==self.CurrentParsingData.PAGES):
            v = int(data.strip())
            if(v>self.totalPages):
                self.totalPages=v


def downloadData(url):
    return urllib.request.urlopen(url).read().decode()

if(len(sys.argv)<2):
    print("Pass target folder as argument")
    exit
folder = sys.argv[1]
with open(folder+'\metadata.csv', mode='w') as meta_file:
    meta_writer = csv.writer(meta_file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    meta_writer.writerow(["link","name","extension","genre","popularity","rating"])
    parser = LMMSParser()
    parser.feed(downloadData('https://lmms.io/lsp/?action=browse&category=Projects&sort=rating'))
    for fileData in parser.files:
        meta_writer.writerow([fileData.link,fileData.name,fileData.extension,fileData.genre,fileData.popularity,fileData.rating])
    currentPage = 0
