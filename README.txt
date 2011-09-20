README
--------

1. BASIC USAGE
----------------

$ sqlite3 ./assets.db
SQLite version 3.6.12
Enter ".help" for instructions
Enter SQL statements terminated with a ";"
sqlite> .schema
CREATE TABLE assets (name varchar unique, type varchar, blob blob);
sqlite> select name,type,length(blob) from assets;
A-OTF-GothicMB101Pro-Heavy.otf|font|3969036
A-OTF-ShinMGoPro-Medium.otf|font|4759804
image0.png|image|3838071
...

$ cat <<__EOT__ | python -m belle.command sqlite:///assets.db > hoge.jpg
<?xml version="1.0"?>
<design width="2480"
        height="3508">
  <layer>
    <image x="0.5"
           y="0.5"
           width="1.0"
           height="1.0"
           rotate="0.0"
           src="image0.png" />
  </layer>
  <layer>
    <char x="0.08"
          y="0.04"
          width="0.10"
          height="0.10"
          rotate="0.0"
          outline-color="#000000"
          outline-edge="0.000806451"
	  tate="tate"
          face="A-OTF-ShinMGoPro-Medium.otf">強</char>
    <char x="0.18"
          y="0.14"
          width="0.10"
          height="0.10"
          rotate="0.0"
          outline-color="#000000"
          outline-edge="0.000806451"
	  tate="tate"
          face="A-OTF-GothicMB101Pro-Heavy.otf">敵</char>
  </layer>
</design>
__EOT__
