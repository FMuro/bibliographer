# from https://github.com/ssp/arXivToBibTeX/blob/master/lookup.py

import cgi
import re
import urllib
from urllib.parse import urlparse
from urllib.request import urlopen
from xml.etree import ElementTree
import xml.etree
import os
import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

authors = ["0000-0001-8457-9889", "0000-0002-2520-2755", "0000-0002-9786-0650", "0000-0003-2865-0219", "0000-0002-8806-3561", "0000-0003-3946-792X"]#, "0000-0002-5537-3299"]
arXivURLs = ["https://arxiv.org/a/"+author+".atom" for author in authors]

IDCleanerRE = re.compile(r"[^0-9]*([0-9]*)\.?([0-9]*)")


def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K


def cmp(a, b):
    return (a > b) - (a < b)


def comparePaperDictionaries(firstPaper, secondPaper):
    """
            Compare paper dictionaries.
            Earlier years are smaller.
            Smaller IDs within a year are smaller.
    """
    comparisonResult = 0
    if "year" in firstPaper and "ID" in firstPaper and "year" in secondPaper and "ID" in secondPaper:
        comparisonResult = cmp(firstPaper["year"], secondPaper["year"])

        if comparisonResult == 0:
            cleanedFirstID = int(IDCleanerRE.sub(r"\1\2", firstPaper["ID"]))
            cleanedSecondID = int(IDCleanerRE.sub(r"\1\2", secondPaper["ID"]))
            comparisonResult = cmp(cleanedFirstID, cleanedSecondID)

    return comparisonResult


def markupForBibTeXItem(myDict, format):
    """
            Input: dictionary with publication data.
            Output: BibTeX record for the preprint.
    """
    bibTeXID = myDict["ID"]
    bibTeXAuthors = " and ".join(myDict["authors"])
    bibTeXTitle = myDict["title"]
    bibTeXYear = myDict["year"]

    hasDOI = myDict["DOI"] != None and len(myDict["DOI"]) > 0
    hasJournal = myDict["journal"] != None
    isPublished = hasJournal or hasDOI

    publicationType = ("@online" if format ==
                       "biblatex" else "@misc") if not isPublished else "@article"

    eprintPrefix = "" if format == "biblatex" else "arXiv:"
    bibTeXEntry = ["\n\n", publicationType, "{", bibTeXID, ",\nAuthor = {", bibTeXAuthors, "},\nTitle = {",
                   bibTeXTitle, "},\nYear = {", bibTeXYear, "},\nEprint = {", eprintPrefix, bibTeXID, "},\n"]
    if format == "biblatex":
        bibTeXEntry += ["Eprinttype = {arXiv},\n"]
    if hasJournal:
        bibTeXEntry += ["Howpublished = {", myDict["journal"], "},\n"]
    if hasDOI:
        bibTeXEntry += ["Doi = {", " ".join(myDict["DOI"]), "},\n"]
    bibTeXEntry += ["}"]
    result = "".join(bibTeXEntry)
    return result


def bibTeXMarkup(items, format):
    """
            Input: List of publication dictionaries.
            Output: Array of strings containing HTML markup with a heading and a textarea full of BibTeX records.
    """
    markup = []
    if len(items) > 0:
        itemmarkup = []
        for item in items:
            bibtexmarkup = markupForBibTeXItem(item, format)
            itemmarkup += [bibtexmarkup]
        markup += ["".join(itemmarkup)]
    return "".join(markup)


for arXivURL in arXivURLs:
    download = urllib.request.urlopen(arXivURL)
    download.encoding = "UTF-8"
    downloadedData = download.read()
    if downloadedData == None:
        printHtml("The arXiv data could not be retrieved.")
    else:
        f = open("arxiv.bib", "w")
        publications = []
        feed = xml.etree.ElementTree.fromstring(downloadedData)

        """	Check for an error by looking at the title of the first paper: errors are marked by 'Error', empty feeds don't have a title """
        firstTitle = feed.find(
            "{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}title")
        if firstTitle == None or firstTitle.text == "Error":
            printHtml(extraInfo())
            printHtml("The arXiv did not return any results for the ORCID: " +
                    author + " you entered. Any chance there may be a typo in there?")
        else:
            """ We got data and no error: Process it. """
            papersiterator = feed.iter("{http://www.w3.org/2005/Atom}entry")
            for paper in papersiterator:
                titleElement = paper.find("{http://www.w3.org/2005/Atom}title")
                if titleElement == None:
                    continue
                theTitle = re.sub(r"\s*\n\s*", r" ", titleElement.text)
                authors = paper.iter("{http://www.w3.org/2005/Atom}author")
                theAuthors = []
                for author in authors:
                    name = author.find("{http://www.w3.org/2005/Atom}name").text
                    theAuthors += [name]
                theAbstract = paper.find(
                    "{http://www.w3.org/2005/Atom}summary").text.strip()

                links = paper.iter("{http://www.w3.org/2005/Atom}link")
                thePDF = ""
                theLink = ""
                for link in links:
                    attributes = link.attrib
                    if "href" in attributes:
                        linktarget = attributes["href"]
                        linktype = attributes["type"] if "type" in attributes else None
                        linktitle = attributes["title"] if "title" in attributes else None
                    if linktype == "application/pdf":
                        thePDF = linktarget
                    elif linktype == "text/html":
                        theLink = linktarget
                splitLink = theLink.split("/abs/")
                theID = splitLink[-1].split('v')[0]
                theLink = splitLink[0] + "/abs/" + theID

                theYear = paper.find(
                    "{http://www.w3.org/2005/Atom}published").text.split('-')[0]

                theDOIs = []
                DOIs = paper.iter("{http://arxiv.org/schemas/atom}doi")
                for DOI in DOIs:
                    theDOIs += [DOI.text]

                journal = paper.find("{http://arxiv.org/schemas/atom}journal_ref")
                theJournal = None
                if journal != None:
                    theJournal = journal.text

                publicationDict = dict({
                    "ID": theID,
                    "authors": theAuthors,
                    "title": theTitle,
                    "abstract": theAbstract,
                    "year": theYear,
                    "PDF": thePDF,
                    "link": theLink,
                    "DOI": theDOIs,
                    "journal": theJournal})
                publications += [publicationDict]

            preprintIDs = []
            preprints = []
            publishedIDs = []
            published = []

            publications.sort(key=cmp_to_key(
                comparePaperDictionaries), reverse=True)

            for publication in publications:
                # LATER SKIP PUBLISHED PAPERS
                if publication["journal"] != None:
                    published += [publication]
                    publishedIDs += [publication["ID"]]
                else:
                    preprints += [publication]
                    preprintIDs += [publication["ID"]]

            f.write("% BIBTEX\n\n")
            if len(preprints) > 0:
                f.write("% PREPRINTS")
                f.write(str(bibTeXMarkup(preprints, "bibtex")))
            if len(published) > 0:
                f.write("\n\n")
                f.write("% PUBLISHED")
                f.write(str(bibTeXMarkup(published, "bibtex")))

            f.write("\n\n\n")

            f.write("% BIBLATEX\n\n")
            if len(preprints) > 0:
                f.write("% PREPRINTS")
                f.write(str(bibTeXMarkup(preprints, "biblatex")))
            if len(published) > 0:
                f.write("\n\n")
                f.write("% PUBLISHED")
                f.write(str(bibTeXMarkup(published, "biblatex")))
            f.write("\n\n")
