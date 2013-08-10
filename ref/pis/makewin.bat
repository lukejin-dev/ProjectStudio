
C:\dev_soft\cx_Freeze\FreezePython.exe -O -O --include-modules=encodings.cp437,encodings.gbk,encodings.utf_16,encodings.utf_8,encodings.string_escape,encodings.mbcs --install-dir ..\Binary --target-name=EDES2008.exe --base-binary=Win32GUI PIS.pyw
REM C:\dev_soft\cx_Freeze\FreezePython.exe --include-modules=encodings.cp437,encodings.gbk,encodings.utf_16,encodings.utf_8 --install-dir ..\Binary --target-name=EDES2008.exe PIS.pyw
mkdir ..\Binary\plugins
mkdir ..\Binary\syntax
mkdir ..\Binary\util
xcopy plugins ..\Binary\plugins /R /S /Y
xcopy syntax ..\Binary\syntax /R /S /Y
copy util\logserver.py ..\Binary\util /y
copy util\profile.py ..\Binary\util /y