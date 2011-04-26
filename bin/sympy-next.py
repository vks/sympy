#! /usr/bin/env python

# Tool to aggeregrate several branches, automatically merge them (if possible)
# and create statistics about unit tests.
#
# Usage: sympy-next.py repo branches out-dir
#    or: sympy-next.py out-dir
# where
#   repo      is is the location of a clean repository (possibly empty)
#             that is going to be used.
#   branches  is a file containing a list of branches, one entry per line, like
#             so:
#                    https://github.com/sympy/sympy.git master
#                    /home/ness/src/sympy 360_zoo
#                    ...
#   out-dir   Is the name of a directory where output is going to be created.
#
# This program walks the list of branches, fetches all of them, and tries to
# merge them in order. If there are merge-failures the branch is dropped. After
# all successful merges are done, the unit tests are run. Finally a report is
# created of which branches could be merged, and which tests passed.
# All commands run are logged to a file in the output directory.
#
# If only out-dir is specified, then only the html is re-created.
#
# TODO
#  o Html output, and output creation, are ugly.
#  o At some stage pruning reports, or at least not showing everything, is
#    probably helpful.

import sys
import os
import time
import subprocess
import pickle

def logit(message):
    print >> log, '>', message
    log.flush()

def read_branchfile(f):
    ret = []
    with open(f) as fd:
        for line in fd:
            src, branch = line.split()
            ret.append((src, branch))

    return ret

def run_tests():
    logit("Running unit tests.")
    out = subprocess.Popen(["./bin/test"], stdout=subprocess.PIPE).stdout

    # echo to log
    print >> log, out
    log.flush()

    report = []
    # process output
    lines = out.xreadlines()
    for line in lines:
        good = None
        if line.endswith('[OK]\n'):
            good = True
        elif line.endswith('[FAIL]\n'):
            good = False
        if good is None:
            continue
        report.append((line.split('[')[0], good))

    return report

def do_test(branches, name):
    def git(message, *args):
        logit("%s: git %s" % (message, ' '.join(args)))
        return subprocess.call(("git",) + args, stdout=log, stderr=log)
    def gitn(message, *args):
        if git(message, *args) != 0:
            raise RuntimeError('%s failed' % message)

    # first pull the main branch
    gitn("checkout master", "checkout", "master")
    gitn("reset tree", "reset", "--hard")
    gitn("pull master", "pull", branches[0][0], branches[0][1])
    if git("switch to temporary branch", "checkout", "-b", name):
        logit("Stale test branch?")
        gitn("delete stale temporary branch", "branch", "-D", name)
        gitn("switch to temporary branch", "checkout", "-b", name)

    # now try and fetch all other branches
    report = []
    for source, branch in branches[1:]:
        logit("Merging branch %s from %s." % (branch, source))
        if git("Fetching branch " + branch, "fetch", source, branch):
            logit("Error fetching branch -- skipping.")
            report.append((source, branch, "fetch"))
            continue
        if git("Merge branch " + branch, "merge", "FETCH_HEAD"):
            gitn("Error merging branch %s -- skipping." % branch,
                 "merge", "--abort")
            report.append((source, branch, "merge"))
            continue
        report.append((source, branch, "clean"))

    # run the tests
    tests = run_tests()

    # delete our temporary branch
    gitn("switch back to master", "checkout", "master")
    gitn("delete temporary branch", "branch", "-D", name)

    return report, tests

def write_report(reports):
    # create a html report
    allstamps   = [t[0] for t in reports]
    allbranches = set()
    alltests    = set()
    for t in reports:
        for u in t[1]:
            allbranches.update([(u[0], u[1])])
        for u in t[2]:
            alltests.update([u[0]])

    branchtable = {}
    testtable   = {}
    for branch in allbranches:
        branchtable[branch] = {}
    for test in alltests:
        testtable[test] = {}

    for stamp, branches, tests in reports:
        for b1, b2, status in branches:
            branchtable[(b1, b2)][stamp] = status
        for test, status in tests:
            testtable[test][stamp] = status

    outf = open('report.html', 'w')
    outf.write('''
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
           "http://www.w3.org/TR/html4/loose.dtd">
    <html>
    <head>
    <title>sympy-next</title>
    </head>
    <body>
    ''')

    outf.write('<h1> Merge Report </h1>\n')
    outf.write('<table border="1">\n')
    outf.write('  <tr>\n')
    outf.write('    <th> </th>\n')
    for stamp in allstamps:
        outf.write('    <th> %s </th\n' % stamp)
    outf.write('  </tr>\n')
    for name, branch in sorted(branchtable.iteritems()):
        outf.write('  <tr>\n')
        outf.write('    <th align="left"> %s %s </th>\n' % (name[0], name[1]))
        for stamp in allstamps:
            if stamp in branch:
                if branch[stamp] == 'clean':
                    outf.write('    <td align="center" bgcolor="#00FF00"> clean </td>\n')
                elif branch[stamp] == 'merge':
                    outf.write('    <td align="center" bgcolor="#FF0000"> conflicts </td>\n')
                else:
                    outf.write('    <td align="center" bgcolor="#FFFF00"> fetch </td>\n')
            else:
                outf.write('    <th> N/A </th>\n')
        outf.write('  </tr>\n')
    outf.write('</table>\n')

    outf.write('<h1> Test Report </h1>\n')
    outf.write('<table border="1">\n')
    outf.write('  <tr>\n')
    outf.write('    <th> </th>\n')
    for stamp in allstamps:
        outf.write('    <th> %s </th\n' % stamp)
    outf.write('  </tr>\n')
    for name, test in sorted(testtable.iteritems()):
        outf.write('  <tr>\n')
        outf.write('    <th align="left"> %s </th>\n' % name)
        for stamp in allstamps:
            if stamp in test:
                if test[stamp]:
                    outf.write('    <td align="center" bgcolor="#00FF00"> OK </td>\n')
                else:
                    outf.write('    <td align="center" bgcolor="#FF0000"> FAIL </td>\n')
            else:
                outf.write('    <td align="center"> N/A </td>\n')
        outf.write('  </tr>\n')
    outf.write('</table>\n')

    outf.write('</body></html>')

picklef = "reports"
def create_report(merges, tests, stamp):
    # load old reports
    reports = []
    if os.path.exists(picklef):
        f = open(picklef, "rb")
        reports = pickle.load(f)
        f.close()

    reports.append((stamp, merges, tests))

    # dump all reports
    f = open(picklef, "wb")
    pickle.dump(reports, f)
    f.close()

    write_report(reports)


# MAIN PROGRAM

if len(sys.argv) == 2:
    os.chdir(sys.argv[1])
    write_report(pickle.load(open(picklef, 'rb')))
    sys.exit(0)

if len(sys.argv) != 4:
    print >> sys.stderr, "Usage: %s repo branches out-dir" % sys.argv[0]
    sys.exit(1)

repo       = os.path.abspath(sys.argv[1])
branchfile = os.path.abspath(sys.argv[2])
outdir     = os.path.abspath(sys.argv[3])

# create us a timestamp
tm = time.localtime(time.time())
stamp = "%s%s%s%s%s" % (tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)

# create out dir if necessary
if not os.path.exists(outdir):
    os.mkdir(outdir)

# we will log all output to here
log = open(os.path.join(outdir, stamp), 'w')

# find out which branches to test
branches = read_branchfile(branchfile)

# do the merging and testing
os.chdir(repo)
merges, tests = do_test(branches, "next-test")

# create a report
os.chdir(outdir)
create_report(merges, tests, stamp)
