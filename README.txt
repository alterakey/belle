README
--------

1. BASIC USAGE
----------------

$ sqlite3 ./assets.db
SQLite version 3.6.12
Enter ".help" for instructions
Enter SQL statements terminated with a ";"
sqlite> .schema
CREATE TABLE assets (name varchar, hash varchar unique, type varchar, blob blob);
sqlite> select name,hash,type,length(blob) from assets;
6fec72327526b803e19f6ffd3bfd25ea5d230c491ae30499c011c1e0b40f5ff9.otf|6fec72327526b803e19f6ffd3bfd25ea5d230c491ae30499c011c1e0b40f5ff9|application/x-font-opentype|3969036
70faaaa2690da0fc68c32e8c91b06e398e67cdd0ba8a51b13613d98d5f8463fa.otf|70faaaa2690da0fc68c32e8c91b06e398e67cdd0ba8a51b13613d98d5f8463fa|application/x-font-opentype|4759804
a253540b952ad69b167717e01bdebeb386af7a9392b874240e5ac34a462f963f.png|a253540b952ad69b167717e01bdebeb386af7a9392b874240e5ac34a462f963f|image/png|3838071
...

$ cat <<__EOT__ | python -m belle.command render sqlite:///assets.db > hoge.jpg
<?xml version="1.0"?>
<design width="2480"
        height="3508">
  <layer>
    <image x="0.5"
           y="0.5"
           width="1.0"
           height="1.0"
           rotate="0.0"
           src="a253540b952ad69b167717e01bdebeb386af7a9392b874240e5ac34a462f963f.png" />
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
          face="70faaaa2690da0fc68c32e8c91b06e398e67cdd0ba8a51b13613d98d5f8463fa.otf">強</char>
    <char x="0.18"
          y="0.14"
          width="0.10"
          height="0.10"
          rotate="0.0"
          outline-color="#000000"
          outline-edge="0.000806451"
	  tate="tate"
          face="6fec72327526b803e19f6ffd3bfd25ea5d230c491ae30499c011c1e0b40f5ff9.otf">敵</char>
  </layer>
</design>
__EOT__


2. THUMBNAIL GENERATION
-------------------------

$ python -m belle.command generate-thumbnail <assetid> x y
