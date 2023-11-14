tar-archive:
	# Create tar archive excluding ignored files
	gtar --exclude-vcs-ignores --exclude-vcs -czvf module.tar.gz .
