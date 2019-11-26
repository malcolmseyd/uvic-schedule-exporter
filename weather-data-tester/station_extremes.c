// Malcolm Seyd - V00938975 - 2019/11/08

#include <stdio.h>

const int COLS = 6;
const char* INPUT_FILE = "input_data.txt";
const char* OUTPUT_FILE = "station_extremes.txt";

//TODO Clean up files
// ensure they're up to spec
// test them
// submit!
int main() {

    long rows = 1;
    double garbage = 0;

    // Count the number of entries

    FILE* in_file = fopen(INPUT_FILE, "r");
    if(!in_file){
        printf("Error: unable to read from file \"%s\"\n", INPUT_FILE);
        return 1;
    }

    for(int i = 0; fscanf(in_file, "%lf", &garbage) == 1; i++){
        if(i == COLS){
            i = 0;
            rows++;
        }
    }

    fclose(in_file);

    // Open it again and read the values

    in_file = fopen(INPUT_FILE, "r");
    if(!in_file){
        printf("Error: unable to read from file \"%s\"\n", INPUT_FILE);
        return 1;
    }

    /* Array value representation:
     * [0]:enabled
     *
     * Minimum:
     * [1]:temp
     * [2]:month
     * [3]:day
     * [4]:hour
     * [5]:minute
     *
     * Maximum
     * [6]:temp
     * [7]:month
     * [8]:day
     * [9]:hour
     * [10]:minute
     */
    double data[1000][11] = {{0}};
    double entry[6];
    double* station = NULL;

    int station_number;

    // Read from file to matrix
    for (long i = 0; i < rows; i++) {
        // Read an entry from the file
        for (int j = 0; j < COLS; ++j) {
            fscanf(in_file, "%lf", &entry[j]);
        }

        station_number = entry[4];
        station = data[station_number];

        if (station[0] == 0){
            // If first observation, temp is min and max
            station[0] = 1;

            station[1] = entry[5];
            station[2] = entry[0];
            station[3] = entry[1];
            station[4] = entry[2];
            station[5] = entry[3];

            station[6] = entry[5];
            station[7] = entry[0];
            station[8] = entry[1];
            station[9] = entry[2];
            station[10] = entry[3];

        } else if (station[1] > entry[5]){
            // If temp is smaller than min, set min to temp
            station[1] = entry[5];
            station[2] = entry[0];
            station[3] = entry[1];
            station[4] = entry[2];
            station[5] = entry[3];

        } else if (station[6] < entry[5]){
            // If temp is larger than max, set max to temp
            station[6] = entry[5];
            station[7] = entry[0];
            station[8] = entry[1];
            station[9] = entry[2];
            station[10] = entry[3];
        }
    }

    fclose(in_file);


    FILE* out_file = fopen(OUTPUT_FILE, "w");
    if(!out_file){
        printf("Error: unable to write to file \"%s\"\n", OUTPUT_FILE);
        return 1;
    }

    // Write formatted data to file
    for (int i = 0; i < 1000; ++i) {
        if (data[i][0] != 0){
            station = data[i];
            fprintf(out_file,
               		"Station %d: Minimum = %.2f degrees (%02.0f/%02.0f %02.0f:%02.0f), Maximum = %.2f degrees (%02.0f/%02.0f %02.0f:%02.0f)\n", 
					i,
                    station[1], station[2], station[3], station[4], station[5],
                    station[6], station[7], station[8], station[9], station[10]);
        }
    }

    fclose(out_file);

    return 0;
}
