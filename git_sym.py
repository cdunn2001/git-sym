#!/usr/bin/env python2.7
"""
Environment variables used:
    GIT_SYM_DIR
    GIT_SYM_CACHE_DIR

We use 2 levels of symlink. The first are committed in the git repo. The second are in GIT_SYM_DIR.
If GIT_SYM_DIR is not set, we try to use .git/git_sym for the symlink cache. But a submodule lacks
the

We expect this in .gitconfig:

    [alias]
    exec = "!exec "

That facilitates running this script, and is also used within this script.
(Git aliases are always run in the root of a Git tree.)
  http://stackoverflow.com/questions/957928/is-there-a-way-to-get-the-git-root-directory-in-one-command

"""
from contextlib import contextmanager
import sys, os, re, subprocess, argparse, traceback, ConfigParser


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    log('-> in dir %r' %newdir)
    yield
    os.chdir(prevdir)
    log('<- back to dir %r' %prevdir)
def shell(cmd):
    """Return result of 'cmd' in a shell.
    cmd: a list of strings
    """
    log("!%s" %cmd)
    return subprocess.check_output(cmd, shell=True) #TODO: Allow python2.6?
def make_dirs(d):
    log("makedirs(%s)" %d)
    if not os.path.exists(d):
        log("mkdir -p %s" %d)
        os.makedirs(d)
def log_msg(msg):
    sys.stderr.write('#')
    sys.stderr.write(str(msg))
    sys.stderr.write('\n')
def debug_msg(msg):
    sys.stderr.write(str(msg))
    sys.stderr.write('\n')
def noop(msg):
    pass

debug = noop
log = noop

def is_in_gitignore(path):
    """Must be relative to CWD, *not* absolute.
    """
    cmd = "git check-ignore -q %r" %path
    try:
        shell(cmd)
        return True
    except Exception:
        return False
def redo_GIT_SYM_LINK(GIT_SYM_LINK):
    """GIT_SYM_LINK should *not* be under revision-control.
    However, even if in .gitignore, 'git clean' can remove it.
    So sometimes we need to re-create it.
    """
    if not os.path.islink(GIT_SYM_LINK):
        log("$ ln -sf %r %r" %(GIT_SYM_DIR, GIT_SYM_LINK))
        os.symlink(GIT_SYM_DIR, GIT_SYM_LINK)
def get_GIT_SYM_LINK():
    """
    Create symlink and add to git-ignores, if needed.
    Needs GIT_DIR and GIT_ROOT_DIR.
    """
    GIT_SYM_LINK = os.path.join(GIT_ROOT_DIR, '.git_sym')
    # Re-create, in case of 'git clean -x'.
    redo_GIT_SYM_LINK(GIT_SYM_LINK)
    if not is_in_gitignore(os.path.relpath(GIT_SYM_LINK, start=os.getcwd())):
        cmd = "echo '/.git_sym' >| %s/info/exclude" %GIT_DIR
        shell(cmd)
    return GIT_SYM_LINK
def get_GIT_SYM_CACHE_DIR():
    result = os.environ.get('GIT_SYM_CACHE_DIR', None)
    if not result:
        result = shell('echo ${HOME}/git_sym_cache').strip()
    result = os.path.abspath(result)
    if not os.path.isdir(result):
        make_dirs(result)
    return result
def get_GIT_DIR():
    """Can return None.
    """
    try:
        # '.git' could be a file for git-submodule, so rely on rev-parse.
        result = shell('git rev-parse --git-dir').strip()
    except Exception as e:
        log(e)
        # Assume we are running in the '.git' dir already, as a git-hook.
        result = None
    return result
def get_GIT_ROOT_DIR():
    result = shell('git gsexec pwd -P').strip()
    return result
def read_cfg(root):
    cfg = {
        'symlinks': {},
    }
    filename = os.path.join(GIT_ROOT_DIR, '.git_sym.cfg')
    if os.path.exists(filename):
        parser = ConfigParser.ConfigParser()
        log("filename=%r" %filename)
        from_file = parser.read(filename)
        log("from_file=%r" %from_file)
        cfg.update(from_file)
    debug("cfg=%r" %(cfg,))
    return cfg
def global_setup():
    """We need to know the top-level directory, unless
    we already have some environment variables.
    """
    global GIT_SYM_LINK, GIT_SYM_DIR, GIT_SYM_CACHE_DIR, GIT_DIR, GIT_ROOT_DIR
    shell("git config alias.gsexec '!exec '")
    GIT_SYM_CACHE_DIR = get_GIT_SYM_CACHE_DIR()
    GIT_ROOT_DIR = get_GIT_ROOT_DIR()
    GIT_DIR = os.path.abspath(get_GIT_DIR())
    GIT_SYM_DIR = os.path.join(GIT_DIR, 'git_sym')
    debug("GIT_SYM_DIR=%r" %GIT_SYM_DIR)
    debug("GIT_SYM_CACHE_DIR=%r" %GIT_SYM_CACHE_DIR)
    debug("GIT_DIR=%r" %GIT_DIR)
    debug("GIT_ROOT_DIR=%r" %GIT_ROOT_DIR)
    make_dirs(GIT_SYM_DIR)
    make_dirs(GIT_SYM_CACHE_DIR)

    # Use an extra level an indirection if '/.git_sym' is in '.gitignore'.
    GIT_SYM_LINK = get_GIT_SYM_LINK() # could be None
    #GIT_SYM_INI = read_cfg(GIT_ROOT_DIR)
    debug("GIT_SYM_LINK=%r" %GIT_SYM_LINK)
def is_link_thru(via, symlink):
    """
    Reject symlink if it does not point to a relative path.
    For simplicity, 'via' should be abspath already.
    """
    if not os.path.islink(symlink):
        return False
    rel_link_to = os.readlink(symlink)
    if os.path.isabs(rel_link_to):
        return False
    link_to = os.path.join(os.path.dirname(symlink), rel_link_to)
    cp = os.path.commonprefix([os.path.abspath(via), os.path.abspath(link_to)])
    return cp == via
def find_all_symlinks():
    """Find all symlinks in git objects beneath the current directory.
    """
    # By using git-ls-tree intead of os.walk(), we do not recurse into submodules.
    # However, we are really looking only at the commit, not the index nor working-dir.
    cmd = 'git ls-tree -r --full-name HEAD'
    ls_tree = shell(cmd)
    re_ls_tree = re.compile(r'^120000\s+blob\s+\S+\s+(\S+)$', flags=re.MULTILINE)
    for full_name in re_ls_tree.findall(ls_tree):
        # full_name is from root-dir, not CWD.
        abs_name = os.path.join(GIT_ROOT_DIR, full_name)
        yield abs_name
def find_symlinks(via):
    """Find symlinks which point thru 'via'.
    Ignore absolute symlinks.
    Return both file and dir symlinks.
    """
    debug("find_symlinks(via=%r)" %via)
    assert os.path.isabs(via)
    cwd = os.getcwd()
    for abs_name in find_all_symlinks():
        if is_link_thru(via, abs_name):
            symlink = os.path.relpath(abs_name, start=cwd)
            log('symlink: %r' %symlink)
            yield symlink
def show_symlinks(abs_symlinks, via):
    """For each symlink,
    describe how we interpret it.

    '+' Unresolved, possibly uncached.
    '.' Cached and fully resolved file.
    '/' Cached and fully resolved directory.
    'O' Ignored.
    """
    cwd = os.getcwd()
    for abs_name in abs_symlinks:
        symlink = os.path.relpath(abs_name, start=cwd)
        if not os.path.islink(abs_name):
            line = '? %s\n' %symlink
            sys.stdout.write(line)
            continue
        elif not is_link_thru(via, abs_name):
            sym = 'O'
        elif os.path.isfile(abs_name):
            sym = '.'
        elif os.path.isdir(abs_name):
            sym = '/'
        else:
            sym = '+'
        link_to = os.readlink(symlink)
        joined_link_to = os.path.normpath(os.path.join(os.path.dirname(symlink), link_to)) \
                if not os.path.isabs(link_to) else link_to
        line = '%s %s\t%s\n' %(sym, symlink, joined_link_to)
        sys.stdout.write(line)
def retrieve_using_make(makefilename, paths):
    MAX_ARG_LEN = 1000
    paths = list(paths) # since we will modify
    while paths:
        a_few = list()
        while len(' '.join(a_few)) < MAX_ARG_LEN and paths:
            a_few.append(paths.pop())
        if len(a_few) > 1:
            # Put one back to avoid exceeding our limit.
            paths.append(a_few.pop())
        cmd = "make -j -f %s %s" %(
            makefilename,
            ' '.join("'%s'"%p for p in a_few))
        shell(cmd)
def retrieve(paths):
    debug("retrieve: %r" %paths)
    if not paths:
        return # to avoid the default make rule
    makefilename = os.path.join(GIT_ROOT_DIR, 'git_sym.makefile')
    with cd(GIT_SYM_CACHE_DIR):
        retrieve_using_make(makefilename, paths)
    for path in paths:
        cached_path = os.path.join(GIT_SYM_CACHE_DIR, path)
        debug('Checking %r -> %r' %(path, cached_path))
        assert os.path.exists(cached_path), cached_path
        if not os.path.islink(path):
            log("$ ln -sf %r %r" %(cached_path, path))
            os.symlink(cached_path, path)
        assert os.path.exists(path), path
        assert os.path.exists(cached_path), cached_path
        assert os.path.samefile(cached_path, path), "%r != %r" %(
                cached_path, path)
def get_linked_path(symlink, via):
    linked = os.readlink(symlink)
    norm_linked = os.path.normpath(os.path.join(os.path.dirname(symlink), linked))
    canon_linked = os.path.relpath(norm_linked, start=via)
    debug("%r -> %r [%r] (%r)" %(symlink, linked, canon_linked, norm_linked))
    return canon_linked
def check_link(symlink):
    """
    Return True iff the symlink is resolved.
    """
    if not os.path.isfile(symlink) and not os.path.isdir(symlink):
        log('%r -> %r does not exist' %(symlink, os.readlink(symlink)))
        return False
    return True
def fix(symlink, via_old, via_new):
    assert os.path.isabs(via_old), via_old
    assert os.path.isabs(via_new), via_new
    to_link_old = os.readlink(symlink)
    #debug(to_link_old)
    to_link_joined_old = os.path.join(os.path.dirname(symlink), to_link_old)
    #debug(to_link_joined_old)
    to_link_rel_old = os.path.relpath(to_link_joined_old, start=via_old)
    #debug(to_link_rel_old)
    to_link_joined_new = os.path.join(via_new, to_link_rel_old)
    #debug(to_link_joined_new)
    to_link_new = os.path.relpath(to_link_joined_new, start=os.path.dirname(symlink))
    #debug(to_link_new)
    debug('%r becomes %r' %(to_link_old, to_link_new))
    os.unlink(symlink)
    os.symlink(to_link_new, symlink)
def unique_name(path):
    if os.path.isdir(path):
        return 'dir.' + path
    if os.path.islink(path):
        raise Exception('We do not cache symlinks: %r' %path)
    if not os.path.isfile(path):
        raise Exception('We cannot cache that which does not exist.' %path)
    sha1 = shell('git hash-object %r' %path)
    log('strip? %r' %sha1)
    sha1 = sha1.strip()
    return 'sha1.' + sha1 + '.' + os.path.basename(path)

def git_sym_update(symlinks, **args):
    if not symlinks:
        symlinks = list(find_symlinks(GIT_SYM_LINK))
    needed = set()
    for symlink in symlinks:
        if not check_link(symlink):
            basename = os.path.basename(os.readlink(symlink))
            path = get_linked_path(symlink, GIT_SYM_LINK)
            # We require flat, unique link-names within GIT_SYM_DIR.
            assert path == basename, (path, basename)
            needed.add(basename)
    debug("needed: %s" %repr(needed))
    with cd(GIT_SYM_DIR):
        retrieve(needed)
    git_sym_check(symlinks)
def git_sym_add(paths, **args):
    needed = set()
    for path in paths:
        uname = unique_name(path)
        needed.add(uname)
        cached = os.path.join(GIT_SYM_CACHE_DIR, uname)
        shell('mv %s %s' %(path, cached))
        link_to = os.path.relpath(os.path.join(GIT_SYM_LINK, uname), start=os.path.dirname(path))
        log('$ ln -sf %r %r' %(link_to, path))
        os.symlink(link_to, path)
        shell('git add %s' %path)
        mode = os.stat(cached).st_mode & ~0222
        log('$ chmod -w %r' %cached)
        os.chmod(cached, mode)
    with cd(GIT_SYM_DIR):
        retrieve(needed)
    git_sym_show(paths)
def git_sym_show(symlinks, **args):
    if not symlinks:
        symlinks = find_all_symlinks()
    show_symlinks(symlinks, via=GIT_SYM_LINK)
def git_sym_check(symlinks, **args):
    if not symlinks:
        symlinks = list(find_symlinks(GIT_SYM_LINK))
    for symlink in symlinks:
        if not check_link(symlink):
            raise Exception(symlink)
def git_sym_missing(symlinks, **arsg):
    if not symlinks:
        symlinks = list(find_symlinks(GIT_SYM_LINK))
    missing = 0
    for symlink in symlinks:
        if not check_link(symlink):
            sys.stdout.write('%s\n' %symlink)
            missing += 1
    #if missing:
    #    raise Exception(missing)
def git_sym_fix(symlinks, **args):
    GIT_SYM_VIA_OLD = GIT_SYM_DIR
    if not symlinks:
        symlinks = list(find_symlinks(GIT_SYM_VIA_OLD))
    for sl in symlinks:
        fix(sl, GIT_SYM_VIA_OLD, GIT_SYM_LINK)
def main(args):
    global log, debug
    if args['verbose']:
        log = log_msg
    if args['debug']:
        log = debug = debug_msg
    debug(args)
    cmd_table = {
            'add': git_sym_add,
            'check': git_sym_check,
            'fix': git_sym_fix,
            'missing': git_sym_missing,
            'show': git_sym_show,
            'update': git_sym_update,
    }
    cmd = args['command']
    del args['command']
    try:
        cmd_table[cmd](**args)
    except subprocess.CalledProcessError as e:
        log(e)
        log(" in directory %r" %os.getcwd())
        sys.exit(1)
    except Exception:
        log(traceback.format_exc())
        sys.exit(1)
def add_command(subs, command, help):
    sub = subs.add_parser(command, help=help)
    sub.add_argument('symlinks', nargs='*', help='If not given, walk through tree to find relevant symlinks.')
    return sub
def parse_args():
    global_setup()
    epilog = 'See git-sym in GitHub for details.'
    parser = argparse.ArgumentParser(
            description='Cache symlinks (presumably for large files).',
            epilog=epilog)
    parser.add_argument('--retriever',
            help="(not implemented) For now, we always use 'make -f git_sym.makefile'.")
    parser.add_argument('--cache-dir',
            default=GIT_SYM_CACHE_DIR,
            help='Directory in which to store retrieved files/directories. [default=%(default)s]')
    parser.add_argument('--dir',
            default=GIT_SYM_DIR,
            help='Directory of symlinks into CACHE_DIR. (1st level of indirection.) [default=%(default)s]')
    parser.add_argument('--link',
            default=GIT_SYM_LINK,
            help='Symlink to GIT_SYM_DIR. Intermediate level of indirection. Should be ignored by git. [default=%(default)s]')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', '-g', action='store_true')

    subs = parser.add_subparsers(dest='command')

    parser_show = subs.add_parser('show',
            help='Show symlinks on stdout. "O" indicates that git-sym will ignore it; "+" that it needs to be resolved; and "." or "/" that it is a fully resolved file or directory.')
    parser_show.add_argument('symlinks', nargs='*',
            help='If not given, walk through tree to find relevant symlinks.')

    parser_update = subs.add_parser('update',
            help='Fill-in symlinks and retrieve files into cache.')
    parser_update.add_argument('symlinks', nargs='*',
            help='If not given, walk through tree to find relevant symlinks.')

    parser_check = subs.add_parser('check',
            help='Look for the first unresolved symlink, if any. Return 1 if found. (Intended for scripting. Humans should use "missing".')
    parser_check.add_argument('symlinks', nargs='*',
            help='If not given, walk through tree to find relevant symlinks.')

    parser_missing = subs.add_parser('missing',
            help='Print all unresolved symlinks on stdout.')
    parser_missing.add_argument('symlinks', nargs='*',
            help='If not given, walk through tree to find relevant symlinks.')

    parser_fix = subs.add_parser('fix',
            help='(IGNORE THIS FOR NOW.) If you add or remove GIT_SYM_LINK from ".gitignore", you will need to alter all symlinks. This does it automatically, but it does not commit the changes. (TODO: Support other changes.)')
    parser_fix.add_argument('symlinks', nargs='*',
            help='If not given, walk through tree to find relevant symlinks.')

    parser_add = subs.add_parser('add',
            help='Move named files/directories to GIT_SYM_CACHE_DIR. Create git-sym symlinks in their places. "git add". You still need to "git commit" before running "git-sym update".')
    parser_add.add_argument('paths', nargs='+',
            help='Files and/or directories. At least one path must be supplied.')

    return parser.parse_args()


if __name__=='__main__':
    args = parse_args()
    main(vars(args))
