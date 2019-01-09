# ctrs-archetype
Archetype instance for CoTRS project
https://github.com/kingsdigitallab/ctrs-django

# Pre requisites

* linux environment (ubuntu/debian)
* postgresql 9+
* pipenv installed system-wide
* git

# Local deployment

## pull code

```
git clone git@github.com:kcl-ddh/digipal.git digipal_github # TODO: develop branch
git clone git@github.com:kingsdigitallab/ctrs-archetype.git
```

## set up project

```
cd ctrs-archetype
ln -s ../digipal_github/digipal
ln -s ../digipal_github/digipal_text
ln -s ../digipal_github/build
```

## virtual env
```
mkdir .venv
cp build/requirements.txt .
pipenv install --two
rm build/requirements.txt
```

## database
```
sudo su postgres
psql
create user app_ctrs_archetype with password 'XXX';
\q
createdb -E 'utf-8' -T template0 -O app_ctrs_archetype_lcl
```

## local_settings.py

local_settings.py SHOULD NOT be part of github repo, it is reserved for any sensitive information like database connections, address to image server, etc. and for anything specific to a particular instance of your site.

settings_sriba.py contains your project customisations, anything which is not sensitive and is shared between all instances (local, development, staging, live) of the projects.

## create db tables
`pipenv shell`
`./manage.py migrate`

# run server
`./manage.py runserver`

# browse your site

open browser as http://localhost:8000/
