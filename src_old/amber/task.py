""" This module provide task manager.

    The task in Amber is a execution thread.
    
    Copyright (C) 2008 ~ 2012. All Rights Reserved.
    The contents of this file are subject to the Mozilla Public License
    Version 1.1 (the "License"); you may not use this file except in
    compliance with the License. You may obtain a copy of the License at
    http://www.mozilla.org/MPL/

    Software distributed under the License is distributed on an "AS IS"
    basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
    License for the specific language governing rights and limitations
    under the License.

    Initial Developer: Lu Ken <bluewish.ken.lu@gmail.com>
"""   

__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__revision__ = "$Revision: 1 $"

#======================================  External Libraries ========================================
import wx
import threading
import sys
import wx.lib.newevent
#======================================  Internal Libraries ========================================
import lib.PyProgress
import image
import mainframe

#============================================== Code ===============================================
(TaskStartEventHandler, EVT_TASK_START) = wx.lib.newevent.NewEvent()
(TaskEndEventHandler, EVT_TASK_END) = wx.lib.newevent.NewEvent()

class Task(threading.Thread):
    """ Task concept is a executable functionality and inherited from threading.Thread 

    """
    def __init__(self, name=None, target=None, args=(), kwargs={}, verbose=True):
        """ Constructor function """
        threading.Thread.__init__(self, None, target, name, args, kwargs, verbose)
        self._stopflag = False
        self._progressLock = threading.Lock()
        self._progress = 0
        
    def Start(self):
        """ Wrapper for start function in threading.Thread """
        threading.Thread.start(self)

    def run(self):
        """ Implement the run interface provided by threading.Thread
            Amber Editor task should implement Run() instead of run().
            
        Before task.Run() is invoked, EVT_TASK_START_EVENT will send to task manager.
        And after task is finished, EVT_TASK_END_EVENT will sent to task manager.  
        """
        frame = wx.GetApp().GetTopWindow()
        wx.PostEvent(frame, TaskStartEventHandler(evtobj=self))
            
        self.Run()
        
        wx.PostEvent(frame, TaskEndEventHandler(evtobj=self))
            
    def Run(self):
        """ Need be implementation by real task. """
        
    def IsWantStop(self):
        """ This interface is used by checking whether user want to stop this task.
            
            Amber Editor's task should use it as much as possible, to make a non-block task.
        """
        return self._stopflag
        
    def IsAlive(self):
        """ Wrapper for threading.Thread's isAlive() interface """
        return self.isAlive()
        
    def Stop(self):
        """ Stop task. Just make a flag. """
        self._stopflag = True
        
    def ReportProgress(self, step=10, text=None):
        """ This interface is used by reporting task progress which will be checking by task
            manager.
        
            Amber Editor's task should use it as much as possible.
        """
        self._progressLock.acquire()
        self._progress += step
        if self._progress >= 100:
            self._progress = 0
        self._progressLock.release()
        
    def GetProgress(self):
        """ This interface is used to get current progress of current task """
        self._progressLock.acquire()
        progress = self._progress
        self._progressLock.release()
        return progress
    
class TaskManager(object):
    """ This class manage all task's status and will display current task's progress 
        in status bar.
        
        TODO: Task manager need a side view to display all active tasks.
    """
    
    def __init__(self):
        """ Constructor function """
        self._taskQueue     = []
        self._taskQueueLock = threading.Lock()
        self._progressDlg   = None
        self._progressTimer = None
        self._timer         = None
        self._activeTask    = None
        self._progressCount = 0

        # register task start/stop event with main frame.
        frame = wx.GetApp().GetTopWindow()
        frame.Bind(EVT_TASK_START, self.OnTaskStart)
        frame.Bind(EVT_TASK_END, self.OnTaskEnd)
        frame.Bind(wx.EVT_CLOSE, self.OnMainframeClose)
        
    def OnTaskStart(self, event):
        """ Callback function for EVT_TASK_START.
        
        When a new task is start, task object will be managed. and a progress dialog
        will be shown.
        """
        wx.GetApp().GetLogger().info("New task is started! %r" % event.evtobj)
        self._taskQueueLock.acquire()
        self._taskQueue.append(event.evtobj)
        self._taskQueueLock.release()
        wx.GetApp().GetTopWindow().PlayTextToasterBox('Task %s start!' % event.evtobj.getName())
        if self._activeTask == None:
            self._activeTask = event.evtobj
            self.ShowProgressDialog(True)
            frame = wx.GetApp().GetTopWindow()
        
    def OnTaskEnd(self, event):
        """ Callback function for EVT_TASK_END.
        
        When a new task is end, task object will be deleted. 
        """
        taskname = event.evtobj.getName()
        wx.GetApp().GetLogger().info("Task is ended! %r" % event.evtobj)
        if self._activeTask != None and self._activeTask == event.evtobj:
            self.ShowProgressDialog(False)
            self._activeTask = None
        self._taskQueueLock.acquire()
        self._taskQueue.remove(event.evtobj)
        self._taskQueueLock.release()
        wx.GetApp().GetTopWindow().PlayTextToasterBox('Task %s end!' % taskname)
    
    def ShowProgressDialog(self, isShow=True):
        """ Show a progress dialog for current task.
            
            A timer will be start to maintain/update gauge control in progress dialog.
        """
        if isShow and self._progressDlg == None:
            self._timer = TaskMonitorTimer(self)
            self._timer.Start(500)
            self._progressDlg = TaskProgressDialog(self, title="Task Progress ...")
        elif not isShow:
            self._timer.Stop()
            statusbar = wx.GetApp().GetTopWindow().GetStatusBar()
            statusbar.SetTaskProgress(0)
            statusbar.SetTaskMessage('')

            if self._progressDlg != None:
                self._progressDlg.Destroy()
                self._progressDlg = None
            
    def CheckTaskProgress(self):
        """ Check task progress """
        name  = self._activeTask.getName()
        count = self._activeTask.GetProgress()
        if count != 0:
            self._progressCount = count
        else:
            self._progressCount += 10
            if self._progressCount > 100:
                self._progressCount = 0
        if self._progressDlg != None:
            self._progressDlg.UpdatePulse('Task %s is in running!' % name)
        statusbar = wx.GetApp().GetTopWindow().GetStatusBar()
        statusbar.SetTaskProgress(self._progressCount)
        statusbar.SetTaskMessage('%s Running' % name)
        
    def OnBTStopActivateTask(self, event):
        """ Callback function for Cancel button click """
        self.StopActivteTask()
        
    def OnMainframeClose(self, event):
        """ If main frame quit, all tasks should be quit.
        
        Please notes, a block task will block main frame's quit!!! 
        """
        # stop any monitor timer
        if self._timer != None:
            self._timer.Stop()
            
        # stop all task
        for task in self._taskQueue:
            task.Stop()
        
        # show dialog to wait all task is closed
        dlg = TaskManagerQuitDialog(self)
        dlg.Show()
        
        while (len(self._taskQueue) != 0):
            wx.YieldIfNeeded()
            dlg.Pulse()
            import time
            time.sleep(0.1)
        dlg.Destroy()
         
        # skip EVT_CLOSE event to permit main frame close
        event.Skip()

    def StopActivteTask(self):
        if self._activeTask == None:
            return
            
        self._activeTask.Stop()
        
class TaskMonitorTimer(wx.Timer):
    def __init__(self, taskMgr):
        wx.Timer.__init__(self)
        self._taskMgr = taskMgr
        
    def Notify(self):
        self._taskMgr.CheckTaskProgress()      

# Some constants, taken straight from wx.ProgressDialog
Uncancelable = -1
Canceled = 0
Continue = 1
Finished = 2

# Margins between gauge and text/button
LAYOUT_MARGIN = 8
class TaskManagerQuitDialog(wx.Dialog):
    def __init__(self, taskmgr):
        self._taskMgr = taskmgr
        style = wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX 
        wx.Dialog.__init__(self, None, title="Task Manager", style=style)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, 'Waiting for quit all tasks!'), 0, wx.LEFT|wx.TOP, 2*LAYOUT_MARGIN)
        self._gauge = lib.PyProgress.ProgressGauge(self, -1, size=(-1, 30))
        sizer.Add(self._gauge, 0, wx.ALL|wx.EXPAND, 2*LAYOUT_MARGIN)
        self.SetSizerAndFit(sizer)
        self.SetSize((400, -1))
        self.Centre(wx.CENTER_FRAME|wx.BOTH)
       
    def Pulse(self):
        self._gauge.Update()
        
class TaskProgressDialog(wx.Dialog):
    """
    PyProgress is similar to wx.ProgressDialog in indeterminated mode, but with a
    different gauge appearance and a different spinning behavior. The moving gauge
    can be drawn with a single solid colour or with a shading gradient foreground.
    The gauge background colour is user customizable.
    The bar does not move always from the beginning to the end as in wx.ProgressDialog
    in indeterminated mode, but spins cyclically forward and backward.
    
    TODO: This class need cleanup
    """

    def __init__(self, taskMgr, parent=None, id=-1, title="", message="",
                 style=wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME, canAbort=True, canBack=True):
        """ Default class constructor. """
        self._taskMgr = taskMgr
        if not canAbort:
            dlgstyle = wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX 
        else:
            dlgstyle = wx.DEFAULT_DIALOG_STYLE 
        wx.Dialog.__init__(self, parent, id, title, style=dlgstyle)
        
        self._delay = 3
        self._hasAbortButton = False
        
        # we may disappear at any moment, let the others know about it
        self.SetExtraStyle(self.GetExtraStyle()|wx.WS_EX_TRANSIENT)
        if canAbort:
            style |= wx.PD_CAN_ABORT
        self._hasAbortButton = (style & wx.PD_CAN_ABORT)

        if wx.Platform == "__WXMSW__":
        # we have to remove the "Close" button from the title bar then as it is
        # confusing to have it - it doesn't work anyhow
        # FIXME: should probably have a (extended?) window style for this
            if not self._hasAbortButton:
                self.EnableClose(False)
    
        self._state = (self._hasAbortButton and [Continue] or [Uncancelable])[0]
        self._parentTop = wx.GetTopLevelParent(parent)

        dc = wx.ClientDC(self)
        dc.SetFont(wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT))
        widthText, dummy = dc.GetTextExtent(message)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._msg = wx.StaticText(self, wx.ID_ANY, message)
        sizer.Add(self._msg, 0, wx.LEFT|wx.TOP, 2*LAYOUT_MARGIN)

        sizeDlg = wx.Size()
        sizeLabel = self._msg.GetSize()
        sizeDlg.y = 2*LAYOUT_MARGIN + sizeLabel.y

        self._gauge = lib.PyProgress.ProgressGauge(self, -1)

        sizer.Add(self._gauge, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 2*LAYOUT_MARGIN)

        sizeGauge = self._gauge.GetSize()
        sizeDlg.y += 2*LAYOUT_MARGIN + sizeGauge.y
        
        # create the estimated/remaining/total time zones if requested
        self._elapsed = None
        self._display_estimated = self._last_timeupdate = self._break = 0
        self._ctdelay = 0

        label = None

        nTimeLabels = 0

        if style & wx.PD_ELAPSED_TIME:
        
            nTimeLabels += 1
            self._elapsed = self.CreateLabel("Elapsed time : ", sizer)
        
        if nTimeLabels > 0:

            label = wx.StaticText(self, -1, "")    
            # set it to the current time
            self._timeStart = wx.GetCurrentTime()
            sizeDlg.y += nTimeLabels*(label.GetSize().y + LAYOUT_MARGIN)
            label.Destroy()

        sizeDlgModified = False
        
        if wx.Platform == "__WXMSW__":
            sizerFlags = wx.ALIGN_RIGHT|wx.ALL
        else:
            sizerFlags = wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM|wx.TOP

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        if canBack:
            self._btnBackground = wx.Button(self, -1, "Run in Background")
            self._btnBackground.Bind(wx.EVT_BUTTON, self.OnRunInBackground)
            buttonSizer.Add(self._btnBackground, 0, sizerFlags, LAYOUT_MARGIN)
            
        if self._hasAbortButton:
            self._btnAbort = wx.Button(self, -1, "Cancel")
            self._btnAbort.Bind(wx.EVT_BUTTON, self.OnCancel)
            
            # Windows dialogs usually have buttons in the lower right corner
            buttonSizer.Add(self._btnAbort, 0, sizerFlags, LAYOUT_MARGIN)

            if not sizeDlgModified:
                sizeDlg.y += 2*LAYOUT_MARGIN + wx.Button.GetDefaultSize().y

        if self._hasAbortButton or canBack:
            sizer.Add(buttonSizer, 0, sizerFlags, LAYOUT_MARGIN )

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
        self._windowStyle = style
        
        self.SetSizerAndFit(sizer)
        #self.SetSizer(sizer)
    
        sizeDlg.y += 2*LAYOUT_MARGIN

        # try to make the dialog not square but rectangular of reasonable width
        sizeDlg.x = max(widthText, 4*sizeDlg.y/3)
        sizeDlg.x *= 3
        sizeDlg.x /= 2
        self.SetClientSize(sizeDlg)
        self.SetSize((400, -1))
        self.Centre(wx.CENTER_FRAME|wx.BOTH)

        
        if style & wx.PD_APP_MODAL:
            self._winDisabler = wx.WindowDisabler(self)
        else:
            if self._parentTop:
                self._parentTop.Disable()
            self._winDisabler = None
        
        self.ShowDialog()
        self.Enable()

        # this one can be initialized even if the others are unknown for now
        # NB: do it after calling Layout() to keep the labels correctly aligned
        if self._elapsed:
            self.SetTimeLabel(0, self._elapsed)

        if not wx.EventLoop().GetActive():
            self.evtloop = wx.EventLoop()
            wx.EventLoop.SetActive(self.evtloop)
        
        self.Update()
        self.SetFirstGradientColour(wx.Color(0, 128, 192))
        self.SetSecondGradientColour(wx.Color(0, 0, 128))
        self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        self.SetGaugeProportion(0.2)
        self.SetGaugeSteps(100)
        
        
    def CreateLabel(self, text, sizer):
        """ Creates the wx.StaticText that holds the elapsed time label. """

        locsizer = wx.BoxSizer(wx.HORIZONTAL)
        dummy = wx.StaticText(self, wx.ID_ANY, text)
        label = wx.StaticText(self, wx.ID_ANY, "unknown")

        if wx.Platform in ["__WXMSW__", "__WXMAC__"]:
            # label and time centered in one row
            locsizer.Add(dummy, 1, wx.ALIGN_LEFT)
            locsizer.Add(label, 1, wx.ALIGN_LEFT|wx.LEFT, LAYOUT_MARGIN)
            sizer.Add(locsizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, LAYOUT_MARGIN)
        else:
            # label and time to the right in one row
            sizer.Add(locsizer, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.TOP, LAYOUT_MARGIN)
            locsizer.Add(dummy)
            locsizer.Add(label, 0, wx.LEFT, LAYOUT_MARGIN)

        return label


    # ----------------------------------------------------------------------------
    # wxProgressDialog operations
    # ----------------------------------------------------------------------------

    def UpdatePulse(self, newmsg=""):
        """ Update the progress dialog with a (optionally) new message. """
       
        self._gauge.Update()
        
        if newmsg and newmsg != self._msg.GetLabel():
            self._msg.SetLabel(newmsg)
            wx.YieldIfNeeded() 
        
        if self._elapsed:        
            elapsed = wx.GetCurrentTime() - self._timeStart
            if self._last_timeupdate < elapsed:
                self._last_timeupdate = elapsed
                
            self.SetTimeLabel(elapsed, self._elapsed)                            

        if self._state == Finished:

            if not self._windowStyle & wx.PD_AUTO_HIDE:
                
                self.EnableClose()
                
                if newmsg == "":
                    # also provide the finishing message if the application didn't
                    self._msg.SetLabel("Done.")
                
                wx.YieldIfNeeded()
                self.ShowModal()
                return False
            
            else:
                # reenable other windows before hiding this one because otherwise
                # Windows wouldn't give the focus back to the window which had
                # been previously focused because it would still be disabled
                self.ReenableOtherWindows()
                self.Hide()
            
        # we have to yield because not only we want to update the display but
        # also to process the clicks on the cancel and skip buttons
        wx.YieldIfNeeded()

        return self._state != Canceled


    def GetFirstGradientColour(self):
        """ Returns the gauge first gradient colour. """

        return self._gauge.GetFirstGradientColour()


    def SetFirstGradientColour(self, colour):
        """ Sets the gauge first gradient colour. """

        self._gauge.SetFirstGradientColour(colour)


    def GetSecondGradientColour(self):
        """ Returns the gauge second gradient colour. """

        return self._gauge.GetSecondGradientColour()


    def SetSecondGradientColour(self, colour):
        """ Sets the gauge second gradient colour. """

        self._gauge.SetSecondGradientColour(colour)
        

    def GetGaugeBackground(self):
        """ Returns the gauge background colour. """

        return self._gauge.GetGaugeBackground()


    def SetGaugeBackground(self, colour):
        """ Sets the gauge background colour. """

        self._gauge.SetGaugeBackground(colour)


    def SetGaugeSteps(self, steps):
        """
        Sets the number of steps the gauge performs before switching from
        forward to backward (or vice-versa) movement.
        """
        
        self._gauge.SetGaugeSteps(steps)


    def GetGaugeSteps(self):
        """
        Returns the number of steps the gauge performs before switching from
        forward to backward (or vice-versa) movement.
        """

        return self._gauge.GetGaugeSteps()


    def GetGaugeProportion(self):
        """
        Returns the relative proportion between the sliding bar and the
        whole gauge.
        """
        
        return self._gauge.GetGaugeProportion()

    
    def SetGaugeProportion(self, proportion):
        """
        Sets the relative proportion between the sliding bar and the
        whole gauge.
        """

        self._gauge.SetGaugeProportion(proportion)


    def ShowDialog(self, show=True):
        """ Show the dialog. """

        # reenable other windows before hiding this one because otherwise
        # Windows wouldn't give the focus back to the window which had
        # been previously focused because it would still be disabled
        if not show:
            self.ReenableOtherWindows()

        return self.Show()


    # ----------------------------------------------------------------------------
    # event handlers
    # ----------------------------------------------------------------------------

    def OnCancel(self, event):
        """ Handles the wx.EVT_BUTTON event for the Cancel button. """

        if self._state == Finished:
        
            # this means that the count down is already finished and we're being
            # shown as a modal dialog - so just let the default handler do the job
            event.Skip()
        
        else:
        
            # request to cancel was received, the next time Update() is called we
            # will handle it
            self._state = Canceled

            # update the buttons state immediately so that the user knows that the
            # request has been noticed
            self.DisableAbort()

            # save the time when the dialog was stopped
            self._timeStop = wx.GetCurrentTime()

        self.ReenableOtherWindows()
        self._taskMgr.StopActivteTask()

    def OnDestroy(self, event):
        """ Handles the wx.EVT_WINDOW_DESTROY event for PyProgress. """
        self.ReenableOtherWindows()
        event.Skip()

    def OnRunInBackground(self, event):
        self.Close()
        
    def OnClose(self, event):
        self.ReenableOtherWindows()
        event.Skip()

        """ Handles the wx.EVT_CLOSE event for PyProgress. """

        """
        if self._state == Uncancelable:
        
            # can't close this dialog
            event.Veto()
        
        elif self._state == Finished:

            # let the default handler close the window as we already terminated
            self.Hide()
            event.Skip()
        
        else:
        
            # next Update() will notice it
            self._state = Canceled
            self.DisableAbort()
    
            self._timeStop = wx.GetCurrentTime()
        """

    def ReenableOtherWindows(self):
        """ Re-enables the other windows if using wx.WindowDisabler. """

        if self._windowStyle & wx.PD_APP_MODAL:
            if hasattr(self, "_winDisabler"):
                del self._winDisabler
            wx.GetApp().GetTopWindow().Enable()
        else:
        
            if self._parentTop:
                self._parentTop.Enable()
        
    def SetTimeLabel(self, val, label=None):
        """ Sets the elapsed time label. """

        if label:
        
            hours = val/3600
            minutes = (val%3600)/60
            seconds = val%60
            strs = ("%lu:%02lu:%02lu")%(hours, minutes, seconds)

            if strs != label.GetLabel():
                label.SetLabel(strs)

    
    def EnableAbort(self, enable=True):
        """ Enables or disables the Cancel button. """

        if self._hasAbortButton:
            if self._btnAbort:
                self._btnAbort.Enable(enable)


    def EnableClose(self, enable=True):
        """ Enables or disables the Close button. """
        
        if self._hasAbortButton:
            if self._btnAbort:        
                self._btnAbort.Enable(enable)
                self._btnAbort.SetLabel("Close")
                self._btnAbort.Bind(wx.EVT_BUTTON, self.OnClose)


    def DisableAbort(self):
        """ Disables the Cancel button. """

        self.EnableAbort(False)              
        
