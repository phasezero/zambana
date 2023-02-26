# zambana
Docker compose solution to install zammad ticket system including Kibana reporting.

## prerequsites
- Docker

## (Quick) Installation
After cloneing zambana Repo go into zambana folder.
```
cd zambana
```
make sure the backup.sh script is executeable.
If needed you can prepair zammad configuration in zammad.conf file before you start the installation.
```
chmod -x scripts/backup.sh
```
now execute  the spawn script
```
sh ./spwn-zambana.sh
```

## Configuration
For explicit an detailed configuration read the elasticsearch and zammad documentaion.
A configuarion of zammad via rails can be prepaird in zammad.conf. These settings will be made during installation process.
