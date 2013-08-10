import core.editor 

class INIDoc(core.editor.EditorDocument):
    def __init__(self):
        core.editor.EditorDocument.__init__(self)
        self._iniobj = None
        
        
class INIView(core.editor.EditorView):
    pass    