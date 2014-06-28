cd /home/loxus/ventrilo/ventrilo$1/
kill `cat ventrilo_srv.pid`
rm ventrilo_srv.usr > /home/loxus/misc/tools/error.log
./start
cd
