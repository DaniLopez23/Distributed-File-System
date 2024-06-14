#!/usr/bin/make -f

NUM_FILEMANAGERS ?= 1
FILE ?= files/text.txt
SAME_FILE_DIFFERENT_NAME ?= files/text_copy.txt
FILE_HASH ?= $(shell md5sum $(FILE) | cut -d' ' -f1)
STORAGE_NAME ?= storage

run-aplication: app-workspace
	$(MAKE) run-node1 &
	sleep 1
	$(MAKE) run-node2 &
	sleep 1
	$(MAKE) run-node3 &
	sleep 1

	icegridadmin --Ice.Config=URFS_App_config/locator.config -e "server start IceStorm"
	icegridadmin --Ice.Config=URFS_App_config/locator.config -e "application patch URFSApp"

run-node1: data/db/registry data/db/node1/servers
	icegridnode --Ice.Config=URFS_App_config/node1.config
	
run-node2: data/db/node2/servers
	icegridnode --Ice.Config=URFS_App_config/node2.config 

run-node3: data/db/node3/servers
	icegridnode --Ice.Config=URFS_App_config/node3.config

run-gui:
	python3 src/GuiApplication.py --Ice.Config=URFS_App_config/locator.config

app-workspace: data/URFS data/db/node3/distrib/URFSApp/$(STORAGE_NAME) 
	cp urfs.ice src/FileManager.py src/Frontend.py src/util.py data/URFS
	icepatch2calc data/URFS

dispatc-aplication:
	icegridadmin --Ice.Config=URFS_App_config/locator.config -e "application add URFSApp" &
	sleep 1
	icegridadmin --Ice.Config=URFS_App_config/locator.config -e "application patch URFSApp"

data/%:
	mkdir -p $@

test-client-icegrid:
	mkdir -p downloads
	./src/Client.py --Ice.Config=URFS_App_config/locator.config --upload $(FILE)
	./src/Client.py --Ice.Config=URFS_App_config/locator.config --upload $(FILE)
	./src/Client.py --Ice.Config=URFS_App_config/locator.config --upload $(SAME_FILE_DIFFERENT_NAME)
	./src/Client.py --Ice.Config=URFS_App_config/locator.config --list
	./src/Client.py --Ice.Config=URFS_App_config/locator.config --download $(FILE_HASH)
	./src/Client.py --Ice.Config=URFS_App_config/locator.config --remove $(FILE_HASH)
	./src/Client.py --Ice.Config=URFS_App_config/locator.config --list

start:
	$(MAKE) run-icestorm & $(MAKE) run-registry &
	sleep 1
	$(MAKE) run-filemanager &
	sleep 1
	$(MAKE) run-frontend

run-filemanager:
	mkdir -p storage
	./src/FileManager.py --Ice.Config=config/fileManager.config

run-frontend:
	./src/Frontend.py --Ice.Config=config/frontend.config $(NUM_FILEMANAGERS)

test-client:
	mkdir -p downloads
	./src/Client.py --Ice.Config=config/client.config --upload $(FILE)
	./src/Client.py --Ice.Config=config/client.config --upload $(FILE)
	./src/Client.py --Ice.Config=config/client.config --upload $(SAME_FILE_DIFFERENT_NAME)
	./src/Client.py --Ice.Config=config/client.config --list
	./src/Client.py --Ice.Config=config/client.config --download $(FILE_HASH)
	./src/Client.py --Ice.Config=config/client.config --remove $(FILE_HASH)
	./src/Client.py --Ice.Config=config/client.config --list

run-icestorm:
	mkdir -p IceStorm/
	icebox --Ice.Config=config/icebox.config

run-registry:
	mkdir -p data/db/registry
	icegridregistry --Ice.Config=config/registry.config

clean:
	$(RM) -r downloads/ storage/ __pycache__/ URFS/
	$(RM) urfs_ice.py *.pyc

vclean: clean
	$(RM) -r IceStorm/ data/
