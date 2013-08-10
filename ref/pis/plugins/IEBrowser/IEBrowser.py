"""
 _template_attribute_ must be defined in template python code as
 [description, filter, dir, ext, docTypeName, viewTypeName, docType, viewType, flag, icon]
"""

_plugin_module_info_ = [{"name":"IEBrowser",
                         "author":"ken",
                         "version":"1.0",
                         "minversion":"0.0.1",
                         "description":"web browser base IE",
                         "class":"IEBrowserPlugin"},
                         {"name":"IEBrowserToolbar",
                         "author":"ken",
                         "version":"1.0",
                         "minversion":"0.0.1",
                         "description":"Tool bar for web browser base IE",
                         "class":"IEBrowserToolBarPlugin"}]

import wx.lib.docview as docview
import core.plugin
import wx
import wx.lib.iewin as  iewin
import wx.lib.throbber as  throb
import throbImages 
import wx.lib.platebtn as platebtn

class IEBrowserPlugin(core.plugin.ITemplatePlugin):
    def IGetDescription(self):
        return 'URL'
    
    def IGetDocumentClass(self):
        return WebDocument
    
    def IGetViewClass(self):
        return WebView
    
    def IGetFilter(self):
        #return '*.h;*.c;*.cpp;*.hpp;*.txt;*.text;*.bat;*.sh;*.py;*.pyw;*.bak;*.cfg;*.ini;*.inf;*.dsc;*.dec;*.lua;*.uni'
        return '*.html;*.htm;*.doc'
    
    def IGetDir(self):
        """Interface for child class provide document's default dir
        """
        return 'html'
    
    def IGetExt(self):
        """Interface for child class provide document's default postfix of file name
        """
        return 'html'
    
    def IGetFlag(self):
        """Interface for child class provide template's flag: TEMPLATE_VISIBLE/TEMPLATE_INVISIBLE
        TEMPLATE_NO_CREATE/DEFAULT_TEMPLATE_FLAGS
        """
        return wx.lib.docview.TEMPLATE_VISIBLE
    
    def IGetIcon(self):
        """Interface for child class provide template's icon"""
        return getIEIcon()
    
class IEBrowserToolBarPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return IEBrowserToolBarService
    
    def IGetName(self):
        return "IE tool bar"
    
class IEBrowserToolBarService(core.service.PISService):
    IE_NEW_ID = wx.NewId()
    
    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        wx.EVT_MENU(frame, self.IE_NEW_ID, self.OnNewIE)
        
    def GetCustomizeToolBars(self):
        toolbar = wx.ToolBar(wx.GetApp().GetTopWindow(),
                              -1, wx.DefaultPosition, wx.DefaultSize,
                             wx.TB_FLAT | wx.TB_NODIVIDER)
        toolbar.AddLabelTool(self.IE_NEW_ID,
                             'New IE Windows',
                             getIEBitmap(),
                             shortHelp = "New IE Windows", 
                             longHelp =  "New IE Windows")
        toolbar.Realize()
        return [toolbar]

    def OnNewIE(self, event):
        docmgr   = wx.GetApp().GetDocumentManager()
        template = docmgr.FindTemplateForPath('*.html')
        doc      = template.CreateDocument('', docview.DOC_NEW)
        
class WebDocument(docview.Document):
    def OnNewDocument(self):
        self.SetTitle('about:blank')
        self.SetFilename('about:blank', notifyViews = True)
        
class WebView(docview.View):
    
    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self.current   = 'www.sina.com.cn'
        self.log       = wx.GetApp().GetLogger()
        self._lastText = None
        self._stack    = []
        self._template = None
        self._progress = 0
        self._inClosing = False
        
    def OnCreate(self, doc, flags):
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.frame = frame
        frame.Freeze()
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        art = wx.GetApp().GetArtProvider()
        btn = platebtn.PlateButton(frame, -1, bmp=getNavLeftBitmap(), style=platebtn.PB_STYLE_SQUARE | platebtn.PB_STYLE_GRADIENT)
        frame.Bind(wx.EVT_BUTTON, self.OnPrevPageButton, btn)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        btn = platebtn.PlateButton(frame, -1, bmp=getNavRightBitmap(), style=platebtn.PB_STYLE_SQUARE | platebtn.PB_STYLE_GRADIENT)
        frame.Bind(wx.EVT_BUTTON, self.OnNextPageButton, btn)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        btn = platebtn.PlateButton(frame, -1, bmp=getStopBitmap(), style=platebtn.PB_STYLE_SQUARE | platebtn.PB_STYLE_GRADIENT)        
        frame.Bind(wx.EVT_BUTTON, self.OnStopButton, btn)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        #btn = wx.BitmapButton(frame, -1, bitmap=art.GetBitmap(wx.ART_FIND), size=(32,32))#, style=wx.BU_EXACTFIT)
        #frame.Bind(wx.EVT_BUTTON, self.OnSearchPageButton, btn)
        #btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        btn = platebtn.PlateButton(frame, -1, bmp=getRefreshBitmap(), style=platebtn.PB_STYLE_SQUARE | platebtn.PB_STYLE_GRADIENT)        
        frame.Bind(wx.EVT_BUTTON, self.OnRefreshPageButton, btn)
        btnSizer.Add(btn, 0, wx.EXPAND|wx.ALL, 2)

        areaSizer = wx.BoxSizer(wx.VERTICAL)
        locSizer  = wx.BoxSizer(wx.HORIZONTAL)
        
        txt = wx.StaticText(frame, -1, "Location:")
        locSizer.Add(txt, 0, wx.CENTER|wx.ALL, 2)
        
        self.location = wx.ComboBox(
                            frame, -1, "", style=wx.CB_DROPDOWN|wx.PROCESS_ENTER
                            )
        frame.Bind(wx.EVT_COMBOBOX, self.OnLocationSelect, self.location)
        self.location.Bind(wx.EVT_KEY_UP, self.OnLocationKey)
        self.location.Bind(wx.EVT_CHAR, self.IgnoreReturn)
        self.location.Bind(wx.EVT_UPDATE_UI, self.ProcessUpdateUIEvent)
        locSizer.Add(self.location, 1, wx.CENTER|wx.ALL, 2)
        images = [throbImages.catalog[i].GetImage().Scale(16, 16)
                  for i in throbImages.index
                  if i not in ['eclouds', 'logo']]
        bitmaps = [BitmapFromImage(img) for img in images]        
        self._throb = throb.Throbber(frame, -1, bitmaps, frameDelay = 0.1, size=(16,16))
        locSizer.Add(self._throb, 0, wx.CENTER|wx.ALL, 2)
        areaSizer.Add(locSizer, 1, wx.EXPAND|wx.ALL, 2)
        #self._gauge = wx.Gauge(frame, -1, size=(20, 1), style=wx.GA_SMOOTH)
        #areaSizer.Add(self._gauge, 0, wx.EXPAND, 2)
        
        btnSizer.Add(areaSizer, 1, wx.EXPAND)
        sizer.Add(btnSizer, 0, wx.EXPAND)
                                
        self.ie = iewin.IEHtmlWindow(frame, -1)
        sizer.Add(self.ie, 1, wx.EXPAND)
        
        frame.SetSizer(sizer)
        frame.Layout()
        frame.Thaw()
        self.current = self.GetDocument().GetFilename()
        if len(self.current) == 0:
            self.current = 'about:blank'
        self.ie.LoadUrl(self.current)
        self.location.Append(self.current)        

        self.ie.AddEventSink(self)
        self._throb.Start()
        return True
        
    def OnLocationSelect(self, evt):
        url = self.location.GetStringSelection()
        self.log.info('OnLocationSelect: %s\n' % url)
        self.ie.Navigate(url)

    def OnLocationKey(self, evt):
        if evt.GetKeyCode() == wx.WXK_RETURN:
            URL = self.location.GetValue()
            self.location.Append(URL)
            self.ie.Navigate(URL)
            self.ie.SetFocus()
        else:
            evt.Skip()

    def IgnoreReturn(self, evt):
        if evt.GetKeyCode() != wx.WXK_RETURN:
            evt.Skip()

    def OnPrevPageButton(self, event):
        self.ie.GoBack()

    def OnNextPageButton(self, event):
        self.ie.GoForward()

    def OnStopButton(self, evt):
        self.ie.Stop()

    def OnSearchPageButton(self, evt):
        self.ie.GoSearch()

    def OnRefreshPageButton(self, evt):
        self.ie.Refresh(iewin.REFRESH_COMPLETELY)

    def logEvt(self, evt):
        pst = ""
        for name in evt.paramList:
            pst += " %s:%s " % (name, repr(getattr(evt, name)))
        self.log.info('%s: %s' % (evt.eventName, pst))

    def OnNewWindow2(self, evt):
        #self.logEvt(evt)
        # Veto the new window.  Cancel is defined as an "out" param
        # for this event.  See iewin.py
        #evt.Cancel = True   
        while len(self._stack) !=0:
            url = self._stack.pop()
            if url.startswith(u'http://'):
                openurl = url
                self.GetTemplate().CreateDocument(openurl, wx.lib.docview.DOC_NEW)
                break
        del self._stack[:]
        evt.Cancel = True   
        
    def GetTemplate(self):
        if self._template == None:
            for temp in wx.GetApp().GetDocumentManager().GetTemplates():
                if temp.GetDocumentType() == WebDocument:
                    self._template = temp
                    break
        
        return self._template
            
    def OnProgressChange(self, evt):
        #self.logEvt(evt)

        curr = getattr(evt, evt.paramList[0])
        max  = getattr(evt, evt.paramList[1])
        if curr in [0, -1] or max == 0:
            #self._gauge.SetValue(0)
            return
        self._progress = curr
            
        num = curr * 100 / max
        #self._throb.Start()
        #self._gauge.Pulse()
        #self._gauge.SetValue(num)
                   
    def DocumentComplete(self, this, pDisp, URL):
        #self.location.Enable(True)
        #self.logEvt(evt)
        #self.current = URL[0]
        #self.location.SetValue(self.current)
        pass
    
    def TitleChange(self, this, text):
        appname = wx.GetApp().GetAppName()
        frame = wx.GetApp().GetTopWindow()
        frame.SetTitle(appname + ' - ' + text)
        self.frame.SetTitle(text)

    def StatusTextChange(self, this, text):
        frame = wx.GetApp().GetTopWindow()
        frame.SetStatusText(text)  
        self._lastText = text
        if len(self._stack) > 10:
            self._stack.pop(0)
        self._stack.append(text)
        
    def NavigateComplete2(self, this, pDisp, URL):
        self.location.Enable(True)
        self.current = URL[0]
        self.location.SetValue(self.current)
        
    def ProgressChange(self, this, curr, max):
        if curr in [0, -1] or max == 0:
            #self._gauge.SetValue(0)
            return
        self._progress = curr
            
        num = curr * 100 / max
        #self._gauge.SetValue(num)
        
    def NewWindow3(self, this, ppDisp, cancel, dwFlags, bstrUrlContext, bstrUrl):
        self.GetTemplate().CreateDocument(bstrUrl, wx.lib.docview.DOC_NEW)
        cancel[0] = True
        
    def ProcessEvent(self, evt):
        id = evt.GetId()
        if id == wx.ID_COPY:
            tObj = wx.TextDataObject()
            tObj.SetText(self.ie.GetStringSelection())
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(tObj)
            wx.TheClipboard.Close() 
            return True
        return False
                    
    def ProcessUpdateUIEvent(self, evt):      
        if self._inClosing:
            # if in closing, must eat all update event to do not 
            # dispatch.
            return True
            
        id = evt.GetId()
        if id == wx.ID_COPY or\
           id == wx.ID_CUT  or\
           id == wx.ID_PASTE:
            #if not self.ie.GetStringSelection():
            evt.Enable(False)
            return True
        elif id == self.location.GetId():
            #if self._gauge.GetValue() == 0:
            #    evt.Enable(True)
            #else:
            #    evt.Enable(False)
            return True
        return True
    
    def OnClose(self, deleteWindow):
        self._inClosing = True
        return docview.View.OnClose(self, deleteWindow)
        
#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

NavLeft = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABHNCSVQICAgIfAhkiAAAAeJJ"
    "REFUKJGFk89LVFEUxz/3vflFU4sirFXQJpmFKIgG6Qw2TERRzKaNu4gIF21a+Q+0qEUU5iqF"
    "YFBEg2CSkiGcEEISTLNaVBKZIFPWVNPQjM19955W2phv6MAX7rn3fvkezvkelOPSCIXCqozk"
    "hqTRu0OD+Lj6TiaejrK88oaXL+bF748veentMxmfydB8OIYVS7lc9hXYQc4/fyiP56eIdyRp"
    "aW7FWIPgK4xSjruVjObuSOV3hWPtcSK7woScEGOPMpS+lxAErTVaa4zxuN2fUUo5LssfXsnk"
    "3H12R/dwKn6WX6bMj40v7Is0EVBBrJgtiFgGhwfpjZ8nMLs0LeNPRmiJtdIeO8pPr0hpo4hn"
    "NWvl93hWo00Nz2o8W+PI3jaM8UAgYMUSDIZQCoxoPKMx1kPbGl4dafNsxOBpA0Cgu+2EWnw9"
    "K1MLD1j/9plEx3Fs0ONrtcDB6CFCbhhj68s2WGNBZHvDBu5dlUq1SiqRwg0rIm6UuxNDrK8V"
    "EbF/R+S4XDjZt50MMJy9KSufVkh2JTmwv4lrN65z6cxl31EF/r24mL6isvkxmcxl6ersxhiD"
    "CCR6Uuq/JgFIJ3tVuvMc0zN5XNeFBibZobwZPfHTCqD/Vl8jg9Fwo+qxuDDnu1l/AN7g9Qo1"
    "DIEvAAAAAElFTkSuQmCC")
getNavLeftData = NavLeft.GetData
getNavLeftImage = NavLeft.GetImage
getNavLeftBitmap = NavLeft.GetBitmap
getNavLeftIcon = NavLeft.GetIcon

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

NavRight = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABHNCSVQICAgIfAhkiAAAAfdJ"
    "REFUKJGFk89L03EYx1/ffbfhj35JFMgS6aBGW1hU0K+54DsZmTACow6ewqDD/oAuZcciwlOX"
    "KDwYuxRIaIjOlPxxiKCiDkst1mgOigj069za9/OjQyRNv6M3PJfn4fXw8H7zYHhMNlcy9Ui7"
    "9TeXBxdl8xnuPu7X6aV32m3+V66w3+cn1HqI5NQg4/PDVRe4wgCh1nZi4S5m3k/x8NmA6wLj"
    "9tAN7TN9aDRaA2hq62qIWz2sOzbrhSITc2OUSkVu9Q0YFfCdoZv6Ss81pJJorVBaorSiJAss"
    "2xl2+HdRa25ncn6c3HKOzsNddIbjBoBHKolUknwhw9e1T2RXF/mykia3+hlH/uJbIcePUh7r"
    "VJRQMMjw3BMePL2nAbyOKKO0xJFlpBII5SBUGakchHL+6Qk0Cq/HxLZtFtIftFdIgdKKxvrm"
    "jZOVlhSdNbIrH2mo2UOduZOZ19MsLixxtOkkLU0HQGuM6/cTWkqJEAIhBAC79zZwubsXu/yT"
    "ckky8nyUYqGAFewmHr+4YZpheExmX05WRJGcHSTRlyD/fZmRsVG2mfWcO36BcCRa6bbhMbfk"
    "d7X/ko5FY6SmUxxsbOdIyzE6zlaCAF638JVSTLxIEWmzaA7s50yHtQWsCu8LBLDazuP3+zlx"
    "OuIK/rm7yse8ffPqv5/1G3jA6tbRQfV1AAAAAElFTkSuQmCC")
getNavRightData = NavRight.GetData
getNavRightImage = NavRight.GetImage
getNavRightBitmap = NavRight.GetBitmap
getNavRightIcon = NavRight.GetIcon

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

Refresh = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABHNCSVQICAgIfAhkiAAAAn9J"
    "REFUKJGFkmtozXEYxz+///kfZo4dbMYs05jLMpeQconkFiFJLnmhvEJJUbwRI+SNQkiUViQp"
    "lJLcY8NyP7McmYzjcnbWjM2Oc87/9//9Hi+G3H3refHU8+l5nm9flBPgx7r5KCb7Tz2WdXtv"
    "yebDd0U5AaoevpQfZ7ZX3GnvlRPgm46cjUh9PMmo0t70LcjB8y11sWaqa+MMKQ6zcv4ItWbX"
    "NUm8/8SJHXPVd/jYuYjU1rfyMemTTGmys4IsmlbKgKKu1L9r4cSFJwQCAYaW5HP59lNO7pyn"
    "nG9bqyIJ8nOE8SVwtHy6GlvicPpKlOjLZkKhbJbMGs6CqWWU9i/AGgPw89m/6syVGnlQ95mZ"
    "EweTaDGkMpa8Li4Hj1/i9K6Fyl27u1ICjsJYQRuLMRatNel0mkjdB1w3i7aUpi0FKc/SOcti"
    "jAbADTiK1YtHo43gGyGjLTXP4tytjVG+YpIqP3RbkmlLMi18zljC2Q6+l26HjRU8Y2lqNXha"
    "cPC5H21gz7opasO+ShlYXEAwGCQ/LHi+JaMFa/x22PMt2gdHgSCAoi3ls/HAdXmT+Mi5eBNe"
    "RuNpje+lsNagvvrsWiv4xmIFOriKjOdQXNidF68bqdgyR/3VTcD1tMed2rfcirxlTFkh/Yry"
    "GTawN00taZZvvShHNk1XAJdu3JOa+iQNzYYZY/KYOn6YUsvKz0uPbtkM6iVcj2aYNq6U7uEc"
    "jAhPnsdpTMRp+9SCti6eLyyc0I35sycrALeoV2e2rWpvKs7clItVUfoW5tIzN0RuuCOhTn2I"
    "xSyvXseZMTL0HfxjSKqrq+Xqw/fEmjxaW1N0DAoFXWHH+qW//f/PhP1PXwDuxzgVPFm8IgAA"
    "AABJRU5ErkJggg==")
getRefreshData = Refresh.GetData
getRefreshImage = Refresh.GetImage
getRefreshBitmap = Refresh.GetBitmap
getRefreshIcon = Refresh.GetIcon

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

Stop = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABHNCSVQICAgIfAhkiAAAAn9J"
    "REFUKJFlkkloEwEUhr8ZJzPdYmvaJtWSqLi01oNb3Kq0daWI4IJ4KV4FL4KiuOBF8CCKBwUv"
    "infF7aCg2CIFKRUFqVq6iAGx0SatWUqTmcykM8+DKE394R0e/B+P996vKOo8Zmv85jmxR0Yo"
    "ZizEddEMF21pGF/XKRY2r1dme5W/cOLBbck/f4axqI75a5rRA1VI0cL+kWT6cwxzLIm2eyfL"
    "Tl5VSuDEg9tidb+idt8OjGANkonjZX+AmUVBgfIF2GmLRO8oSlsrTaevK//g2LFOqT+8Dzeb"
    "pBAbBc/FqPUj5hR2YgKKBYyGetTgCsZfvkcuXWP1lg5F+3nronjxOEZjA5mBfkKX7wOQvHQE"
    "HIuGW2/+rHV8LTVLIviXRUg/vQeA5owME+hohXyq5HChK49KerwZZDJGZUuUVM9bhgY/iFpM"
    "5dGDAbzsOHqojonLXcxV4sRGfJqFl/6OUV+NO2WRy5lo4rmIY4GZAXMKcUwQ+W8qXhG0Spin"
    "4QGOY6P6KhTs+E8QoRAfI3jhLpJPlVToRjeO50dpaMKezOH5y0AEVVsaJvdxBAw/FC0k9wvJ"
    "/SJ5fj/JM53/enxlqOF15AZjOOEwPt3486ovBzZLcG8ULx2nEB8DdwZdLyBFG8fRwVeOsXwV"
    "aqiJ2MMXpI6fpfPgUUUD0He0MdHTR7BtFTUbqpHxIbx0EiorKF+0EnVxlELGI/akh0x0E1WB"
    "2tJ4frlxSrzePioijVS1RDDqqxHVh5M2yQ1/IzH6lWw0StnOw7R17FFKYIDB/tfiPb6DfBtj"
    "ZtrGFWGmqgw7EqbQfgh/oI7t7btKsz1XnwbeST5v4jgOALqus3VbhzLX9xvIUigfa4tJjgAA"
    "AABJRU5ErkJggg==")
getStopData = Stop.GetData
getStopImage = Stop.GetImage
getStopBitmap = Stop.GetBitmap
getStopIcon = Stop.GetIcon

from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib


def getIEData():
    return zlib.decompress(
'x\xda\x01\x0b\x03\xf4\xfc\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\
\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x00\x03sBIT\x08\
\x08\x08\xdb\xe1O\xe0\x00\x00\x02\xc3IDAT(\x91u\xd1\xc9O\x13a\x1c\xc6\xf1\
\xdf\xcc\xbc\xf3\xbeS\xda\xe9\xb4\x85\xb6\xb4 \xa0\r\x86\x82D\xc4\xe0\x82$F\
\x0e\xc4\xc4\xf5\xc0\xc5\x837O\x1e\xfc\x13\xbc\x99x1\xc6\x18/F\xa3A\x0fj4\
\xb8\x11\xf5\x80\xa2F\x13\x81`HY\x02\x8amYm;\x9dB\xa7\xcb\xec\xaf\x17\x12\
\x13\x13\x9f\xf3\xf7sz\x98\xc4b\x1e\xfe?\xcdr\xd6\xb7J\x13\x06\x96\xa8S\xabm\
\xf6\xec\x8a\xa2\x7f\x8ad6\x9f/kk\x85\xb2f\xd8I\x87oj\xdbijDT3aI\x9c\xa7\x82\
\xb4.\xff\x05iYY\xb4)\n\x87\nRM\x16\x98\xc5\x15\x1ds\xa8\xb8\xbc\x1a^J\xec\
\x8d\xb7tE\xfc\x8b\xab%\xc3\xa9l\x83dNQ\xbc5 \xf8\x90i\xafe\xf3iG\xca\xe7l\
\xbd\xac\xf3L [\x7f\xb82\xfdm\xb9P\xe9\x8b5\x04\xdc\x81m\xb0A\xa9\xac:]T\x9d\
\xa2\xfcl\xda\xc8|\x1fc\xbca\xe4\xaf\xd7,\xea \x9cj:d\'F:\xc2\x92\xcb/"\x00x\
:\x9f\xf4Fw\x9c\x96\xd0\x98N\xdf\xfcT\xe5\xfb\xd7\xf1f\x86\x04Bj\xdbq\xdc\
\xd2EM\x9b\xa2\x9a\xf9"\x9a[Z\x0e\x06$T\xachjI\x1f\x94\xd0\x03Y\x9b\x04\x9f2\
;ik\xd6\xb3;\xb7\x00\xe0\xea\xe3\xd1Dn\x01j\xe3V\xd5\x16Z:?|y\xd1\x1c\xf63\
\xef\'RAI\x1c\xcd\x94_1\x81\xdcoMWu\xa6\xaa3\x94\xe5(\x08\xd42\xc0\x8dXV\xe0\
\x89@\xec\xc2\xa3\xcb\xe7\x07O\xa3\xa0$N\xa7V\x87\xb9XA\xd1\xf5\xa2\xce\xaf\
\xe4\xfe\x9e\x00\x00P2\x00\x0c\x80"\x00kj\xe9\xac\x82\x0c\xd3z[\xf2T1\xd8e\
\x93jvic\xc6\x1a\x7fR\x17\x89\x12\x9e\x98\xac\xdb ~\x07\x00\x11\xecs9l\xa4\
\x11\x13\x82&\xd7\xd54\x89:U\x1b\x01\x0b\x0c\xc7\xc5\x0e\x80\x92|p\xe5"\x00\
\x8c\xce\xe6\x86\xe6\xad\x9a]-\xddq\xc1\xb3\xb20>\xfc\xac#\xd6\x88\xc6\xf2\
\xcc\xd6\xd6\x86\xb5\xf2Kl?h\x9a\x8c\xedb\x99#\x17\x06o~\xe5xBb{\xfc\x1d\xde\
\xf6\x18\xd9\x8d\xb4\xa1\xbb\xb7#\xd1\x88\x8b\xf0H\xc1\xa2\xf7\xc7\xa8<\xfdi\
K7\xa5\xd8>"\xb8\x1c\x8b\x92\xce>,r\xc1\x10\xdf\x1a\xe6j+\x85\x877\xae\x99\
\xaar\xb4\xf7T}\x9d\x9f\xe9\x7f*\xf7\x97\xe7\xf66\x07_~\x9c\xf8<\xb3\xe1\x8e\
\xf7\xbaB\r\xee:\x8f\xe8\xc1>Z\x90\x13\xe3?\xc6\xdeaj\r\x9c=9\xb0\xbf\xdb\'\
\x8a\xa8\xc9)\xa6\x94\xca\x99\xc3\xa1K\xe7Nl\x8e\xcc\xe6SK\xd9\xa9\xe7YMe\
\xc1\xe1\xac*\xc6|k[\xeb\xb1\xdeC\x9d;\x9b\xbdn\x0f\x8fX\xe6\xde\xdb\xb9\xd7\
kP1\xed:\x1e\xe2\x1e\xb3\xa7\xd9\xbf\x9e\x91\xd7220\x94\x10\xdc\x18\x0e\xd4\
\x8a\x1e\x97K\x100\xc1\x08\x01\x03\x7f\x00\xe3{O^\x99W\x19\x12\x00\x00\x00\
\x00IEND\xaeB`\x82X)n|' )

def getIEBitmap():
    return BitmapFromImage(getIEImage())

def getIEImage():
    stream = cStringIO.StringIO(getIEData())
    return ImageFromStream(stream)

def getIEIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getIEBitmap())
    return icon


    