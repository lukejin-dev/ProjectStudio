import wx, wx.stc
import os
import clex
import re
_name   = 'c'
_filter = 'c,cpp,h,hpp'

_lex = wx.stc.STC_LEX_CPP

_stc_styles = {'STC_C_DEFAULT':   {'fore': '#000000'},
               'STC_C_COMMENTLINE': {'fore': '#007F00', 'italic': True },
               'STC_C_COMMENT': {'fore': '#007F00', 'italic': True },
               'STC_C_COMMENTDOC': {'fore': '#007F00', 'italic': True },
               'STC_C_COMMENTLINEDOC': {'fore': '#007F00', 'italic': True },
               'STC_C_COMMENTDOCKEYWORD': {'fore': '#007F00', 'italic': True },
               'STC_C_COMMENTDOCKEYWORDERROR': {'fore': '#007F00', 'italic': True },
               'STC_C_NUMBER': {'fore': '#007F7F'},
               'STC_C_STRING': {'fore': '#7F007F'},
               'STC_C_CHARACTER': {'fore': '#7F007F'},
               'STC_C_WORD': {'fore': '#00007F', 'bold':True},
               'STC_C_UUID': {'fore': '#007F00', 'italic':True},
               'STC_C_OPERATOR': {},
               'STC_C_IDENTIFIER': {},
               'STC_C_STRINGEOL': {'fore': '#000000', 'back':'#E0C0E0', 'eol':True},
               'STC_C_PREPROCESSOR': {'fore': '#808080', 'eol':True},
               'STC_C_VERBATIM': {'fore': '#808080', 'back':'#E0C0E0', 'eol':True},
               'STC_C_REGEX': {'fore': '#808080', 'back':'#E0C0E0', 'eol':True},
               'STC_C_WORD2': {'fore': '#808080', 'back':'#E0C0E0', 'eol':True},
               'STC_C_GLOBALCLASS': {'fore': '#808080', 'back':'#E0C0E0', 'eol':True},
              }

_properties = {'fold':'1',
               'styling.within.preprocessor':'1',
               'fold.comment':'1',
               'fold.compact':'1',
               'fold.at.else':'1',
               'lexer.cpp.allow.dollars':'1'}
               
_keywords = ("asm break case const continue default do else for goto return "
              "if sizeof static switch typeof while"
             "and and_eq bitand bitor catch class compl const_cast delete "
             "dynamic_cast false friend new not not_eq opperator or or_eq "
             "private protected public reinterpret_cast static_cast this "
             "throw try true typeid using xor xor_eq"
             "auto bool char clock_t complex div_t double enum extern float "
             "bool inline explicit export mutable namespace template typename "
             "virtual wchar_t"
             "fpos_t inline int int_least8_t int_least16_t int_least32_t "
             "int_least64_t int8_t int16_t int32_t int64_t intmax_t intptr_t "
             "jmp_buf ldiv_t long mbstate_t ptrdiff_t register sig_atomic_t "
             "size_t ssize_t short signed struct typedef union time_t "
             "uint_fast8_t uint_fast16_t uint_fast32_t uint_fast64_t uint8_t "
             "uint16_t uint32_t uint64_t uintptr_t uintmax_t unsigned va_list "
             "void volatile wchar_t wctrans_t wctype_t wint_t FILE DIR __label__ "
             "__complex__ __volatile__ __attribute__ "
             "TODO FIXME XXX author brief bug callgraph category class "
             "code date def depreciated dir dot dotfile else elseif em "
             "endcode enddot endif endverbatim example exception file if "
             "ifnot image include link mainpage name namespace page par "
             "paragraph param return retval section struct subpage "
             "subsection subsubsection test todo typedef union var "
             "verbatim version warning $ @ ~ < > # % HACK "
             # >>========= EFI related ===============<<
             "UINT8 UINT16 UINT32 UINT64 UINTN "
             "INT8 INT16 INT32 INT64 INTN "
             "CHAR8 CHAR16 GUID CONST TRUE FALSE "
             "EFIAPI EFI_STATUS IN OUT VOID EFI_GUID NULL BOOLEAN EFI_ERROR "
             "EFI_EVENT EFI_HANDLE EFI_STRING_ID STRING_TOKEN "
             "EFI_SUCCESS EFI_LOAD_ERROR EFI_INVALID_PARAMETER EFI_UNSUPPORTED "
             "EFI_BAD_BUFFER_SIZE EFI_BUFFER_TOO_SMALL EFI_NOT_READY "
             "EFI_DEVICE_ERROR EFI_WRITE_PROTECTED EFI_OUT_OF_RESOURCES "
             "EFI_VOLUME_CORRUPTED EFI_VOLUME_FULL EFI_NO_MEDIA EFI_MEDIA_CHANGED "
             "EFI_NOT_FOUND EFI_ACCESS_DENIED EFI_NO_RESPONSE EFI_NO_MAPPING EFI_TIMEOUT "
             "EFI_NOT_STARTED EFI_ALREADY_STARTED EFI_ABORTED EFI_ICMP_ERROR EFI_TFTP_ERROR "
             "EFI_PROTOCOL_ERROR EFI_INCOMPATIBLE_VERSION EFI_SECURITY_VIOLATION EFI_CRC_ERROR ")

            
def _OutlineCallback(view, tree):
    doc   = view.GetDocument()
    fname = doc.GetFilename()
    tree.DeleteAllItems()
    root  = tree.AddRoot(os.path.basename(fname))
    text  = view.GetValue()
    #arr = text.split('\r\n')
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    tokens = clex.run_parse(text)
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
                lineno   = tokens[index - 1].lineno
                    
                if not re.match('[a-zA-Z0-9]+', funcname, re.UNICODE):
                    level += 1
                    continue
                    
                # work around to skip following macro function
                if funcname.lower() in [u'_cr', u'_assert', u'while', u'\\',
                                            u'debug_code_begin', u'debug_code_end']:
                    level += 1
                    continue
                       
                item = tree.AppendItem(root, funcname)
                tree.SetPyData(item, lineno)                        
            
        if tokens[index].type == 'LPAREN':
            level += 1
                            
        if tokens[index].type == 'RBRACE' or \
            tokens[index].type == 'RPAREN':
            level -= 1
            
    tree.SortAllChildren(root)
    
def _SelectCallback(view, pydata):
    if pydata == None:
        return
    view.GotoLine(pydata)
    wx.CallAfter(view.SetFocus)
    
_outline_callbacks = {'InitTree': _OutlineCallback,
                      'SelectAction':_SelectCallback}     