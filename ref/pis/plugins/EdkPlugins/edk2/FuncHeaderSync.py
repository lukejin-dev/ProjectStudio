import sys
import os
import re
import wx
import  wx.grid as  Grid
import core.service

class func_entry:
    def __init__(self, filename, func, start, end):
        self.filename = filename
        self.func = func
        self.start = start
        self.end = end

class match_entry_class:
    def __init__(self, declare_entry, impl_entry):
        self.declare_entry = declare_entry
        self.impl_entry = impl_entry
        
class FuncHeaderSyncService(core.service.PISService):
    def __init__(self):
        core.service.PISService.__init__(self)

    def merge(self, match_table, inputbuf_table):
        outputbuf_table = {}
        for filename in inputbuf_table.keys():
            inputbuf = inputbuf_table[filename]
            outputbuf = ''
            fill_start = 0
            for match_entry in match_table[filename]:
                declare_entry = match_entry.declare_entry
                impl_entry = match_entry.impl_entry
                replace_str = inputbuf_table[impl_entry.filename][impl_entry.start : impl_entry.end]
                if declare_entry.start > fill_start:
                    outputbuf += inputbuf[fill_start : declare_entry.start]
                outputbuf += replace_str
                fill_start = declare_entry.end
            if fill_start < len(inputbuf):
                outputbuf += inputbuf[fill_start : len(inputbuf)]
            outputbuf_table[filename] = outputbuf
        return outputbuf_table

    def gen_match(self, inputbuf_table):
        match_table = {}
        declare_table = {}
        impl_table = {}
        comment_pattern = re.compile(r'/\*\*.*?\*\*/', re.S)
        declare_pattern = re.compile(r'(?<=\n)([^\r\n]+)[\n]+(^EFIAPI[\n]+)?(^\w+) \([\n]+([^;]*?)(^  \))(?=;)', re.S|re.M)
        impl_pattern = re.compile(r'(?<=\n)([^\r\n]+)[\n]+(^EFIAPI[\n]+)?(^\w+) \([\n]+([^;]*?)(^  \))(?=[\n]+\{)', re.S|re.M)
        for filename in inputbuf_table.keys():
            declare_list = []
            impl_list = []
            inputbuf = inputbuf_table[filename]
            comments_match = comment_pattern.finditer(inputbuf)
            comments = []
            for comment in comments_match:
                comments.append(comment)
            i = 0
            while i < len(comments):
                comment = comments[i]
                search_start = comment.end()
                if i == len(comments) - 1:
                    search_end = len(inputbuf)
                else:
                    search_end = comments[i+1].start()
                declare_matches = declare_pattern.finditer(inputbuf, search_start, search_end)
                match_index = 0
                for declare_match in declare_matches:
                    declare_start = declare_match.start()
                    if match_index == 0 and declare_match.start() - comment.end() < 5:
                        declare_start = comment.start()
                    declare = func_entry(filename, declare_match.group(3), declare_start, declare_match.end())
                    declare_list.append(declare)
                    match_index += 1
                impl_match = impl_pattern.search(inputbuf, search_start, search_end)
                if impl_match != None:
                    impl = func_entry(filename, impl_match.group(3), comment.start(), impl_match.end())
                    impl_list.append(impl)
                i += 1
            declare_table[filename] = declare_list
            impl_table[filename] = impl_list
        for filename in declare_table.keys():
            match_list = []
            declare_list = declare_table[filename]
            for declare_entry in declare_list:
                for impl_list in impl_table.values():
                    for impl_entry in impl_list:
                        if declare_entry.func == impl_entry.func:
                            match_entry = match_entry_class(declare_entry, impl_entry)
                            match_list.append(match_entry)
            match_table[filename] = match_list
        return match_table
                
    def read_files(self, dir):
        table = {}
        for filename in os.listdir(dir):
            if filename.endswith('.h') or filename.endswith('.c'):
                fin = open(os.path.join(dir, filename),'r')
                table[filename] = fin.read()
                fin.close()
        return table

    def write_files(self, dir, outputbuf_table):
        for filename in outputbuf_table.keys():
            fout = open(os.path.join(dir, filename), 'w')
            fout.truncate()
            fout.write(outputbuf_table[filename])
            fout.close()

    def Run(self, workspace, folder):
        if not os.path.exists(workspace):
            wx.MessageBox('FuncHeaderSync fail: Workspace path %s does not exist!' % worksapce)
            return
        dir = os.path.join(workspace, folder)
        if not os.path.exists(dir):
            wx.MessageBox('FuncHeaderSync fail: Folder path %s does not exist!' % folder)
            return
        dlg = wx.MessageDialog(None, "This feature is experimental and might break your files. Use with care!", "Warning", wx.OK|wx.CANCEL)
        result = dlg.ShowModal ()
        dlg.Destroy ()
        if result == wx.ID_OK:
            inputbuf_table = self.read_files(dir)
            self.write_files(dir, self.merge(self.gen_match(inputbuf_table), inputbuf_table))
            wx.MessageBox('FuncHeaderSync Done for dir %s!' % dir)
