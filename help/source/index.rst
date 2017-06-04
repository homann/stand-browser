.. StandBrowser documentation master file, created by
   sphinx-quickstart on Sun Feb 12 17:11:03 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Stand Browser - forestry in QGIS 
============================================

I have for a long time used QGIS to store and view my forestry
data. For almost as long time, I've been thinking about adapting QGIS
to work better with forestry. There are mainly three areas I would
like to improve:

* Easy viewing of stand data
* Caclulating stand data from observations
* Yearly update of growth

This is the first step.

Data format
===========

The plugin assumes the data is stored in a vector data set. The field names
must follow the description below. It is modelled after how the
Heureka data model of the SLU stores its data.
See the `Heureka Wiki <http://heurekaslu.org/wiki/Main_Page>`_ for more info.
Some filed names have been shortened, due to the 12 character limit of
SHP-files.

The fields and their data shall be UTF-8 encoded.

==========  =======     ==================================================
Fält        Typ         Beskrivning
==========  =======     ==================================================
standid     string      Valfri identifierare, tex '12'
prodarea    real        Produktiv area [ha]
layer       integer     Beståndslager. Normalt = 1, överstandare/skärm = 2
meanage	    integer	Genomsnittsålder
maturitycl  string	Huggningsklass Ex: 'R1' eller 'S3'
sispecie    string	Art för ståndortsindex. Ex: G24 → 'G'
sis	    integer	Höjd för ståndortsindex. Ex: G24-> '24'
v	    integer	Volym [m3sk/ha]
managecl    string	Målklass Ex: 'PG eller 'NO'
ppine	    string	Andel tall i tiondelar Ex: 'X' = 10/10
pspruce	    string	 -”- gran -”-
pbroadleaf  string	 -”- triviallöv -”-
pbirch	    string	 -”- björk -”-
pdeciduous  string	 -”- ädellöv -”-
paspen	    string	 -”- asp -”-
poak	    string	 -”- ek -”-
pbeech	    string	 -”- bok -”-
pcontorta   string	 -”- contorta -”-
plarch	    string	 -”- lärk -”-
dgv	    integer	Medeldiameter, grundytevägd [cm]
comment	    string	
cai	    real	Årlig tillväxt [m3sk/ha]
h	    real	Medelhöjd [m]
n	    integer	Stammantal [1/ha]
g           real	Grundyta [m2/ha]
invdate     date	Datum för senaste inventering
invsource   string	Källa senaste inventering (valfri text)
updated	    date	Aktualitetsdatum (inventering, framskrivning, etc)
altitude    integer	Höjd över havet [m]
countycode  integer	DLÄN-kod. Se `Heureka WIKI`__
==========  =======     ==================================================

__ http://heurekaslu.org/wiki/Variable:CountyCode


Usage
=====

In the drop-down menu at the top of the dock window, all available
vector layers that contains the required ``standid`` field are
shown. Select the layer you want to browse here.

Pushing the buttons Next and Prev shows information about the next
and previous stand in the window. If any fields are missing in the
vector layer, it is shown as blank. These buttons also change the
current selection in the layer, and pans/zooms to the newly selected
stand.

If you select - e.g. with the mouse or in the QGIS attribute table -
more than one stand a new set of buttons appear. They are Next
Selected and Prev Selected respectively. Pushing those buttons loops
through the selected stands, but *does not* change the selection.

Next to the ``Stand ID`` field, there's a field with yellow background
and search icon next to it. Writing the name of a stand and hitting return
or the search icon, searches for that stand and displays it. If no such
stand is found, nothing happens.

Toolbox
=======

By clicking the toolbox button, a new window is opened. It provuides
the following functionality:

Grid
----

If you want to make a data set with inventory points for a stand,
'Grid' can distribute the points for you. By selecting a template
layer file, you can also give the inventory points the fields you
want. An example inventory template is provided.

The number of points is interpolated with a square root function
between the minimum value for 1 hectare and the maximum value for 5
hectares. Above and below that size og stand, the number of points is
fixed. The minimum distance between points is set to 25 m, and half
that distance is used as padding to the stand border. If the number of
points can not be randomly placed with those constraints within a
certain time, the tool will give up and you will be notifed.

The 'Grid' tool scans the filed names and will look for a name
indicating the field contains the id. If so, it will be populated with
a sequence number.

If a field name indicates it contains a date, it will be populated
with today's date in ISO 8601 format (YYYY-MM-DD).


Example data
============

There is example data in the `.../example_data`__ directory.

It also contains a QML-file, that can be applied to the stand layer
for a nice look.

A template file for inventory points is also provided. If you
want to modify it, first copy it to a safe place.

__ ../../../example_data


.. toctree::
   :maxdepth: 2

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

