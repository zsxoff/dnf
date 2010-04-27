#! /usr/bin/python -tt

import yum, os, time, gc, sys
from urlgrabber.progress import format_number

def out_mem(pid):
    ps = {}
    for line in open("/proc/%d/status" % pid):
        if line[-1] != '\n':
            continue
        data = line[:-1].split(':\t', 1)
        if data[1].endswith(' kB'):
            data[1] = data[1][:-3]
        ps[data[0].strip().lower()] = data[1].strip()
    if 'vmrss' in ps and 'vmsize' in ps:
        print "* Memory : %5s RSS (%5sB VSZ)" % \
                    (format_number(int(ps['vmrss']) * 1024),
                     format_number(int(ps['vmsize']) * 1024))

print "Running:", yum.__version__

def _leak_tst_yb():
 print "Doing YumBase leak test. "
 out_mem(os.getpid())
 while True:
    yb = yum.YumBase()
    yb.repos.setCacheDir(yum.misc.getCacheDir())
    yb.rpmdb.returnPackages()
    yb.pkgSack.returnPackages()
    out_mem(os.getpid())
    time.sleep(4)

    if False:
       del yb
       print len(gc.garbage)
       if gc.garbage:
           print gc.garbage[0]
           print gc.get_referrers(gc.garbage[0])
    # print "DBG:", gc.get_referrers(yb)

def _leak_tst_ir():
    print "Doing install/remove leak test. "

    sys.path.insert(0, '/usr/share/yum-cli')
    import cli
    out_mem(os.getpid())
    yb = cli.YumBaseCli() # Need doTransaction() etc.
    yb.preconf.debuglevel = 0
    yb.preconf.errorlevel = 0
    yb.repos.setCacheDir(yum.misc.getCacheDir())
    yb.conf.assumeyes = True

    def _run(yb):
        print "  Run"
        (code, msgs) = yb.buildTransaction()
        if code == 1:
            print "ERROR:", core, msgs
            sys.exit(1)
        returnval = yb.doTransaction()
        if returnval != 0: # We could allow 1 too, but meh.
            print "ERROR:", returnval
            sys.exit(1)
        yb.closeRpmDB()

    last = None
    while True:
        out_mem(os.getpid())
        print "  Install:", sys.argv[1:]
        for pat in sys.argv[1:]:
            yb.install(pattern=pat)
        out_mem(os.getpid())
        _run(yb)

        print "  Remove:", sys.argv[1:]
        for pat in sys.argv[1:]:
            yb.remove(pattern=pat)
        out_mem(os.getpid())
        _run(yb)

if sys.argv[1:]:
    _leak_tst_ir()
else:
    _leak_tst_yb()
