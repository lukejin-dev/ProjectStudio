import debug
import config
import os
import wx

from util.constant import *

DEFAULT_STYLE = {'font': 'Courier New',
                 'fore': '#000000',
                 'back': '#F6F6F6',
                 'size': 10,
                 'bold': False,
                 'italic': False,
                 'eol': False,
                 'underline': False
                }
ID_SYNTAX_MANAGE = wx.NewId()
                
class SyntaxMgr(object):
    _instance = None
    _dict     = {'default': {'filter': '*', 
                             'styles': {'STC_STYLE_DEFAULT':{},
                                        'STC_STYLE_LINENUMBER':{'back': '#C0C0C0',
                                                                'size': 8},
                                        'STC_STYLE_CONTROLCHAR':{},
                                        'STC_STYLE_BRACELIGHT':{'back': '#0000FF',
                                                                'bold': True},
                                        'STC_STYLE_BRACEBAD':{'back': '#FF0000',
                                                              'bold': True},
                                        'STC_STYLE_INDENTGUIDE':{'fore': '#838383'}
                                       }
                            }
                }
                
    def __new__(cls, *args, **kwargs):
        """Maintain only a single instance of this object
        @return: instance of this class

        """
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        object.__init__(self)
        self._config = config.StyleConfig()
        self._logger = debug.GetSyntaxLogger()
        
    def GetConfig(self):
        return self._config
        
    def Initialize(self, path):
        """Load all syntax from specific path"""
        appPath = wx.GetApp().GetAppLocation()
        if appPath == None:
            wx.MessageBox("Fail to load syntax, app location is wrong!")
            return
        if not os.path.exists(os.path.join(appPath, path)):
            self._logger.error('The path %s does not exist!' % path)
            return

        oldpath = os.getcwd()    
        os.chdir(appPath)
            
        modules = self.SearchModules(path)
        for module in modules:
            name   = self.GetAttr(module, '_name')
            filter = self.GetAttr(module, '_filter')
            if name == None or filter == None: continue
            if self._dict.has_key(name):
                self._logger.warning('Syntax %s has been in database!' % name)
                continue
            self._dict[name] = {}
            self._dict[name]['filter'] = filter
            self._dict[name]['styles'] = {}
            
            styles = self.GetAttr(module, '_stc_styles')
            for key in styles.keys():
                self._dict[name]['styles'][key] = styles[key]
            
            lex = self.GetAttr(module, '_lex')
            if lex == None:
                lex = wx.stc.STC_LEX_NULL
            self._dict[name]['lex'] = lex
            
            keywors = self.GetAttr(module, '_keywords')
            if keywors != None:
                self._dict[name]['keywords'] = keywors
                   
            properties = self.GetAttr(module, '_properties')
            if properties != None:
                self._dict[name]['properties'] = properties
                
            outline = self.GetAttr(module, '_outline_callbacks')
            if outline != None:
                self._dict[name]['outlinecallbacks'] = outline
                
        # Register the style editor menu
        frame = wx.GetApp().GetTopWindow()
        menubar = frame.GetMenuBar()
        toolmenu = menubar.GetMenu(menubar.FindMenu('Document'))
        item = wx.MenuItem(toolmenu, ID_SYNTAX_MANAGE, 'Style Editor', 'Edit existing style')
        item.SetBitmap(wx.GetApp().GetArtProvider().GetBitmap(wx.ART_REPORT_VIEW))
        wx.EVT_MENU(frame, ID_SYNTAX_MANAGE, self.OnStyleEditor)
        toolmenu.InsertItem(0, item)
        toolmenu.InsertSeparator(1)  
                       
        os.chdir(oldpath)
        
    def GetAttr(self, mod, name):
        if not hasattr(mod, name):
            self._logger.error('Can not find %s in module %s!' % (name, mod.__name__))
            return None
        return getattr(mod, name)
        
    def GetDict(self):
        return self._dict
        
    def SearchModules(self, path):
        modules = []
        names   = []
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                if dir.lower() in IGNORE_DIRS:
                    dirs.remove(dir) 
            for file in files:
                f, ext = os.path.splitext(file)
                if ext != '.py' and ext != '.pyc': continue
                
                # skip init file.
                if file.find('__init__') != -1: continue
                
                mPath = os.path.join(root, file).replace(os.sep, '.')

                # names list to avoid duplicate import module for .py/.pyc module.
                if mPath[:mPath.rfind('.')].lower() in names:
                    continue
                names.append(mPath[:mPath.rfind('.')].lower())
                
                # skip file postfix name
                mPath = mPath.split('.')[:-1]
                try:
                    mod   = __import__('.'.join(mPath))
                except ImportError, e:
                    self._logger.exception('Fail to import module %s' % mPath)
                    continue
                except:
                    self._logger.exception('Fail to import module %s' % mPath)
                    continue
                
                for comp in mPath[1:]:
                    try:
                        mod = getattr(mod, comp)
                    except:
                        self._logger.error('Fail to get attribute %s' % comp)
                        break
                
                if mod not in modules:
                    modules.append(mod)
        return modules        
    
    def GetLanguageFromExt(self, ext=None):
        if ext == None:
            return 'default'
        for key in self._dict.keys():
            supports = self._dict[key]['filter'].split(',')
            if ext in supports:
                return key
        return 'default'
    
    def GetStyleDict(self, lan):
        return self._dict[lan]['styles']
        
    def OnStyleEditor(self, event):
        pass
        
class Style:
    def __init__(self, ext=None):
        self._lan = 'default'
        self._mgr = SyntaxMgr()
        self._lan = self._mgr.GetLanguageFromExt(ext)
        self._config = self._mgr.GetConfig()
    
    def IsDefault(self):
        return self._lan == 'default'
        
    def GetDefaultFont(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('font', DEFAULT_STYLE['font'])
        
    def GetDefaultBackColor(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('back', DEFAULT_STYLE['back'])
        
    def GetDefaultForeColor(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('fore', DEFAULT_STYLE['fore'])
        
    def GetDefaultSize(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('size', DEFAULT_STYLE['size'])
        
    def GetStyleNames(self):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict.keys()
        
    def GetDefaultBold(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('bold', False)

    def GetDefaultItalic(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('italic', False)

    def GetDefaultEol(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('eol', False)
            
    def GetDefaultUnderline(self, styname):
        dict = self._mgr.GetStyleDict(self._lan)
        return dict[styname].get('underline', False)
    
    def GetLex(self):
        dict = self._mgr.GetDict()
        return dict[self._lan].get('lex', wx.stc.STC_LEX_NULL)
             
    def GetKeywords(self):
        dict = self._mgr.GetDict()
        return dict[self._lan].get('keywords', ())
        
    def GetProperties(self):
        dict = self._mgr.GetDict()
        return dict[self._lan].get('properties', {})
        
    def GetOutlineCallback(self):
        dict = self._mgr.GetDict()
        return dict[self._lan].get('outlinecallbacks', None)
        
    def GetStyle(self, styname):
        prefix  = self._lan + '_' + styname + '_'
        font    = self._config.Get(prefix + 'font', self.GetDefaultFont(styname))
        back    = self._config.Get(prefix + 'back', self.GetDefaultBackColor(styname))
        fore    = self._config.Get(prefix + 'fore', self.GetDefaultForeColor(styname))
        size    = self._config.GetInt(prefix + 'size', self.GetDefaultSize(styname))
        bold    = self._config.GetBoolean(prefix + 'bold', self.GetDefaultBold(styname))
        italic    = self._config.GetBoolean(prefix + 'italic', self.GetDefaultItalic(styname))
        eol       = self._config.GetBoolean(prefix + 'eol', self.GetDefaultEol(styname))
        underline = self._config.GetBoolean(prefix + 'underline', self.GetDefaultUnderline(styname))
        
        stystr = "face:%s,fore:%s,back:%s,size:%d" %(font, fore, back, size)
        if bold:
            stystr += ',bold'
        if italic:
            stystr += ',italic'
        if eol:
            stystr += ',eol'
        if underline:
            stystr += ',underline'
            
        return stystr
            
class StyleEditor(wx.Dialog):
    def __init__(self, parent, id_=wx.ID_ANY, title="Style Editor",
                 style=wx.DEFAULT_DIALOG_STYLE | wx.RAISED_BORDER):
        wx.Dialog.__init__(self, parent, id_, title, style=style)
        
        # Main Sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        
       # Control Panel
        self.ctrl_pane = wx.Panel(self, wx.ID_ANY)
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)  # Main Control Sizer
        left_colum = wx.BoxSizer(wx.VERTICAL)    # Left Column
        right_colum = wx.BoxSizer(wx.VERTICAL)   # Right Column
                