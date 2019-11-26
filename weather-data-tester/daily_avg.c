// Malcolm Seyd - V00938975 - 2019/11/08

#include <stdio.h>

const int COLS = 6;
const char* INPUT_FILE = "input_data.txt";
const char* OUTPUT_FILE = "daily_averages_summary.txt";

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

    // Date as index, [0] is sum of temp, [1] is # of entries
    double data[13][32][2] = {{{0}}};
    double entry[6];
    double* today = NULL;

    int month;
    int day;

    // Read raw data to matrix
    for (long i = 0; i < rows; i++) {
        // Read an entry from the file
        for (int j = 0; j < COLS; ++j) {
            fscanf(in_file, "%lf", &entry[j]);
        }

        month = entry[0];
        day = entry[1];

        today = data[month][day];

        today[0] += entry[5];
        today[1] += 1;
    }

    fclose(in_file);


    FILE* out_file = fopen(OUTPUT_FILE, "w");
    if(!out_file){
        printf("Error: unable to write to file \"%s\"\n", OUTPUT_FILE);
        return 1;
    }

    // Write formatted data to file
    for (int i = 0; i < 13; ++i) {
        for (int j = 0; j < 32; ++j) {
            // If there's any data for that day, output it
            if (data[i][j][1] != 0){
                //                                      sum of temp  /  # of entries
                fprintf(out_file, "%d %d %.2lf\n", i, j, data[i][j][0] / data[i][j][1]);
            }
        }
    }

    fclose(out_file);

    return 0;
}
