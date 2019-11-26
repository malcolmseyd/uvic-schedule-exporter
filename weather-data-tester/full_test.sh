#!/usr/bin/env sh

#
# This script was created by Gabe Dunn, full credit to him
# https://github.com/redxtech
# 
#I've commented some lines, added logging, and added my python script
#

# quit if anything fails
set -e

# logging
log() {
	echo "$1" | tee -a testing.log
}

# main function
main() {
  # clear the log file, idk if this is good style
  echo > testing.log
  
  if [ ! -d "./data" ]; then
    echo "Data files don't exist yet, downloading."
	echo
    python3 get_test_data.py
  fi
  
    # for each of the three programs
  for PROGRAM in "daily_avg" "daily_min_max" "station_extremes"; do

    # compile the program
    log "Compiling $PROGRAM..."
    gcc -Wall -std=c11 -o ./main "$PROGRAM.c"

    # for each set of testing data
    for TEST_SET in 1 2 3 4 5 6 7 8 9; do
      # set the dataset
      #log "Setting the dataset to $TEST_SET..."
      ln -f "./data/data-$TEST_SET.txt" "./input_data.txt"

      # run the program
      #log "Running $PROGRAM ($TEST_SET)..."
      ./main

      # create a variable and set the output file based on which program is running
      PROGRAM_FILE=""
      case $PROGRAM in
      daily_avg)
        PROGRAM_FILE="daily_averages_summary.txt"
        ;;
      daily_min_max)
        PROGRAM_FILE="daily_minimum_maximum_summary.txt"
        ;;
      station_extremes)
        PROGRAM_FILE="station_extremes.txt"
        ;;
      *)
        log "error: no program by that name"
        return 1
        ;;
      esac

      # diff the output against the expected output
      #log "Diffing output..."
      diff "./$PROGRAM_FILE" "./data/output/$PROGRAM/output-$TEST_SET.txt"

      DIFF_STATUS="$?"

      if test "$DIFF_STATUS" -eq 0; then
        log "Test $PROGRAM ($TEST_SET) passed!"
      else
        log "Test $PROGRAM ($TEST_SET) failed!"
        exit 1
      fi

      # new line
      #log
    done

    log "$PROGRAM tests completed!"
    log
  done

  log "All tests passed!"

  echo "Results have been recorded in 'testing.log'"

  # Cleanup
  #rm -r ./data/
  rm ./daily_averages_summary.txt
  rm ./daily_minimum_maximum_summary.txt
  rm ./station_extremes.txt
  rm ./input_data.txt
  rm ./main
}

main
