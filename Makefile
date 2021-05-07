DOCKER_USER:=cletaio
DOCKER_ORGANIZATION=cletaio
DOCKER_IMAGE:=base
BUILDDIR=build
PWD=$(shell pwd)

XZ_THREADS ?= 0

hooks:
	mkdir -p alpm-hooks/usr/share/libalpm/hooks
	find /usr/share/libalpm/hooks -exec ln -sf /dev/null $(PWD)/alpm-hooks{} \;

rootfs: hooks
	mkdir -vp $(BUILDDIR)/var/lib/pacman/
	cp /usr/share/devtools/pacman-extra.conf rootfs/etc/pacman.conf
	cat pacman-conf.d-noextract.conf >> rootfs/etc/pacman.conf
	fakechroot -- fakeroot -- pacman -Sy -r $(BUILDDIR) \
		--noconfirm --dbpath $(PWD)/$(BUILDDIR)/var/lib/pacman \
		--config rootfs/etc/pacman.conf \
		--noscriptlet \
		--hookdir $(PWD)/alpm-hooks/usr/share/libalpm/hooks/ $(shell cat packages)
	cp --recursive --preserve=timestamps --backup --suffix=.pacnew rootfs/* $(BUILDDIR)/
	
	# remove passwordless login for root (see CVE-2019-5021 for reference)
	sed -i -e 's/^root::/root:!:/' "$(BUILDDIR)/etc/shadow"

	# fakeroot to map the gid/uid of the builder process to root
	# fixes #22
	fakeroot -- tar --numeric-owner --xattrs --acls --exclude-from=exclude -C $(BUILDDIR) -c . -f archlinux.tar
	rm -rf $(BUILDDIR) alpm-hooks

archlinux.tar: rootfs

compress-rootfs: archlinux.tar
	xz -9 -T"$(XZ_THREADS)" -f archlinux.tar

docker-image: compress-rootfs
	docker build -t $(DOCKER_ORGANIZATION)/$(DOCKER_IMAGE) .

docker-image-test: docker-image
	# FIXME: /etc/mtab is hidden by docker so the stricter -Qkk fails
	docker run --rm $(DOCKER_ORGANIZATION)/$(DOCKER_IMAGE) sh -c "/usr/bin/pacman -Sy && /usr/bin/pacman -Qqk"
	docker run --rm $(DOCKER_ORGANIZATION)/$(DOCKER_IMAGE) sh -c "/usr/bin/pacman -Syu --noconfirm docker && docker -v" # Ensure that the image does not include a private key
	! docker run --rm $(DOCKER_ORGANIZATION)/$(DOCKER_IMAGE) pacman-key --lsign-key sdmunozsierra@miners.utep.edu
	docker run --rm $(DOCKER_ORGANIZATION)/$(DOCKER_IMAGE) sh -c "/usr/bin/id -u http"
	docker run --rm $(DOCKER_ORGANIZATION)/$(DOCKER_IMAGE) sh -c "/usr/bin/pacman -Syu --noconfirm grep && locale | grep -q UTF-8"

docker-push:
	docker login -u $(DOCKER_USER)
	docker push $(DOCKER_ORGANIZATION)/$(DOCKER_IMAGE)

.PHONY: rootfs docker-image docker-image-test docker-push
