# ctrs-archetype
Archetype instance for CoTRS project
https://github.com/kingsdigitallab/ctrs-django

Geoffroy Noel, KDL, 2018-2021

# Purpose

This site was used as a private editorial environment for the researchers to:
* edit the metadata of manuscripts of Declaration & Regiam
* paste the text of the manuscripts and them mark up (e.g. unsettled regions) using new custom markup in the Text Editor
* draw a bounding box for each the unsettled region on the image of SP13
* verify the alignment of the regions across group of manuscripts (using a new web page developed for that purpose)

Note that because some regions span across two lines 
and Archetype doesn't support linking more than one image area to one part of the text,
we had to use two identical images and texts of the SP13 manuscript. 
The first line of each region was annotated on the first image, 
the second line (if any) of each region on the second image. 

# Data migration to the public website (cotr)

The content described above was regularly extracted using Archetype rest API
and uploaded to the public website (see the cotr repository in KDL github).
```
# go to the following address with your browser:
https://ctrs-archetype-stg.kdl.kcl.ac.uk/digipal/api/textcontentxml/?@select=*status,id,str,content,*text_content,*item_part,group,group_locus,type,*current_item,locus,shelfmark,*repository,place&@limit=10000
# Save it as arc-content.json then, in the cotr folder run the following:
./manage.py ctrstxt import PATHTO/arc-content.json
```

To migrate the SP13 graphical annotations (bounding boxes):
```
# go to the following address with your browser:
http://ctrs-archetype-stg.kdl.kcl.ac.uk/digipal/api/annotation/?_image__id__in=[4,5]&@select=id,geo_json,image_id&@limit=1000
# save the file and copy it to /media/arch-annotations.json in the cotr project
```

# Installation of Archetype

## Pre requisites

* linux environment (ubuntu/debian)
* python2, with pip and virtualenv
* postgresql 9+
* git
* nodejs > npm > lessc, typescript

## Download the code from github

```
# AROOT is the root path where you'll install archetype
cd AROOT 
git clone -b develop git@github.com:kcl-ddh/digipal.git digipal_github
git clone git@github.com:kingsdigitallab/ctrs-archetype.git
```

## Set up the project folders

```
cd AROOT
cd ctrs-archetype
ln -s ../digipal_github/digipal
ln -s ../digipal_github/digipal_text
ln -s ../digipal_github/build
```

## Create the python virtual environment

```
cd AROOT
python2 -m virtualenv venv
. venv/bin/activate
pip install -r ctrs-archetype/build/requirements.txt
```

## Create the database
```
sudo su postgres
psql
create user app_ctrs_archetype with password 'XXX';
\q
createdb -E 'utf-8' -T template0 -O app_ctrs_archetype app_ctrs_archetype_lcl
```

## local_settings.py

local_settings.py SHOULD NOT be part of github repo, it is reserved for any sensitive information like database connections, address to image server, etc. and for anything specific to a particular instance of your site.

settings_ctrs.py contains your project customisations, anything which is not sensitive and is shared between all instances (local, development, staging, live) of the projects.

## create db tables
`pipenv shell`
`./manage.py migrate`

## run server
`./manage.py runserver`

## browse your site

open browser as http://localhost:8000/

# Package up the data

Run the following script from your root folder to create an archive
at ctrs/static/archetype.tar.gz. The archive will contain all the content
and the project settings & customisations.

```
python build/zip_digipal_project.py 
```

If the `images` folder in the archive is empty, you'll need to add it
yourself. The image folder will contain your `jp2` & `originals` folder.
To find their locations on the server run the following command and look
at the first path in the output.

```
python manage.py dpim --help | head -n 12
```

Edit local_settings.py inside the archive and leave only one line:

```
from settings_ctrs import *
```

