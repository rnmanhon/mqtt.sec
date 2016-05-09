[FIWARE Lab Header & Footer guide] (https://github.com/ging/horizon/blob/master/openstack_dashboard/static/library/FIWARE-Lab-header:footer/README.jpg)


FIWARE Lab portals use a header & footer template. It is composed of the necessary elements of the framework Bootstrap3, the Font Awesome library and HTML and CSS.

The folder contains the CSS styles, you have to include the files:

- boottrap-frame.css
- font-awesome.css
- style.css


Inside the < head > tag using the following tags: 

  < link href="css/bootstrap-frame.css" rel="stylesheet" media="screen" >

  < link href="css/style.css" rel="stylesheet" media="screen" >

  < link href="css/font-awesome.css" rel="stylesheet" media="screen" >


In the fonts folder you will find the corporate font "Neotech" and the source of icons "Font Awesome". (the css is located in style.css)


The img folder contains: 
- favicon.ico 
- avatar by default (organizations, users and applications)
- Logo and FIWARE FIWARE Lab


In the “js” folder you will find the file collapse.js (from Bootstrap 3). To link the file you have to write the following lines before closing the < body > tag:

< script src="http://code.jquery.com/jquery.js">< /script >
< script src="js/collapse.js">< /script >


Finally the HTML code, is located in index.html
