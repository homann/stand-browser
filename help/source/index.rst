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

Pushing the buttons Next and Prev shows infrormation about the next
and previous stand in the window. If any fields are missing in the
vector layer, it is shown as blank. These buttons also change the
current selection in the layer, and pans/zooms to the newly selected
stand.

If you select - e.g. with the mouse or in the QGIS attribute table -
more than one stand a new set of buttons appear. They are Next
Selected and Prev Selected respectively. Pushing those buttons loops
through the selected stands, but *does not* change the selection.

The yellow background in the ``Stand ID`` field indicates that it is
editable. Writing the name of a stand and hiting return, searches for
that stand and displays it. If no such stand is found, the field is
reset to last valid stand.

Example data
============

There is example data in the `.../example_data`__ directory.

__ ../../../example_data


.. toctree::
   :maxdepth: 2

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

