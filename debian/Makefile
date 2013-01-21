#
# This Makefile is responsoble for build debian package.
# 4 variables must be provided:
#   HSN2_VER=2.X
#   BUILD_NUMBER=999
#   DEBIAN_DIST=(experimental|2.X)

DEBIAN_DIST=experimental
HSN2_COMPONENT=console

all:	hsn2-console

clean:	hsn2-console-clean

PKG=hsn2-$(HSN2_COMPONENT)_$(HSN2_VER)-$(BUILD_NUMBER)_all
hsn2-console: hsn2-console-clean
	mkdir -p $(PKG)/DEBIAN
	mkdir -p $(PKG)/etc/hsn2
	mkdir -p $(PKG)/opt/hsn2/$(HSN2_COMPONENT)
	#mkdir -p $(PKG)/usr/bin
	cp ../*.py $(PKG)/opt/hsn2/$(HSN2_COMPONENT)
	#ln -s /opt/hsn2/$(HSN2_COMPONENT)/hc.py $(PKG)/usr/bin/hc
	cp ../$(HSN2_COMPONENT).conf $(PKG)/etc/hsn2
	cp control conffiles postinst postrm ${PKG}/DEBIAN
	sed -i "s/{VER}/${HSN2_VER}-${BUILD_NUMBER}/" $(PKG)/DEBIAN/control
	sed -i "s/{DEBIAN_DIST}/${DEBIAN_DIST}/" $(PKG)/DEBIAN/control
	fakeroot dpkg -b $(PKG)

hsn2-console-clean:
	rm -rf hsn2-$(HSN2_COMPONENT)_*
