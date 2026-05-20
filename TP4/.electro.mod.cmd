savedcmd_electro.mod := printf '%s\n'   electro.o | awk '!x[$$0]++ { print("./"$$0) }' > electro.mod
