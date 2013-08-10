import wx
import wx.grid
import os.path
import version
_ = wx.GetTranslation

licenseData = [  # add licenses for base IDE features
    ("Python 2.5", "Python Software Foundation License", "http://www.python.org/2.5/license.html"),
    ("wxPython 2.8.0", "wxWidgets 2 - LGPL", "http://wxwidgets.org/about/newlicen.htm"),
    ("wxWidgets", "wxWindows Library License 3", "http://www.wxwidgets.org/manuals/2.8.0/wx_wxlicense.html"),
    ("pysvn", "Apache License, Version 2.0", "http://pysvn.tigris.org/"),
]

if wx.Platform == '__WXMSW__':  # add Windows only licenses
    licenseData += [("pywin32", "Python Software Foundation License", "http://sourceforge.net/projects/pywin32/")]

class AboutDialog(wx.Dialog):

    def __init__(self, parent):
        """
        Initializes the about dialog.
        """
        wx.Dialog.__init__(self, parent, -1, _("About ") + wx.GetApp().GetAppName(), style = wx.DEFAULT_DIALOG_STYLE)

        nb = wx.Notebook(self, -1)

        aboutPage = wx.Panel(nb, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)

        #splash_bmp = wx.Bitmap("Resources/Logo.bmp", wx.BITMAP_TYPE_ANY)

        # find version number from
        
        #versionFilepath = 'Version.txt'
        #if os.path.exists(versionFilepath):
        #    versionfile = open(versionFilepath, 'r')
        #    versionLines = versionfile.readlines()
        #    versionfile.close()
        #    version = "".join(versionLines)
        #else:
        #    version = _("Version Unknown - %s not found" % versionFilepath)
        
        ver = _('Version %s' % version.VERSION) 
        #image = wx.StaticBitmap(aboutPage, -1, splash_bmp, (0,0), (splash_bmp.GetWidth(), splash_bmp.GetHeight()))
        #sizer.Add(image, 0, wx.ALIGN_CENTER|wx.ALL, 0)
        sizer.Add(wx.StaticText(aboutPage, -1, wx.GetApp().GetAppName() + _("\n%s\n\nCopyright (c) 2008-2010 Intel Incorporated and Contributors.  All rights reserved.") % ver), 0, wx.ALIGN_LEFT|wx.ALL, 10)
        #sizer.Add(wx.StaticText(aboutPage, -1, _("http://edk2.tianocore.org")), 0, wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, 10)
        aboutPage.SetSizer(sizer)
        nb.AddPage(aboutPage, _("Copyright"))

        licensePage = wx.Panel(nb, -1)
        grid = wx.grid.Grid(licensePage, -1)
        grid.CreateGrid(len(licenseData), 2)

        dc = wx.ClientDC(grid)
        dc.SetFont(grid.GetLabelFont())
        grid.SetColLabelValue(0, _("License"))
        grid.SetColLabelValue(1, _("URL"))
        w, h1 = dc.GetTextExtent(_("License"))
        w, h2 = dc.GetTextExtent(_("URL"))
        maxHeight = max(h1, h2)
        grid.SetColLabelSize(maxHeight + 6)  # add a 6 pixel margin

        maxW = 0
        for row, data in enumerate(licenseData):
            package = data[0]
            license = data[1]
            url = data[2]
            if package:
                grid.SetRowLabelValue(row, package)
                w, h = dc.GetTextExtent(package)
                if w > maxW:
                    maxW = w
            if license:
                grid.SetCellValue(row, 0, license)
            if url:
                grid.SetCellValue(row, 1, url)

        grid.EnableEditing(False)
        grid.EnableDragGridSize(False)
        grid.EnableDragColSize(False)
        grid.EnableDragRowSize(False)
        grid.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        grid.SetLabelBackgroundColour(wx.WHITE)
        grid.AutoSizeColumn(0)
        grid.AutoSizeColumn(1)
        grid.SetRowLabelSize(maxW + 10)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND|wx.ALL, 10)
        licensePage.SetSizer(sizer)
        nb.AddPage(licensePage, _("Licenses"))

        creditsPage = wx.Panel(nb, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(creditsPage, -1, _("PIS Development Team:\n\nLu Ken")), 0, wx.ALIGN_LEFT|wx.ALL, 10)
        creditsPage.SetSizer(sizer)
        nb.AddPage(creditsPage, _("Credits"))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        btn = wx.Button(self, wx.ID_OK)
        sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        grid.ForceRefresh()  # wxBug: Get rid of unnecessary scrollbars


