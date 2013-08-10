import core.plugin
import wx, re, array
import wx.lib.pydocview as pydocview
import core.service
import ui.MessageWindow
import os
import locale
import re
    
_plugin_module_info_ = [{"name":"DoxygenPlugin",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Provide doxygen utilities",
                         "class":"DoxygenPlugin"}]
                         
class DoxygenPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return DoxygenService          
        
class DoxygenService(core.service.PISService):
    ID_DOXYGEN_FILE = wx.NewId()
    
    def GetName(self):
        return 'Doxygen'
        
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        menubar = frame.GetMenuBar()
        toolmenu = menubar.GetMenu(menubar.FindMenu('Tools'))
        item = wx.MenuItem(toolmenu, self.ID_DOXYGEN_FILE, 'Beautify Doxygen Comments', 'Beautify Doxygen Comments')
        wx.EVT_MENU(frame, self.ID_DOXYGEN_FILE, self.OnDoxygenFile)
        toolmenu.InsertItem(0, item)                                   
        
    def OnDoxygenFile(self, event):
        # get current document
        docMgr = wx.GetApp().GetDocumentManager()
        doc = docMgr.GetCurrentDocument()
        if doc == None:
            wx.MessageBox("No doc is opened!",
                          'Doxygen comment',
                          wx.OK | wx.ICON_ERROR)             
            return
        fname = doc.GetFilename()
        name, ext = os.path.splitext(fname)
        if ext not in ['.c', '.h']:
            wx.MessageBox('Current document %s is not a valid source code!' % fname,
                          'Doxygen comment',
                          wx.OK|wx.ICON_ERROR)
            return
        view = doc.GetFirstView()
        if view == None: return
        self.Process(view)
        
    def Process(self, view):
        self.ProcessFunctionHeader(view)
        self.ProcessFileHeader(view)
        
    def ProcessFileHeader(self, view):
        count = view.GetLineCount()
        old_start = 0
        old_end   = 0
        status    = None
        descript  = []
        abstract  = []
        header_start = 0
        header_end   = 0
        name_start   = 0
        abstract_start = 0
        for index in xrange(count - 1):
            line = view.GetLine(index + 1).rstrip()
            if index > 5 and status == None:
                self.GetLogger().info('no any file header!')
                return
            
            if line.startswith('/**') and line.find('@file') != -1:
                self.GetLogger().info('already is doxygen header')
                return
                
            #
            # Status machine change
            #                
            if line.startswith('/*+') or line.startswith('/*-'):
                status = 'old_comment_start'
                header_start = index + 1
                continue
                
            if line.endswith('-*/') or line.endswith('+*/'):
                status = 'old_comment_end'
                header_end = index + 1
                break
            
            if line.lower().find('module name:') != -1:
                status = 'module_name_comment'
                name_start = index + 1
                continue
                
            if line.lower().find('abstract:') != -1:
                status = 'abstract_comment'
                abstract_start = index + 1
                continue
                
            if status == 'old_comment_start':
                descript.append(line)
                
            if status == 'abstract_comment':
                abstract.append(line)
        
        if status != 'old_comment_end':
            self.GetLogger().warning('Fail to parse old file header')
            return
        
        # apply doxygen indicator    
        view.LineDelete(header_start)
        view.InsertLine(header_start, '/** @file')
        view.LineDelete(header_end)
        view.InsertLine(header_end, '**/')
        
        # remove all lines after 'Module Name:'
        visit  = header_end - 1
        top = min(name_start, abstract_start)
        if top != 0:
            while (visit >= top):
                view.LineDelete(visit)
                visit -= 1
                
        visit = len(abstract) - 1
        while (visit >= 0):
            line = abstract[visit].strip()
            if len(line) == 0:
                del abstract[visit]
            else:
                break
            visit -= 1
        
        # add abstraction
        visit = header_start + 1
        if len(abstract) == 0:
            view.InsertLine(visit, '  EDES_TODO: Add abstraction')
            visit += 1
        else:
            for line in abstract:
                view.InsertLine(visit, line)
                visit += 1
                 
    def ProcessFunctionHeader(self, view):
        text = view.GetValue()
        import syntax.clex
        text = text.replace('\r\n', '\n')
        tokens = syntax.clex.run_parse(text)

        funclist = []
        level = 0

        for index in xrange(len(tokens)):
            if tokens[index].type == 'LBRACE':
                level += 1
                
            # find '(' char in level 0, it potential is a function.
            if tokens[index].type == 'LPAREN' and level == 0:
                if tokens[index - 2].value == u'typedef' or \
                   tokens[index - 3].value == u'typedef' or \
                   tokens[index - 4].value == u'typedef':
                    level += 1
                    continue
                    
                line = tokens[index - 1].lineno
                linetext = view.GetLine(line)
                
                # skip macro function 
                if not linetext.strip().startswith('#'):
                    funcname = tokens[index - 1].value
                    
                    if not re.match('[a-zA-Z0-9]+', funcname, re.UNICODE):
                        level += 1
                        continue
                    
                    # work around to skip following macro function
                    if funcname.lower() in [u'_cr', u'_assert', u'while', u'\\',
                                            u'debug_code_begin', u'debug_code_end']:
                        level += 1
                        continue
                    
                    visit = index - 1
                    while ((tokens[visit].type == 'ID' or tokens[visit].type == 'ASTERISK') and \
                           (tokens[visit + 1].lineno - tokens[visit].lineno) < 3) :
                        visit -= 1
                    new_start = tokens[visit].lineno + 1
                    new_end   = tokens[visit + 1].lineno
                    
                    visit = index 
                    while tokens[visit].type != 'RPAREN':
                        visit += 1
                    old_start = tokens[visit].lineno + 1
                    while tokens[visit].type != 'SEMICOLON' and \
                          tokens[visit].type != 'LBRACE':
                        visit += 1
                        if visit >= len(tokens) - 1:
                            break;
                    old_end = tokens[visit].lineno

                    # find functon list
                    visit = index
                    params = []
                    while tokens[visit].type != 'RPAREN':
                        if tokens[visit].type == 'COMMA':
                            params.append(tokens[visit - 1].value)
                        visit += 1
                    params.append(tokens[visit - 1].value)
                    
                    funclist.append((funcname, old_start, old_end, new_start, new_end, params))
                    
            if tokens[index].type == 'LPAREN':
                level += 1
                            
            if tokens[index].type == 'RBRACE' or \
               tokens[index].type == 'RPAREN':
                level -= 1
        
        # process function list
        index = len(funclist) - 1
        while (index >= 0):
            item = funclist[index]
            func_desc, param_desc, return_desc = self.GetOldDescription(view, item[1], item[2], item[5])        
            visit = item[2] - 1
            while (visit >= item[1]):
                view.LineDelete(visit)
                visit -= 1
                
            if self.HasNewDescription(view, item[3], item[4]):
               index -= 1
               continue
               
            visit = item[4]
            view.InsertLine(visit, '/**')
            visit += 1
            if len(func_desc) == 0:
                view.InsertLine(visit, '  EDES_TODO: Add function description')
                visit += 1
            else:
                for desc in func_desc:
                    view.InsertLine(visit, '  %s' % desc)
                    visit += 1
            
            view.InsertLine(visit, ' ')
            visit += 1
            
            # Add parameters
            for param in item[5]:
                if param_desc.has_key(param) and len(param_desc[param]) != 0:
                    for pIndex in range(len(param_desc[param])):
                        if pIndex == 0:
                            view.InsertLine(visit, 
                                            '  @param %-15s %s' % (param, 
                                                                param_desc[param][pIndex].lstrip())
                                            )
                        else:
                            str = ''
                            view.InsertLine(visit, '%-25s'%str + param_desc[param][pIndex].lstrip())
                        visit += 1
                else:
                    view.InsertLine(visit, '  @param %-15s EDES_TODO: Add parameter description' % param)
                    visit += 1
            
            view.InsertLine(visit, ' ')
            visit += 1
            
            # Add return value
            if len(return_desc) == 0:
                view.InsertLine(visit, '  @return EDES_TODO: Add description for return value')
                visit += 1
            else:
                for rIndex in range(len(return_desc)):
                    if rIndex == 0:
                        view.InsertLine(visit, '  @return %s' % return_desc[rIndex].lstrip())
                        visit += 1
                    else:
                        view.InsertLine(visit, '          ' + return_desc[rIndex].lstrip())
                        visit += 1
            view.InsertLine(visit, ' ')
            visit += 1
                                    
            view.InsertLine(visit, '**/')
            index -= 1
                
    def HasNewDescription(self, view, start, end):
        if end - start <= 0:
            return False
        
        index = start
        while (index < end):
            line = view.GetLine(index).strip()
            
            if line.startswith('/*'):
                return True
            index += 1
        return False
        
    def GetOldDescription(self, view, start, end, params):
        if end - start <= 0:
            return [], {}, []
        
        index   = start
        status  = None
        func_desc    = []
        param_desc   = {}
        return_desc  = []
        last_param = None
        while (index < end):
            line = view.GetLine(index).strip()
            index += 1
            
            if line.startswith('/*+'):
                status = ''
                
            if line.startswith('--*/') or line.startswith('++*/') or \
               line.startswith('-*/') or line.startswith('--*/'):
               status = None
            
            if status == None: continue
            
            if line.lower().startswith('routine description:'):
                status = 'function'
                continue
            
            if line.lower().startswith('arguments:'):
                status = 'argument'
                continue
                
            if line.lower().startswith('returns:') or \
               line.lower().startswith('return:'):
                status = 'return'
                continue
                
            if status == 'function':
                func_desc.append(line)
                
            if status == 'argument' and len(line) != 0:
                name = line.split(' ')[0]
                if name in params:
                    param_desc[name] = []
                    param_desc[name].append(line[line.find(name) + len(name) + 1:])
                    last_param = name
                else:
                    if last_param != None:
                        param_desc[last_param].append(line)
            
            if status == 'return' and len(line) != 0:
                return_desc.append(line)
                
        return func_desc, param_desc, return_desc
    