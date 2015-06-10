# Why?
The purpose is to separate big-file caching from revision-control. There are several alternatives:

  * https://github.com/jedbrown/git-fat
  * https://github.com/schacon/git-media
  * http://git-annex.branchable.com/
  * https://github.com/github/git-lfs

But all those impose the penalty of checksums on the large files. We assert that the large files can be uniquely derived from URLs, versioned in S3 or by filename, etc. We store only symlinks in the git repo.

## Installing
You can run this as a **git** command by calling it `git-sym`
in your `$PATH`. Here is one way:
```
ln -sf `pwd`/git_sym.py ~/bin/git-sym
```
Alternatively, you can run it directly:
```
python git_sym.py -h
```

## Basic usage
### For repo users
```
git-sym show
git-sym update
```
### For repo owners
```
git-sym add my_big_file.gif
git commit -m 'git-sym added'
ls -l my_big_file.gif
```
Or more explicitly, and with a rule for retrieval:
```
ln -sf .git_sym/my_big_data.v123.db my_big_data.db
git add my_big_data.db
git commit
cat <<EOF >> git_sym.makefile
my_big_data.v123.db:
        wget http://www.somewhere.com/my_big_data.v123.db
EOF
git-sym update
```

## Examples
These examples explain the basics:

* <https://github.com/cdunn2001/git-sym-test/wiki/Examples>

If you prefer words to shell code:
* <https://github.com/cdunn2001/git-sym/wiki/Details>
* <https://github.com/cdunn2001/git-sym/wiki/Examples>
