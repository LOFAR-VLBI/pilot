#!/bin/sh

# VLBI_ROOT_DIR is defined in pyprojects.toml

errors=0
for step in "$VLBI_ROOT_DIR/steps"/*.cwl; do
    cwltool $1 --validate $step || errors=$(($errors+1))
done

[ $errors -gt 0 ] && echo "Failed validation count = $errors"

[ $errors -eq 0 ] # exit status
