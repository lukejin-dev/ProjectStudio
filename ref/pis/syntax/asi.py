import wx, wx.stc

_name   = 'asi'
_filter = 'asi,asl'

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
             # >>========= ASL related ===============<<
             "Device Name Method Else If Return CreateDwordField Store LGreaterEqual "
             "OperationRegion Field Package LEqual LLess Add Sleep Notify ")              