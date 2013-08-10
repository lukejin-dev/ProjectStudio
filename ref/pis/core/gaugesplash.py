#-----------------------------------------------------------------------------
# Name:        gaugesplash.py
# Purpose:     splash screen with gauge to show progress
#
# Author:      Rob McMullen
#
# Created:     2007
# RCS-ID:      $Id: $
# Copyright:   (c) 2007 Rob McMullen
# License:     wxWidgets
#-----------------------------------------------------------------------------
"""Splash screen with progress bar

A replacement for the standard wx.SplashScreen that adds a text label
and progress bar to update the user on the progress loading the
application.

I looked at both Andrea Gavana's AdvancedSplash, here:

http://xoomer.alice.it/infinity77/main/AdvancedSplash.html

and Ryaan Booysen's AboutBoxSplash

http://boa-constructor.cvs.sourceforge.net/boa-constructor/boa/About.py?revision=1.38&view=markup

for inspiration and code.
"""

import os

import wx
from wx.lib.statbmp import *


class GaugeSplash(wx.Frame):
    """Placeholder for a gauge-bar splash screen."""
    def __init__(self, bmp, timeout=5000):
        wx.Frame.__init__(self, None, style=wx.FRAME_NO_TASKBAR)
        self.border = 2

        self.SetBackgroundColour(wx.WHITE)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.bmp = GenStaticBitmap(self, -1, bmp)
        sizer.Add(self.bmp, 0, wx.EXPAND)

        self.label = wx.StaticText(self, -1, "Loading...")
        self.label.SetBackgroundColour(wx.WHITE)
        sizer.Add(self.label, 0, flag=wx.EXPAND|wx.ALL, border=self.border)

        self.progressHeight = 12
        self.gauge = wx.Gauge(self, -1,
              range=100, size = (-1, self.progressHeight),
              style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.gauge.SetBackgroundColour(wx.WHITE)
        sizer.Add(self.gauge, 0, flag=wx.EXPAND|wx.ALL, border=self.border)

        self.CenterOnScreen()

        self.timeout = timeout
        self._splashtimer = wx.PyTimer(self.OnNotify)
        self._splashtimer.Start(self.timeout)
        self.count = 0

        self.visible = True

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.bmp.Layout()
        self.label.Layout()
        self.gauge.Layout()
        self.CenterOnScreen()
        self.Layout()
        self.Update()
        wx.SafeYield()
        
    def OnNotify(self):
        """ Handles The Timer Expiration, And Calls The Close() Method. """
        # If we've taken too long and the object is dead, just return
        if not self:
            return

        # If we still have ticks remaining, don't close the window
        if self.count < self.gauge.GetRange():
            self._splashtimer.Start(self.timeout/10)
        else:
            self.Close()

    def setTicks(self, count):
        """Set the total number of ticks that will be contained in the
        progress bar.
        """
        self.gauge.SetRange(count)

    def tick(self, text):
        """Advance the progress bar by one tick and update the label.
        """
        self.count += 1
        self.label.SetLabel(text)
        self.gauge.SetValue(self.count)
        self.gauge.Update()
        wx.SafeYield()
