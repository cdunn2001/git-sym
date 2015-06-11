# Why?
The purpose is to separate big-file caching from revision-control.

From the author of **git-fat**:
> Checking large binary files into a source repository (Git or otherwise) is a bad idea because repository size quickly becomes unreasonable. Even if the instantaneous working tree stays manageable, preserving repository integrity requires all binary files in the entire project history, which given the typically poor compression of binary diffs, implies that the repository size will become impractically large. Some people recommend checking binaries into different repositories or even not versioning them at all, but these are not satisfying solutions for most workflows.

* https://github.com/cdunn2001/git-sym/wiki/Rationale

## Examples
These examples explain the basics:

* <https://github.com/cdunn2001/git-sym-test/wiki/Examples>

If you prefer words to shell code:
* <https://github.com/cdunn2001/git-sym/wiki/Details>
* <https://github.com/cdunn2001/git-sym/wiki/Examples>
