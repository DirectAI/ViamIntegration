module.tar.gz: requirements.txt *.sh src/*.py
	tar czf module.tar.gz $^
