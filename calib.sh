#!/bin/bash
MKECC_DATA_PATH=/home/ubuntu/.local/lib/python3.8/site-packages/pymkecc_util/pymkecc_session/data/
MKECC_SESSION=/home/ubuntu/.local/bin/pymkecc_session
MKETS=/home/ubuntu/.local/bin/mkets
#MKETS_PATH=/opt/mke/mketk/mkets
MAKEFW_PATH=/opt/mke/mke-firmware-cm3
#MKEENV_SCRIPT=/opt/mke/mketk/env.sh
MACROFILE=macros.json
SESSION_EXT=msf

usage () {
  echo "usage calib.sh [-g] [-m <MACROFILE>] <type> <SENSOR_ID> <DATAPATH>"
  echo "     <type> vcsel : vcsel sensor (mkedet02)"
  echo "     <type> vcsel1 : vcsel sensor (mkedet01)"
  echo "     <type> fisheye : fisheye sensor"
  echo "     <type> eel : eel laser"
  echo "     -g : gamma search mode on"
}

while getopts "gm:" OPT
  do
    case $OPT in
      "g" ) FLG_G="TRUE" ;;
      "m" ) MACROFILE=$OPTARG ;;
       *  ) usage
            exit 1;;
    esac
  done

shift `expr $OPTIND - 1`

if [ "$#" -ne 3 ]
then
  usage
  exit 1
fi

if [ "$FLG_G" = "TRUE" ]; then
  echo 'gamma search mode on'
fi

MODE=$1
CALIB_SENID=$2
DATAPATH="$(cd $3 && pwd)"
OUTPATH=$DATAPATH
MKEDD_NAME=${OUTPATH}/mkedet_$CALIB_SENID.bin

echo ${DATAPATH}/${MACROFILE}

if [ ! -e ${DATAPATH}/${MACROFILE} ]
then
  echo "macrofile ${DATAPATH}/${MACROFILE} is not exist"
  exit 1
fi

case ${MODE} in 
"vcsel" ) TEMPLATE=$MKECC_DATA_PATH/templates/vcsel_mkedet02_sensor.json ;;
"vcsel1" ) TEMPLATE=$MKECC_DATA_PATH/templates/vcsel_raytopo_sensor.json ;;
"fisheye" ) TEMPLATE=$MKECC_DATA_PATH/templates/fisheye4l_raytopo_sensor.json ;;
"eel" ) TEMPLATE=$MKECC_DATA_PATH/templates/eel_raytopo_sensor_det02.json ;;
* ) echo "illegal type"
    exit 1
esac


exp="s|\"DATA_PATH\":.*\/\",|\"DATA_PATH\":\"${DATAPATH}\/\",|"
sed -i -E $exp ${DATAPATH}/${MACROFILE}

exp="s|\"SERIAL_NUMBER\":.*\",|\"SERIAL_NUMBER\":\"${CALIB_SENID}\",|"
sed -i -E $exp ${DATAPATH}/${MACROFILE}

do_calibration () {
  $MKECC_SESSION -t $TEMPLATE -m ${DATAPATH}/${MACROFILE} -d -e -o ${OUTPATH}/$CALIB_SENID.$SESSION_EXT -v

  #### Make Package ###
  if [ ${MODE} = "fisheye" ]; then
    cp $MKEDD_NAME ${OUTPATH}/tmp.bin
    $MAKEFW_PATH/make_fw_package.pl -o ${OUTPATH}/$CALIB_SENID.mfw -c tmp.bin
  else
    cp $MKEDD_NAME ${OUTPATH}/mkedet.bin
    $MAKEFW_PATH/make_fw_package.pl -o ${OUTPATH}/$CALIB_SENID.mfw mkedet.bin
  fi

  ### VISUALIZATION / INVESTIGATION
  (
#  cd $MKETS_PATH
#  source $MKEENV_SCRIPT
#  $MKETS --exp_dir=${OUTPATH} stats calibfolder --cal_dir ${DATAPATH} --session_file ${OUTPATH}/${CALIB_SENID}.$SESSION_EXT --sess_opts plot:points num:points plot:target_results --dot_size 2
  $MKETS -O ${OUTPATH} stats sessionreport -s ${OUTPATH}/$CALIB_SENID.$SESSION_EXT -t calibimagesreport
  $MKETS -O ${OUTPATH} stats sessionreport -s ${OUTPATH}/$CALIB_SENID.$SESSION_EXT -t sessionreport # --ignore_dets # -t calibreport
  )
}

setgamma () {
  exp="s|\"LASER_TARGET_GAMMA\":.*,|\"LASER_TARGET_GAMMA\":$1,|"
  sed -i -E $exp ${DATAPATH}/${MACROFILE}
}

if [ "$FLG_G" = "TRUE" ]; then
  gammas=(0.45 0.50 0.56 0.63 0.71 0.83 1.0 1.2 1.4 1.6 1.8 2.0 2.2)
  for gamma in "${gammas[@]}" ; do
    echo gamma ${gamma} ----------------
    setgamma ${gamma}
    do_calibration
    gamma_folder=${OUTPATH}/gamma_${gamma}
echo ${gamma_folder} ------------------
    mkdir -p $gamma_folder
    cp ${OUTPATH}/*.html ${OUTPATH}/*.bin ${OUTPATH}/*.mfw ${OUTPATH}/*.$SESSION_EXT ${gamma_folder}
  done
else
  do_calibration
fi

