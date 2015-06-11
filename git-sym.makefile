HOST:=https://raw.githubusercontent.com/open-source-parsers/jsoncpp

version-3f05b1a89708381c6f42b3f62cb4203557cb7f35:
	curl ${HOST}/3f05b1a89708381c6f42b3f62cb4203557cb7f35/version >| $@
version-9cb88d2ca66af19c53a98843d159cc1d32ebaec6:
	curl ${HOST}/9cb88d2ca66af19c53a98843d159cc1d32ebaec6/version >| $@
