build:
	docker build --force-rm $(options) -t unimatch:latest .

build-prod:
	$(MAKE) build options"--target production"