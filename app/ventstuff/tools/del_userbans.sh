cd /home/loxus/ventrilo/ventrilo$1/
kill `cat ventrilo_srv.pid`
rm ventrilo_srv.usr
rm ventrilo_srv.ban
./start
cd
