# Why?
The purpose is to separate big-file caching from revision-control. There are several alternatives:

  * https://github.com/jedbrown/git-fat
  * https://github.com/schacon/git-media
  * http://git-annex.branchable.com/
  * https://github.com/github/git-lfs

But all those impose the penalty of checksums on the large files. We assert that the large files can be uniquely derived from URLs, versioned in S3 or by filename, etc. We store only symlinks in the git repo.

## Installing
```
ln -sf `pwd`/git_sym.py ~/bin/git-sym
```

## Running
You can test it right here.
```
touch ~/foo
git-sym update links/foo
# or
# python git_sym.py update links/foo
cat links/foo
```
And this should fail:
```
rm -f ~/git_sym_cache/foo ~/foo
git-sym update
```

## Adding your own large-files.
```
git-sym add large1 large2 large3
git commit -m 'adding links'
git-sym show
```
**git-sym** will choose unique filenames based on checksums. But `git-sym add` is strictly for convenience.
You are free to use your own filenames. Anything symlinked via `GIT_ROOT/.git_sym` will be update-able.

Next, you might want to make those files available to other.
You can then move those files out of GIT_SYM_CACHE_DIR and into Amazon S3, or an ftp site, or wherever.
Just add rules to your `git_sym.makefile`.

## Other useful commands
```
git-sym show -h
git-sym missing -h
git-sym -h
```

# Details
## Typical usage
You will store relative symlinks in your repo. They will point to a unique filename inside `ROOT/.git_sym/`, where ROOT is `../../` etc.

`git-sym update` will search your repo for symlinks (unless you specify them on the command-line). For each, it will execute `ROOT/git_sym.makefile` in your `GIT_SYM_CACHE_DIR` (`~/git_sym_cache` by default). The makefile targets will be the basenames of the symlinks.

If all those files are properly retrieved, then symlinks will be created with the same filenames inside `.git/git_sym`. `ROOT/.git_sym` will point at that. And all other symlinks will point *thru* `ROOT/.git_sym`. Thus, there are three (3) levels of indirection.

## Makefile
Someday, we will offer a plugin architecture. But for now, using a makefile is really very simple. Just create a rule for each unique filename. (You *are* using unique filenames, right?) You can run `wget`, `curl`, `ftp`, `rcp`, `rsync`, `aws-s3-get`, or whatever you want. The retrieval mechanism is decoupled from caching.

You should try to ensure that you have a rule for every current symlink. Old rules for symlinks no longer in your repo are fine; they are simply ignored.

To test your rules:
```
export GIT_SYM_CACHE_DIR=~/mytest
git-sym missing # should report something
git-sym update
git-sym missing
```

## Other notes
### Cache
**git-sym** sets the mode to read-only for the cached files. These files should never change. You might want to name them after their own checksums. `git-sym add` can help you with that.
### Submodules
If your module can be used as a *submodule*, we cannot point at `.git/git_sym/` directly because for submodules `.git/` is not inside the tree. (The relative symlinks are constant, so they need to work no matter where `.git/` sits.) That is why we have *three* levels of indirection, in case your were wondering. (This is also why **git-annex** *fails* for submodules.)

This is also why we write `ROOT/.git_sym`; it might be a different directory than `.git`.

For submodule support, you will also need this:
```
git config --global alias.gsexec '!exec '
```
We use that to learn the actual location of the `.git/` directory. If it fails, we try current directory, and if `.git` is not a directory there, we attempt to find it in `../.git/modules/REPO`, where REPO is the root directory. (This can fail in many ways. The alias never fails.)

Again, we expect you to forget that, so we add that alias to your local repo for you. Believe us: It's a Good Thing.

### .gitignore
Since the intermediate symlink is also in the repo, but points to a changing target, it needs to be listed in `.gitignore`. (That anticipates both accidental `git add` and `git clean`.) We expect you to forget that important rule, so **git-sym** will detect its absence and add it to `.git/info/exclude` instead. No worries.

### Complicated symlinks?
We require a flat directory structure within `.git/git_sym`. If you need more files than your filesystem
can handle, you're Doing It Wrong. Git will slow down anyway.

However, we support symlinked *directories*, which can then be an entire tree in GIT_SYM_CACHE_DIR. That should
satisfy all reasonable use-cases.

# TODO
* git-sym fix -- also fix broken links from moved cache, and missing links in GIT_SYM_DIR
* Try `.gitattributes` instead of `.gitignore`, to avoid problems with `git clean`.
* Add `git-submodule` support, to run `git-sym update` automatically.
