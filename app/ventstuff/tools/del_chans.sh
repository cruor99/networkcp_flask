cd /home/loxus/ventrilo/ventrilo$1/
kill `cat ventrilo_srv.pid`
rm /home/loxus/ventrilo/ventrilo$1/ventrilo_srv.chn
./start
cd
