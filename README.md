# zambana
Docker compose solution to install [zammad](https://zammad.com/ "Zammad: Helpdesk-Software & Ticketsystem für Ihr Business") ticket system including [Kibana](https://www.elastic.co/de/kibana/ "Kibana: Visualisieren, Analysieren und Erkunden von Daten") reporting.

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
chmod +x scripts/backup.sh
```
now execute  the spawn script
```
sh ./spwn-zambana.sh
```

## Configuration
For explicit an detailed configuration read the [Zammad admin-doc](https://admin-docs.zammad.org/en/latest/ "Zammad - Documentation for administrators"), [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/settings.html "Configuring Elasticsearch") and [Kibana](https://www.elastic.co/guide/en/kibana/current/settings.html "Configure Kibana") configuration guides.
A configuarion of Zammad via rails can be prepaird in zammad.conf. These settings will be made during installation process.

## ToDO
Minor preconfiguration of elasticsearch and kibana.
