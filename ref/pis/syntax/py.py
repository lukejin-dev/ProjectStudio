import wx
import wx.stc
import string
import re
import os

_name   = 'py'
_filter = 'py,pyw'

_lex = wx.stc.STC_LEX_PYTHON

_stc_styles = {'STC_P_DEFAULT':   {'fore': '#000000'},
               'STC_P_COMMENTLINE': {'fore': '#007F00', 'italic': True },
               'STC_P_COMMENTBLOCK': {'fore': '#007F00', 'italic': True },
               'STC_P_DEFNAME': {'fore': '#000000', 'bold':True, 'italic': True },
               'STC_P_TRIPLEDOUBLE': {'fore': '#770077', 'italic': True },
               'STC_P_TRIPLE': {'fore': '#770077', 'italic': True },
               'STC_P_NUMBER': {'fore': '#007F7F'},
               'STC_P_STRING': {'fore': '#7F007F'},
               'STC_P_CHARACTER': {'fore': '#7F007F'},
               'STC_P_WORD': {'fore': '#00007F', 'bold':True},
               'STC_P_OPERATOR': {},
               'STC_P_IDENTIFIER': {},
               'STC_P_STRINGEOL': {'fore': '#000000', 'back':'#E0C0E0', 'eol':True},
               'STC_P_DECORATOR': {'fore': '#808080', 'back':'#E0C0E0', 'eol':True},
               'STC_P_WORD2': {'fore': '#808080', 'back':'#E0C0E0', 'eol':True},
               'STC_P_CLASSNAME': {'fore': '#808080', 'back':'#E0C0E0', 'eol':True},
              }

_properties = {'fold':'1',
               'styling.within.preprocessor':'1',
               'fold.comment':'1',
               'fold.compact':'1',
               'fold.at.else':'1',
               'lexer.cpp.allow.dollars':'1'}
                             
import keyword              
_keywords = string.join(keyword.kwlist)  

def _OutlineCallback(view, tree):
    doc   = view.GetDocument()
    fname = doc.GetFilename()
    tree.DeleteAllItems()
    rootItem  = tree.AddRoot(os.path.basename(fname))
    text      = view.GetValue()
        
    CLASS_PATTERN = 'class[ \t]+\w+.*?:'
    DEF_PATTERN = 'def[ \t]+\w+\(.*?\)'
    classPat = re.compile(CLASS_PATTERN, re.M|re.S)
    defPat= re.compile(DEF_PATTERN, re.M|re.S)
    pattern = re.compile('^[ \t]*((' + CLASS_PATTERN + ')|('+ DEF_PATTERN +'.*?:)).*?$', re.M|re.S)

    iter = pattern.finditer(text)
    indentStack = [(0, rootItem)]
    for pattern in iter:
        line = pattern.string[pattern.start(0):pattern.end(0)]
        classLine = classPat.search(line)
        if classLine:
            indent = classLine.start(0)
            itemStr = classLine.string[classLine.start(0):classLine.end(0)-1]  # don't take the closing ':'
            itemStr = itemStr.replace("\n", "").replace("\r", "").replace(",\\", ",").replace("  ", "")  # remove line continuations and spaces from outline view
        else:
            defLine = defPat.search(line)
            if defLine:
                indent = defLine.start(0)
                itemStr = defLine.string[defLine.start(0):defLine.end(0)]
                itemStr = itemStr.replace("\n", "").replace("\r", "").replace(",\\", ",").replace("  ", "")  # remove line continuations and spaces from outline view

        if indent == 0:
            parentItem = rootItem
        else:
            lastItem = indentStack.pop()
            while lastItem[0] >= indent:
                lastItem = indentStack.pop()
            indentStack.append(lastItem)
            parentItem = lastItem[1]

        item = tree.AppendItem(parentItem, itemStr)
        tree.SetPyData(item, [pattern.end(0), pattern.start(0) + indent])
        indentStack.append((indent, item))

def _SelectCallback(view, pydata):
    line = view.LineFromPosition(pydata[0])
    view.GotoLine(line)
    wx.CallAfter(view.SetFocus)
    
_outline_callbacks = {'InitTree': _OutlineCallback,
                      'SelectAction':_SelectCallback}
                        