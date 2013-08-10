import sys
import profile, pstats

if __name__== '__main__':
    args = sys.argv
    
    if len(args) < 2:
        print 'Please specific profile file'
        sys.exit(0)
        
    fname = sys.argv[1]
    
    stats = pstats.Stats(fname)
    print "======= Sort by time ======="
    stats.strip_dirs().sort_stats("time").print_stats(20)     
    
    print "======= Sort by calls ======="
    stats.strip_dirs().sort_stats("calls").print_stats(20)     
    
    print "======= Sort by primitive call count ======="
    stats.strip_dirs().sort_stats("pcalls").print_stats(20)         
        