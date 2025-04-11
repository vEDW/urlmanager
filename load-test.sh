#!/bin/bash

#URL="http://<ip or url>"

[ "${URL}" == "" ] && echo 'usage: export URL="http://<ip or url>"' && exit 1

declare answers
#answers=("test")

echo "testing with URL = ${URL} "
get_result() {
        #returns json
        RESPONSE=$(curl -s -w '####%{response_code}' ${URL}  --connect-timeout 1)
        RESERROR=$?
        HTTPSTATUS=$(echo ${RESPONSE} |awk -F '####' '{print $2}')
        if [ $RESERROR = 7 ]; then
            echo "No Answer - curl error 7"
            exit
        fi
        case $HTTPSTATUS in
                200)    
                        echo ${RESPONSE} |awk -F '####' '{print $1}'
                        ;;
                503)    
                        echo "Not Ready"
                        ;;
                000)    
                        echo "No Answer - Status 000"
                        ;;
                *)      
                         echo ${RESPONSE} |awk -F '####' '{print $1}'
                        ;;
        esac
}

while true; do
    testresult=$(get_result)
    echo ${testresult}
    if [[ ${answers[$testresult]} == "" ]]; then
        answers[$testresult]=1
    else
        answers[$testresult]=$((${answers[$testresult]} + 1 ))
    fi
    clear
    for x in "${!answers[@]}"; do printf "[%s]=%s\n" "$x" "${answers[$x]}" ; done
    sleep 1
done