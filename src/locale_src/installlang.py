
import os
import msgfmt

if __name__ == "__main__":
    curpath = os.getcwd()
    outpath = os.path.join("..", "locale")
    
    for dir in os.listdir(curpath):
        if dir.lower() in [".svn", "_svn", "cvs"]:
            continue
        
        if os.path.isfile(dir):
            continue
        
        outputdir = os.path.join(outpath, dir)
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
            
        for file in os.listdir(os.path.join(curpath, dir)):
            if file.lower().endswith(".po"):
                msgfmt.make(os.path.join(curpath, dir, file), os.path.join(outputdir, file[:-3] + ".mo"))
                
    